# Architecture Overview

This document describes the architecture of the GameAgent GridWorld RL Framework.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GameAgent Framework                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Agent      │  │   Env        │  │   Sim        │          │
│  │   Layer      │  │   Layer      │  │   Layer      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ BaseAgent    │  │ GridWorld    │  │ EpisodeRunner│          │
│  │ GreedyAgent  │  │ GridConfig   │  │ SimConfig    │          │
│  │ QLearning    │  │ Action       │  │ SimResult    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Core       │  │   CLI        │  │   Utils      │          │
│  │   Layer      │  │   Layer      │  │   Layer      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Trainer      │  │ CLI Commands │  │ Visualize    │          │
│  │ TrainingCfg  │  │ train        │  │ Benchmark    │          │
│  │ TrainingRes  │  │ simulate     │  │              │          │
│  │              │  │ benchmark    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Agent Layer

The agent layer provides the interface and implementations for reinforcement learning agents.

**BaseAgent**: Abstract base class defining the agent interface:
- `act(observation)`: Select an action given current observation
- `set_training_mode(training)`: Toggle training vs evaluation mode
- `update(state, action, reward, next_state, done)`: Update agent's knowledge

**GreedyAgent**: A simple agent that always selects the action with highest Q-value.

**QLearningAgent**: Implements Q-learning algorithm:
- Maintains a Q-table mapping states to action values
- Uses epsilon-greedy exploration strategy
- Supports learning rate and discount factor configuration

### Environment Layer

The environment layer defines the GridWorld simulation environment.

**GridWorld**: The main environment class:
- Configurable grid size (width x height)
- Configurable goal position
- Random obstacle placement
- Step-based interaction protocol

**GridConfig**: Configuration dataclass for environment setup:
- `width`: Grid width in cells
- `height`: Grid height in cells
- `goal_position`: Target position (row, col)
- `seed`: Random seed for reproducibility

**Action**: Enum of possible actions:
- `UP`, `DOWN`, `LEFT`, `RIGHT`

### Simulation Layer

The simulation layer handles episode execution and result collection.

**EpisodeRunner**: Executes episodes and collects metrics:
- Runs multiple episodes with a given agent
- Tracks rewards, steps, and termination conditions
- Supports rendering during simulation

**SimulationConfig**: Configuration for simulation runs:
- `num_episodes`: Number of episodes to run
- `grid_width`, `grid_height`: Grid dimensions
- `goal_position`: Goal location
- `seed`: Random seed
- `render`: Whether to render episodes
- `render_every`: Frequency of rendering

**SimulationResult**: Results from simulation:
- `total_episodes`: Number of episodes completed
- `mean_reward`: Average reward per episode
- `std_reward`: Standard deviation of rewards
- `mean_steps`: Average steps per episode
- `success_rate`: Fraction of successful episodes
- `rewards`: List of all rewards
- `steps`: List of all step counts

### Core Layer

The core layer provides training and evaluation utilities.

**GridWorldTrainer**: Main training class:
- `train()`: Run training loop
- `save_agent()`: Persist trained agent to JSON
- `load_agent()`: Load agent from JSON
- `evaluate_agent()`: Evaluate agent performance
- `run_benchmark()`: Compare multiple agents

**TrainingConfig**: Configuration for training:
- `num_episodes`: Number of training episodes
- `grid_width`, `grid_height`: Grid dimensions
- `goal_position`: Goal location
- `learning_rate`: Q-learning learning rate
- `discount_factor`: Q-learning discount factor
- `epsilon_start`, `epsilon_decay`, `epsilon_min`: Exploration parameters
- `seed`: Random seed
- `save_path`: Output path for trained agent
- `render_every`: Frequency of rendering during training

**TrainingResult**: Results from training:
- `rewards`: List of rewards per episode
- `steps`: List of steps per episode
- `epsilon_history`: Epsilon values over training
- `final_epsilon`: Final epsilon value

### CLI Layer

The CLI layer provides command-line interface for all operations.

**Commands**:
- `train`: Train a Q-learning agent
- `simulate`: Run simulations with trained agents
- `benchmark`: Run full benchmark comparing agents

### Utility Layer

The utility layer provides visualization and benchmarking tools.

**Visualize**:
- `plot_training_curves()`: Generate plots of training progress
- `render_grid()`: Render current grid state

**Benchmark**:
- `benchmark_agent()`: Measure performance of single agent
- `compare_agents()`: Compare multiple agents

## Data Flow

### Training Flow

1. User specifies training configuration via CLI or programmatically
2. GridWorldTrainer creates GridWorld environment and QLearningAgent
3. Training loop executes episodes:
   - Agent selects action using epsilon-greedy policy
   - Environment returns reward and next state
   - Agent updates Q-table using Q-learning update rule
   - Epsilon decays over episodes
4. Training results are collected and returned
5. Trained agent is saved to JSON

### Evaluation Flow

1. User specifies evaluation configuration
2. GridWorldTrainer creates environment and loads agent
3. Agent evaluates over multiple episodes:
   - Agent uses greedy policy (no exploration)
   - Environment returns reward and next state
   - Metrics are collected
4. Results include mean reward, success rate, and step counts

### Benchmark Flow

1. User specifies benchmark configuration
2. Multiple agents are evaluated on same environment
3. Results are compared and displayed
4. Benchmark includes RandomAgent, GreedyAgent, and trained QLearningAgent

## Design Patterns

### Strategy Pattern

Agents implement the BaseAgent interface, allowing different agent types to be swapped interchangeably.

### Factory Pattern

GridWorldTrainer acts as a factory for creating environments and agents with consistent configurations.

### Observer Pattern

Training progress is reported via print statements, allowing for potential extension to logging systems.

## Extension Points

### Adding New Agents

1. Create new class inheriting from BaseAgent
2. Implement `act()`, `set_training_mode()`, and `update()` methods
3. Register in `gameagent/agent/__init__.py`

### Adding New Environments

1. Create new environment class following GridWorld interface
2. Define configuration dataclass
3. Update CLI to support new environment

### Adding New Commands

1. Create command handler function
2. Add argument parser configuration
3. Register in main() function

## Dependencies

- **numpy**: Numerical computations
- **json**: Agent serialization
- **argparse**: CLI argument parsing
- **matplotlib**: Visualization (optional)
- **hypothesis**: Property-based testing (optional)
- **pytest**: Testing framework (optional)
