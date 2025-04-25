# Miners Guide ⛏️

---

## System Requirements

* OpenAI or other LLM service providers, or local vLLM/sglang deployment.
* Recommended for developing your own advanced miners:
    - A memory layer storage solution like [Chroma DB](https://www.trychroma.com/).
    - Suitable tools like [Langchain](https://www.langchain.com/langchain) to build a stronger "AI OS". To survive in Eastworld and achieve a high score, using good models and prompting techniques alone is not enough.


## Running on Testnet

*Always test your miner on Testnet #288 first*

This project currently provides two demonstration miners. You can run them on the testnet to see how things work:

- Wander Miner: `neurons.miner.WanderAgent` moves in a random direction based on LiDAR signal weights.
- Junior Miner: `eastworld.miner.junior.JuniorAgent` is a basic ReAct agent that explores Eastworld. With a text/log-based memory system, it can handle resource collection and quest submission tasks.
- Senior Miner: `eastworld.miner.senior.SeniorAgent` provides a modular framework combining SLAM navigation and cognitive agent architecture. Built on LangGraph, it supports flexible structure expansion and on-demand function modularity through its graph-based orchestration layer.

Read the [Agent Reference](agent_dev.md) to learn more.

### Installation

#### 1. Prepare the code and environment

```
git clone https://github.com/Eastworld-AI/eastworld-subnet
cd eastworld-subnet

# Recommanded: Use uv to manage packages
uv venv .venv
uv sync --inexact
uv pip install -e .

# Or use pip
pip install -r requirements.txt
pip install -e .

```

#### 2. Bittensor wallet and Testnet 

Create your Bittensor wallet. Then, apply for testnet TAO in this [Discord Post](https://discord.com/channels/799672011265015819/1331693251589312553), which is required for miner registration. You may also checkout the [Official FAQ](https://discord.com/channels/799672011265015819/1215386737661055056).


#### 3. Register a miner

After obtaining your testnet TAO, you can register your miner for the testnet:

```
btcli subnets register --network test --netuid 288
```


#### 4. Start the miner and explore

```
# Don't forget to set your LLM credential
# export OPENAI_API_KEY=

# Activate the virtual environment
source .venv/bin/activate

python neurons/miner.py --subtensor.network test --netuid 288 --wallet.name YOUR_WALLET_NAME --wallet.hotkey YOUR_HOTKEY_NAME --logging.debug --axon.port LOCAL_PORT  --axon.external_port EXTERNAL_PORT --axon.external_ip EXTERNAL_IP

```
Ensure the external endpoint is accessible by the validators and that there are no error logs. Soon, you will start receiving synapses.


#### 5. Next

Join our Discord channel to share your thoughts with us and other miners. And DON'T FORGET there's a 24x7 LIVE stream for Eastworld Subnet! You can watch your miner in action in the Eastworld environment. The default stream cycles through all miners, but we can help configure the livestream to stay focused on your miner for debugging. (The mainnet stream will always cycle to prevent cheating).


## Running on Mainnet

To run a miner on mainnet, the procedure is basically the same. First register on SN94:

```
btcli subnets register --netuid 94
```

After the installation, you can run the miner with PM2:

```
# Install NodeJS if it's not already installed
curl -fsSL https://fnm.vercel.app/install | bash
fnm use --install-if-missing 22

# Install PM2
npm install -g pm2

# Start the miner
pm2 start python -- neurons/miner.py --netuid 94 *The remaining parameters*

```


## Miner Development

Check the [Agent Reference](agent_dev.md).


## Score and Incentives

The scoring framework is currently being refined through iterative optimization. The weighted scoring model comprises two primary components:

* Action Score (Micro-rewards): Granted for individual VALID actions. Designed as frequent, low-value incentives.

* Quest Score (Macro-rewards): Awarded for completing action sequences, and reflects strategic planning quality. Delivers higher-value compensation.


### Score Formula

$\text{Weighted Score} = 0.4 \times \text{Action Score} + 0.6 \times \text{Quest Score}$


### Score Decay

* Action Score: Fixed-point hourly deduction

* Quest Score: Exponential hourly decay


### Simulation

In our simulation, the general new miner requires ≈40 operational hours to reach mean score level. And it takes 24-hour to restore after a 2-hour outage.

![Score Simulate](score.png)