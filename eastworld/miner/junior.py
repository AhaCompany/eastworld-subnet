# The MIT License (MIT)
# Copyright © 2025 Eastworld AI

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import datetime
from collections import deque

import bittensor as bt
import httpx
import json_repair
from openai import AsyncOpenAI, APITimeoutError
from pydantic import BaseModel

from eastworld.protocol import Observation
from eastworld.base.miner import BaseMinerNeuron


class ActionLog(BaseModel):
    timestamp: datetime.datetime
    action: str
    feedback: str
    repeat_times: int


class JuniorAgent(BaseMinerNeuron):
    reflection: str
    action_log: deque

    prompt_system_tpl: str
    prompt_reflection_tpl: str
    prompt_action_tpl: str

    http_client: httpx.AsyncClient

    def __init__(self, config=None):
        super(JuniorAgent, self).__init__(config=config)

        self.reflection = ""
        self.action_log = deque(maxlen=100)

        with open("eastworld/miner/prompts/junior_system.txt", "r") as f:
            self.prompt_system_tpl = f.read()
        with open("eastworld/miner/prompts/junior_reflection.txt", "r") as f:
            self.prompt_reflection_tpl = f.read()
        with open("eastworld/miner/prompts/junior_action.txt", "r") as f:
            self.prompt_action_tpl = f.read()

        self.http_client = httpx.AsyncClient()

    def log_action(self, action: str):
        action_log = ActionLog(
            timestamp=datetime.datetime.now(),
            action=action.strip(),
            feedback="",
            repeat_times=1,
        )
        self.action_log.append(action_log)

    def log_feedback(self, feedback: str):
        if not self.action_log:
            # Miner may have restarted
            return

        last_log = self.action_log[-1]
        if last_log.feedback:
            # The last log already has feedback, unexpected
            return
        last_log.feedback = feedback.strip()

        if len(self.action_log) < 2:
            return
        previous_log = self.action_log[-2]
        if (
            previous_log.action == last_log.action
            and previous_log.feedback == last_log.feedback
        ):
            # Merge the two logs with the same action and feedback
            previous_log.timestamp = last_log.timestamp
            previous_log.repeat_times += 1
            self.action_log.pop()

    async def forward(self, synapse: Observation) -> Observation:
        bt.logging.info(f"Feedback of previous action: {synapse.action_log}")
        self.log_feedback("\n\n".join(synapse.action_log))

        # Generate new action
        messages = []
        messages.append({"role": "system", "content": self.prompt_system_tpl.format()})

        # Hardcoded tasks for demonstration
        tasks = """
  - Compete with other agents to achieve superior task performance: high priority
  - Locate a power generator: high priority
  - Survey the surroundings: medium priority
"""
        lidar = ""
        if synapse.scanner.get("lidar"):
            for items in synapse.scanner["lidar"]:
                lidar += f"  - {', '.join(items)}\n"
        perception = synapse.perception

        items = ""
        for item in synapse.items:
            if len(item) < 3:
                continue
            items += f"  - {item[0]}, {item[1]}, x{item[2]}\n"

        tool_list = ""
        for act in synapse.action_space:
            tool_list += (
                f"  - {act['function']['name']}: {act['function']['description']}\n"
            )

        action_log = ""
        for idx, l in enumerate(self.action_log):
            l: ActionLog
            repeat_str = (
                f" (repeated {l.repeat_times} times)" if l.repeat_times > 1 else ""
            )
            action_log += f"""
## Log {idx + 1}
    Action: {l.action}
    Result: {l.feedback} {repeat_str}
"""

        llm_client = AsyncOpenAI(http_client=self.http_client)
        try:
            reflection_context = {
                "tasks": tasks,
                "reflection": self.reflection,
                "lidar": lidar,
                "perception": perception,
                "items": items,
                "tool_list": tool_list,
                "action_log": action_log,
            }
            # Reflection first
            messages.append(
                {
                    "role": "user",
                    "content": self.prompt_reflection_tpl.format(**reflection_context),
                }
            )
            bt.logging.trace(messages[1]["content"], ">>>> Reflection Message")

            response = await llm_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_completion_tokens=1024,
                timeout=20,
            )

            if not response.choices[0].finish_reason in ["stop", "length"]:
                bt.logging.warning(f"LLM generation failed: {response}")
                return synapse

            self.reflection = response.choices[0].message.content

            # Take action then
            action_context = {
                "tasks": tasks,
                "reflection": self.reflection,
            }
            messages = [
                {"role": "system", "content": self.prompt_system_tpl.format()},
                {
                    "role": "user",
                    "content": self.prompt_action_tpl.format(**action_context),
                },
            ]
            bt.logging.trace(messages[1]["content"], ">>>> Action Message")
            # bt.logging.trace(synapse.action_space, ">>>> Action Space")
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=synapse.action_space,
                tool_choice="required",
                max_completion_tokens=1024,
                timeout=10,
            )

            if response.choices[0].finish_reason != "tool_calls":
                bt.logging.warning(f"LLM tool call failed: {response}")
                return synapse

            action = response.choices[0].message.tool_calls[0].function
            bt.logging.trace(action, ">>>> Action: ")
            if action:
                parsed_action = {
                    "name": action.name,
                    "arguments": json_repair.loads(action.arguments),
                }

                synapse.action = [parsed_action]
                self.log_action(
                    f"{action.name}, "
                    + ", ".join(
                        [f"{k}: {v}" for k, v in parsed_action["arguments"].items()]
                    )
                )
        except APITimeoutError as e:
            bt.logging.error(e)
        except Exception as e:
            bt.logging.error(e)
        finally:
            return synapse
