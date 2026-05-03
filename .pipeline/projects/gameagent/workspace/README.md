# GameAgent - GridWorld RL Framework

A Python framework for training and evaluating reinforcement learning agents on a GridWorld environment.

## Installation

### Prerequisites

- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -e .
```

### Optional Dependencies

For visualization, testing, and documentation:

```bash
pip install -e ".[dev]"
```

This installs:
- matplotlib - For visualization
- hypothesis - For property-based testing
- pytest-benchmark - For benchmarking
- sphinx and sphinx-rtd-theme - For documentation
- flake8 - For linting
- black - For formatting
- mypy - For type checking

## Quick Start

### Training an Agent

Train a Q-learning agent with default settings:

```bash
python -m gameagent.cli train --episodes 1000
```

Train with custom parameters:

```bash
python -m gameagent.cli train \
    --episodes 2000 \
    --width 10 \
    --height 10 \
    --lr 0.1 \
    --gamma 0.99 \
    --epsilon-start 1.0 \
    --epsilon-decay 0.99 \
    --epsilon-min 0.05 \
    --seed 42 \
    --save my_trained_agent.json \
    --render-every 100
```

### Simulating a Trained Agent

Run simulations with a trained agent:

```bash
python -m gameagent.cli simulate \
    --agent my_trained_agent.json \
    --episodes 100 \
    --width 5 \
    --height 5
```

Render episodes during simulation:

```bash
python -m gameagent.cli simulate \
    --agent my_trained_agent.json \
    --episodes 50 \
    --render \
    --render-every 10
```

### Running Benchmarks

Run a full benchmark comparing different agents:

```bash
python -m gameagent.cli benchmark \
    --episodes 1000 \
    --width 5 \
    --height 5
```

## Project Structure

```
gameagent/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point for python -m gameagent
├── cli.py               # Command-line interface
├── trainer.py           # Training and evaluation utilities
├── agent/
│   ├── __init__.py
│   ├── base.py          # Base agent interface
│   ├── greedy_agent.py  # Greedy agent implementation
│   └── q_learning.py    # Q-learning agent implementation
├── env/
│   ├── __init__.py
│   ├── grid_world.py    # GridWorld environment
│   └── types.py         # Type definitions
├── sim/
│   ├── __init__.py
│   ├── runner.py        # Episode runner
│   └── types.py         # Simulation types
├── visualize.py         # Visualization utilities
└── benchmark.py         # Benchmarking utilities
```

## Usage Examples

### Programmatic Usage

```python
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig
from gameagent.agent.q_learning import QLearningAgent
from gameagent.trainer import GridWorldTrainer, TrainingConfig

# Create environment
config = GridConfig(width=5, height=5, goal_position=(4, 4))
env = GridWorld(config=config)

# Create and train agent
training_config = TrainingConfig(num_episodes=1000)
trainer = GridWorldTrainer(training_config)
result = trainer.train()

# Save and load agent
trainer.save_agent("trained_agent.json")
agent = trainer.load_agent("trained_agent.json")

# Evaluate
metrics = trainer.evaluate_agent(agent, env, num_episodes=100)
print(f"Success Rate: {metrics['success_rate']:.2%}")
```

### Using Visualization

```python
from gameagent.visualize import plot_training_curves, render_grid
from gameagent.trainer import TrainingConfig, GridWorldTrainer

# Train and visualize
trainer = GridWorldTrainer(TrainingConfig(num_episodes=500))
result = trainer.train()
trainer.save_agent()

# Plot training curves
plot_training_curves(result.rewards, result.steps, save_path="training_curves.png")

# Render grid state
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig

env = GridWorld(config=GridConfig(width=5, height=5))
render_grid(env, None, title="Initial Grid State")
```

### Using Benchmarking

```python
from gameagent.benchmark import benchmark_agent, compare_agents
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig
from gameagent.agent import RandomAgent, GreedyAgent, QLearningAgent

env = GridWorld(config=GridConfig(width=5, height=5))

# Benchmark a single agent
metrics = benchmark_agent(QLearningAgent(), env, num_episodes=100)
print(f"Mean Reward: {metrics['mean_reward']:.2f}")

# Compare multiple agents
results = compare_agents(
    {"Random": RandomAgent(), "Greedy": GreedyAgent(), "QLearning": QLearningAgent()},
    env,
    num_episodes=100
)
```

## Command-Line Reference

### train

Train a Q-learning agent.

```
usage: gameagent train [-h] [--episodes EPISODES] [--width WIDTH] [--height HEIGHT]
                       [--lr LR] [--gamma GAMMA] [--epsilon-start EPSILON_START]
                       [--epsilon-decay EPSILON_DECAY] [--epsilon-min EPSILON_MIN]
                       [--seed SEED] [--save SAVE] [--render-every RENDER_EVERY]
```

### simulate

Simulate agent behavior.

```
usage: gameagent simulate [-h] [--agent AGENT] [--episodes EPISODES] [--width WIDTH]
                          [--height HEIGHT] [--seed SEED] [--render] [--render-every RENDER_EVERY]
                          [--save-results SAVE_RESULTS]
```

### benchmark

Run full benchmark.

```
usage: gameagent benchmark [-h] [--episodes EPISODES] [--width WIDTH] [--height HEIGHT]
                           [--lr LR] [--gamma GAMMA] [--epsilon-start EPSILON_START]
                           [--epsilon-decay EPSILON_DECAY] [--epsilon-min EPSILON_MIN]
                           [--seed SEED] [--save SAVE] [--render-every RENDER_EVERY]
```

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=gameagent --cov-report=html
```

Run property-based tests:

```bash
pytest tests/test_property_based.py -v
```

## License

MIT License
