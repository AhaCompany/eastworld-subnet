# The MIT License (MIT)
# Copyright 2025 Eastworld AI

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
import traceback
from collections import deque

import bittensor as bt
import httpx
import json_repair
from openai import AsyncOpenAI, APITimeoutError
from pydantic import BaseModel

from eastworld.protocol import Observation
from eastworld.base.miner import BaseMinerNeuron
from eastworld.miner.miner_memory import MinerMemory

class ActionLog(BaseModel):
    timestamp: datetime.datetime
    action: str
    feedback: str
    repeat_times: int


class JuniorAgent(BaseMinerNeuron):
    memory_reflection: deque
    memory_action: deque

    prompt_system_tpl: str
    prompt_reflection_tpl: str
    prompt_action_tpl: str

    http_client: httpx.AsyncClient

    def __init__(self, config=None):
        super(JuniorAgent, self).__init__(config=config)

        self.memory_reflection = deque(maxlen=100)
        self.memory_action = deque(maxlen=100)

        self.miner_memory = MinerMemory()

        with open("eastworld/miner/prompts/junior_system.txt", "r") as f:
            self.prompt_system_tpl = f.read()
        with open("eastworld/miner/prompts/junior_reflection.txt", "r") as f:
            self.prompt_reflection_tpl = f.read()
        with open("eastworld/miner/prompts/junior_action.txt", "r") as f:
            self.prompt_action_tpl = f.read()

        self.http_client = httpx.AsyncClient()

    def push_reflection_memory(self, reflection: str):
        self.memory_reflection.append(reflection)

    def push_action_memory(self, action: str):
        action_log = ActionLog(
            timestamp=datetime.datetime.now(),
            action=action.strip(),
            feedback="",
            repeat_times=1,
        )
        self.memory_action.append(action_log)

    def update_action_memory(self, feedback: str):
        """
        This function updates the feedback of the last action in the memory.

        The action log is added to the memory immediately after the submission. But the action
        result is only available in the next observation.
        """
        if not self.memory_action:
            # Miner may have restarted and the last action is lost
            return

        last_log = self.memory_action[-1]
        if last_log.feedback:
            # The last log already has feedback, unexpected behavior
            return
        last_log.feedback = feedback.strip()

        # Try to merge the last two logs if they are the same
        if len(self.memory_action) < 2:
            return
        previous_log = self.memory_action[-2]
        if (
            previous_log.action == last_log.action
            and previous_log.feedback == last_log.feedback
        ):
            # Merge the two logs with the same action and feedback
            previous_log.timestamp = last_log.timestamp
            previous_log.repeat_times += 1
            self.memory_action.pop()

        # --- ADD: Update feedback/result in MinerMemory DB for last action ---
        # Find the most recent 'pending' action for the current quest and update it
        current_quest = ""
        if hasattr(self, 'last_quest'):
            current_quest = self.last_quest
        elif self.memory_action:
            # Try to extract from last action if possible
            current_quest = getattr(self.memory_action[-1], 'quest', "")

        # Check if feedback indicates success or failure
        result = "unknown"
        if "[SUCCESS]" in last_log.feedback:
            result = "SUCCESS"
        elif "[FAILURE]" in last_log.feedback:
            result = "FAILURE"
        else:
            result = last_log.feedback  # Use full feedback as result if no explicit status

        # Use the most recent action for this quest
        import sqlite3
        try:
            bt.logging.info(f"MinerMemory: Updating pending action result to '{result}' for quest '{current_quest}'")

            # First check if there's any pending action to update
            c = self.miner_memory.conn.cursor()
            c.execute('''
                SELECT id, action FROM actions 
                WHERE quest=? AND result='pending' 
                ORDER BY id DESC LIMIT 1
            ''', (current_quest,))
            pending_action = c.fetchone()

            if pending_action:
                action_id, action_name = pending_action
                bt.logging.info(f"MinerMemory: Found pending action #{action_id}: {action_name}")

                # Update the pending action with actual result
                c.execute('''
                    UPDATE actions SET result=?, feedback=?
                    WHERE id = ?
                ''', (result, last_log.feedback, action_id))
                self.miner_memory.conn.commit()
                bt.logging.info(f"MinerMemory: Successfully updated action #{action_id} with result: {result}")
            else:
                bt.logging.warning(f"MinerMemory: No pending action found for quest '{current_quest}'")

        except sqlite3.Error as e:
            bt.logging.error(f"MinerMemory: Failed to update action feedback in DB: {e}")
        except Exception as e:
            bt.logging.error(f"MinerMemory: Unexpected error updating action feedback: {e}")

    async def forward(self, synapse: Observation) -> Observation:
        bt.logging.info(f"Feedback of previous action: {synapse.action_log}")
        self.update_action_memory("\n\n".join(synapse.action_log))

        current_quest = ""
        if hasattr(synapse, 'tasks') and synapse.tasks:
            current_quest = synapse.tasks[0]['description'] if isinstance(synapse.tasks[0], dict) else str(synapse.tasks[0])
        inventory_full = False
        if hasattr(synapse, 'items'):
            for item in synapse.items:
                if hasattr(item, 'is_full') and item.is_full:
                    inventory_full = True
                    self.miner_memory.log_inventory(item.name, 'full')
                else:
                    self.miner_memory.log_inventory(item.name, 'available')

        blocked_dirs = self.miner_memory.get_blocked_directions(current_quest)
        recent_actions = self.miner_memory.get_recent_actions(current_quest)

        # Lấy ID của các action gần đây
        action_ids = []
        try:
            c = self.miner_memory.conn.cursor()
            c.execute('''
                SELECT id, action, direction, result, feedback 
                FROM actions
                WHERE quest=?
                ORDER BY id DESC
                LIMIT 50
            ''', (current_quest,))
            
            action_details = c.fetchall()
            action_log = ""
            
            if action_details:
                for row in action_details:
                    action_id, action, direction, result, feedback = row
                    direction_str = f"({direction})" if direction else ""
                    action_log += f"#{action_id}: {action} {direction_str}, Result: {result}, Feedback: {feedback}\n"
            else:
                # Fallback nếu không lấy được ID từ DB
                for idx, (action, direction, result, feedback, reflection) in enumerate(recent_actions):
                    direction_str = f"({direction})" if direction else ""
                    action_log += f"#{idx+1}: {action} {direction_str}, Result: {result}, Feedback: {feedback}\n"
        except Exception as e:
            bt.logging.error(f"Error getting action IDs: {e}")
            # Fallback nếu có lỗi
            action_log = ""
            for idx, (action, direction, result, feedback, reflection) in enumerate(recent_actions):
                direction_str = f"({direction})" if direction else ""
                action_log += f"#{idx+1}: {action} {direction_str}, Result: {result}, Feedback: {feedback}\n"
        
        blocked_dirs_str = ', '.join([d for d in blocked_dirs if d])
        
        tasks = getattr(synapse, 'tasks', [])
        lidar = getattr(synapse, 'lidar', 'N/A')
        odometry = getattr(synapse, 'odometry', 'N/A')
        perception = getattr(synapse, 'perception', 'N/A')
        items = ""
        for item in getattr(synapse, 'items', []):
            items += f"  - {item.name}, Amount {getattr(item, 'count', '?')}, Description: {getattr(item, 'description', '').strip()}\n"
        tool_list = ""
        for act in getattr(synapse, 'action_space', []):
            tool_list += (
                f"  - {act['function']['name']}: {act['function']['description']}\n"
            )

        reflection_context = {
            "tasks": tasks,
            "reflection": (self.memory_reflection[-1] if self.memory_reflection else "N/A"),
            "lidar": lidar,
            "odometry": odometry,
            "perception": perception,
            "items": items,
            "tool_list": tool_list,
            "action_log": action_log,
            "blocked_dirs": blocked_dirs_str,
            "inventory_full": inventory_full,
        }

        messages = [
            {"role": "system", "content": self.prompt_system_tpl.format()},
            {
                "role": "user",
                "content": self.prompt_reflection_tpl.format(**reflection_context),
            },
        ]
        bt.logging.trace(messages[1]["content"], ">>>> Reflection Prompt")

        llm_client = AsyncOpenAI(http_client=self.http_client)
        try:
            response = await llm_client.chat.completions.create(
                model=self.config.eastworld.llm_model,
                messages=messages,
                max_completion_tokens=1024,
                timeout=20,
            )

            if not response.choices[0].finish_reason in ["stop", "length"]:
                bt.logging.warning(f"LLM generation failed: {response}")
                return synapse

            reflection = response.choices[0].message.content.strip()
            self.push_reflection_memory(reflection)
            bt.logging.debug(self.memory_reflection[-1], ">>>> Reflection")

            # Luôn log action với reflection bất kể có recent_actions hay không
            if recent_actions:
                last_action = recent_actions[0]
                bt.logging.info(f"MinerMemory: Updating existing action with reflection: {last_action[0]}")
                self.miner_memory.log_action(
                    quest=current_quest,
                    action=last_action[0],
                    direction=last_action[1],
                    result=last_action[2],
                    feedback=last_action[3],
                    reflection=reflection
                )
            else:
                bt.logging.info(f"MinerMemory: Logging new action with reflection: ")
                self.miner_memory.log_action(
                    quest=current_quest,
                    action="",
                    direction="",
                    result="",
                    feedback="",
                    reflection=reflection
                )

            action_context = {
                "tasks": tasks,
                "reflection": (self.memory_reflection[-1] if self.memory_reflection else "N/A"),
                "blocked_dirs": blocked_dirs_str,
                "inventory_full": inventory_full,
            }
            messages = [
                {
                    "role": "user",
                    "content": self.prompt_action_tpl.format(**action_context),
                },
            ]
            bt.logging.trace(messages[0]["content"], ">>>> Action Prompt")
            response = await llm_client.chat.completions.create(
                model=self.config.eastworld.llm_model,
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
                self.push_action_memory(
                    f"{action.name}, "
                    + ", ".join(
                        [f"{k}: {v}" for k, v in parsed_action["arguments"].items()]
                    )
                )
                # Luôn log action mới, không phụ thuộc vào recent_actions
                # Use bt.logging.info để dễ debug
                bt.logging.info(f"MinerMemory: Logging new action: {parsed_action['name']}")
                log_success = self.miner_memory.log_action(
                    quest=current_quest,
                    action=parsed_action["name"],
                    direction=parsed_action["arguments"].get("direction", ""),
                    result="pending",  # Will be updated after feedback
                    feedback="",
                    reflection=""
                )
                if not log_success:
                    bt.logging.warning(f"MinerMemory: Failed to log new action {parsed_action['name']}")
        except APITimeoutError as e:
            bt.logging.error(f"API Timeout Error: {e}")
        except Exception as e:
            traceback.print_exc()
        finally:
            return synapse
