# API Documentation

This document provides API documentation for the GameAgent GridWorld RL Framework.

## Package Overview

The `gameagent` package provides tools for training and evaluating reinforcement learning agents on a GridWorld environment.

## Modules

### gameagent

Main package containing all components.

**Version**: 0.1.0

---

### gameagent.agent

Agent implementations and base classes.

#### BaseAgent

Abstract base class for all agents.

**Methods:**

- `act(observation) -> Action`
  - Select an action given current observation.
  - **Parameters:**
    - `observation`: Current state observation
  - **Returns:** Action to take
  - **Raises:** NotImplementedError if not implemented

- `set_training_mode(training: bool) -> None`
  - Toggle between training and evaluation mode.
  - **Parameters:**
    - `training`: True for training mode, False for evaluation

- `update(state, action, reward, next_state, done) -> None`
  - Update agent's knowledge based on experience.
  - **Parameters:**
    - `state`: Current state
    - `action`: Action taken
    - `reward`: Reward received
    - `next_state`: Next state after action
    - `done`: Whether episode terminated

#### GreedyAgent

Agent that always selects the action with highest Q-value.

**Inherits:** BaseAgent

**Methods:**
- `act(observation) -> Action`
  - Select action with maximum Q-value.
  - **Returns:** Action with highest Q-value

#### QLearningAgent

Q-learning agent with configurable parameters.

**Inherits:** BaseAgent

**Constructor:**
- `QLearningAgent(learning_rate: float = 0.2, discount_factor: float = 0.95, epsilon: float = 1.0, epsilon_decay: float = 0.995, epsilon_min: float = 0.01)`
  - **Parameters:**
    - `learning_rate`: Learning rate for Q-update (default: 0.2)
    - `discount_factor`: Discount factor for future rewards (default: 0.95)
    - `epsilon`: Initial exploration rate (default: 1.0)
    - `epsilon_decay`: Decay rate for epsilon (default: 0.995)
    - `epsilon_min`: Minimum epsilon value (default: 0.01)

**Attributes:**
- `q_table`: Dict mapping states to action values
- `learning_rate`: Learning rate
- `discount_factor`: Discount factor
- `epsilon`: Current exploration rate

**Methods:**
- `decay_epsilon() -> None`
  - Decay epsilon by epsilon_decay factor, bounded by epsilon_min

- `get_q_value(state, action) -> float`
  - Get Q-value for state-action pair.
  - **Returns:** Q-value (0.0 if not in table)

---

### gameagent.env

Environment definitions and types.

#### GridWorld

GridWorld environment for RL training.

**Constructor:**
- `GridWorld(config: GridConfig)`
  - **Parameters:**
    - `config`: GridConfig instance with environment settings

**Attributes:**
- `config`: GridConfig instance
- `width`: Grid width
- `height`: Grid height
- `goal_position`: Goal position tuple

**Methods:**

- `reset() -> tuple[tuple[int, int], dict]`
  - Reset environment to initial state.
  - **Returns:** (initial_observation, info)

- `step(action: Action) -> StepResult`
  - Execute action in environment.
  - **Parameters:**
    - `action`: Action to execute
  - **Returns:** StepResult with observation, reward, terminated, truncated, info

- `render() -> str`
  - Render current grid state as string.
  - **Returns:** String representation of grid

- `get_state() -> tuple[int, int]`
  - Get current agent position.
  - **Returns:** (row, col) position

#### GridConfig

Configuration for GridWorld environment.

**Fields:**
- `width: int` - Grid width
- `height: int` - Grid height
- `goal_position: tuple[int, int]` - Goal position
- `seed: int` - Random seed

#### Action

Enumeration of possible actions.

**Values:**
- `UP = 0` - Move up
- `DOWN = 1` - Move down
- `LEFT = 2` - Move left
- `RIGHT = 3` - Move right

#### StepResult

Result of a step in the environment.

**Fields:**
- `observation: tuple[int, int]` - New state
- `reward: float` - Reward received
- `terminated: bool` - Whether episode terminated
- `truncated: bool` - Whether episode was truncated
- `info: dict` - Additional information

---

### gameagent.sim

Simulation utilities.

#### EpisodeRunner

Runs episodes and collects metrics.

**Constructor:**
- `EpisodeRunner(config: SimulationConfig)`
  - **Parameters:**
    - `config`: SimulationConfig instance

**Methods:**

- `run(agent: BaseAgent) -> SimulationResult`
  - Run simulation with given agent.
  - **Parameters:**
    - `agent`: Agent to evaluate
  - **Returns:** SimulationResult with metrics

#### SimulationConfig

Configuration for simulation runs.

**Fields:**
- `num_episodes: int` - Number of episodes
- `grid_width: int` - Grid width
- `grid_height: int` - Grid height
- `goal_position: tuple[int, int]` - Goal position
- `seed: int` - Random seed
- `render: bool` - Whether to render
- `render_every: int` - Render frequency

#### SimulationResult

Results from simulation.

**Fields:**
- `total_episodes: int` - Total episodes run
- `mean_reward: float` - Mean reward
- `std_reward: float` - Standard deviation of rewards
- `mean_steps: int` - Mean steps per episode
- `success_rate: float` - Success rate
- `rewards: list[float]` - All rewards
- `steps: list[int]` - All step counts

---

### gameagent.trainer

Training and evaluation utilities.

#### GridWorldTrainer

Main training class.

**Constructor:**
- `GridWorldTrainer(config: TrainingConfig)`
  - **Parameters:**
    - `config`: TrainingConfig instance

**Methods:**

- `train() -> TrainingResult`
  - Run training loop.
  - **Returns:** TrainingResult with metrics

- `save_agent(path: str) -> None`
  - Save trained agent to JSON file.
  - **Parameters:**
    - `path`: Output file path

- `load_agent(path: str) -> QLearningAgent`
  - Load agent from JSON file.
  - **Parameters:**
    - `path`: Input file path
  - **Returns:** Loaded QLearningAgent

- `evaluate_agent(agent: BaseAgent, env: GridWorld, num_episodes: int = 100) -> dict`
  - Evaluate agent performance.
  - **Parameters:**
    - `agent`: Agent to evaluate
    - `env`: Environment to evaluate on
    - `num_episodes`: Number of episodes
  - **Returns:** Dict with metrics

- `run_benchmark(episodes: int = 1000, width: int = 5, height: int = 5) -> dict`
  - Run full benchmark.
  - **Parameters:**
    - `episodes`: Number of episodes per agent
    - `width`: Grid width
    - `height`: Grid height
  - **Returns:** Dict with benchmark results

#### TrainingConfig

Configuration for training.

**Fields:**
- `num_episodes: int` - Number of episodes
- `grid_width: int` - Grid width
- `grid_height: int` - Grid height
- `goal_position: tuple[int, int]` - Goal position
- `learning_rate: float` - Learning rate
- `discount_factor: float` - Discount factor
- `epsilon_start: float` - Initial epsilon
- `epsilon_decay: float` - Epsilon decay
- `epsilon_min: float` - Minimum epsilon
- `seed: int` - Random seed
- `save_path: str` - Save path
- `render_every: int` - Render frequency

#### TrainingResult

Results from training.

**Fields:**
- `rewards: list[float]` - Rewards per episode
- `steps: list[int]` - Steps per episode
- `epsilon_history: list[float]` - Epsilon values
- `final_epsilon: float` - Final epsilon

---

### gameagent.cli

Command-line interface.

**Commands:**

- `train` - Train a Q-learning agent
- `simulate` - Simulate agent behavior
- `benchmark` - Run full benchmark

**Usage:**
```bash
python -m gameagent.cli train [OPTIONS]
python -m gameagent.cli simulate [OPTIONS]
python -m gameagent.cli benchmark [OPTIONS]
```

---

### gameagent.visualize

Visualization utilities.

#### plot_training_curves

Plot training curves.

**Signature:**
```python
plot_training_curves(rewards: list[float], steps: list[int], save_path: str = None) -> None
```

**Parameters:**
- `rewards`: List of rewards per episode
- `steps`: List of steps per episode
- `save_path`: Optional path to save plot

#### render_grid

Render grid state.

**Signature:**
```python
render_grid(env: GridWorld, agent: BaseAgent = None, title: str = None) -> None
```

**Parameters:**
- `env`: GridWorld environment
- `agent`: Optional agent to show policy
- `title`: Optional plot title

---

### gameagent.benchmark

Benchmarking utilities.

#### benchmark_agent

Benchmark a single agent.

**Signature:**
```python
benchmark_agent(agent: BaseAgent, env: GridWorld, num_episodes: int = 100) -> dict
```

**Parameters:**
- `agent`: Agent to benchmark
- `env`: Environment to benchmark on
- `num_episodes`: Number of episodes

**Returns:** Dict with metrics

#### compare_agents

Compare multiple agents.

**Signature:**
```python
compare_agents(agents: dict[str, BaseAgent], env: GridWorld, num_episodes: int = 100) -> dict
```

**Parameters:**
- `agents`: Dict mapping names to agents
- `env`: Environment to benchmark on
- `num_episodes`: Number of episodes

**Returns:** Dict with comparison results
