"""Training script for DQN agent on GridWorld environment."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np

from gameagent.agent.dqn_agent import DQNAgent, DQNConfig
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import Action, GridConfig


def train_dqn(
    env: GridWorld,
    agent: DQNAgent,
    num_episodes: int = 1000,
    max_steps_per_episode: int = 100,
    log_interval: int = 10,
    save_interval: int = 100,
    save_dir: str = "checkpoints",
) -> None:
    """Train the DQN agent.

    Args:
        env: GridWorld environment.
        agent: DQNAgent to train.
        num_episodes: Number of training episodes.
        max_steps_per_episode: Maximum steps per episode.
        log_interval: How often to log training progress.
        save_interval: How often to save the model.
        save_dir: Directory to save checkpoints.
    """
    os.makedirs(save_dir, exist_ok=True)

    episode_rewards = []
    episode_lengths = []

    for episode in range(num_episodes):
        observation, _ = env.reset()
        state = agent._encode_state(observation)
        total_reward = 0.0
        step = 0

        while step < max_steps_per_episode:
            action = agent.act(observation)
            next_observation, reward, done, info = env.step(action)
            next_state = agent._encode_state(next_observation)

            agent.update(state, action.value, reward, next_state, done)
            state = next_state
            total_reward += reward
            step += 1

            if done:
                break

            observation = next_observation

        episode_rewards.append(total_reward)
        episode_lengths.append(step)

        # Decay exploration
        agent.decay_epsilon()

        # Log progress
        if (episode + 1) % log_interval == 0:
            avg_reward = np.mean(episode_rewards[-log_interval:])
            avg_length = np.mean(episode_lengths[-log_interval:])
            print(f"Episode {episode + 1}/{num_episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Length: {avg_length:.1f} | "
                  f"Epsilon: {agent.epsilon:.3f}")

        # Save checkpoint
        if (episode + 1) % save_interval == 0:
            save_path = Path(save_dir) / f"dqn_checkpoint_{episode + 1}.pt"
            np.save(str(save_path), agent.network.weights)
            print(f"Saved checkpoint to {save_path}")

    # Final save
    final_path = Path(save_dir) / "dqn_final.pt"
    np.save(str(final_path), agent.network.weights)
    print(f"Saved final model to {final_path}")


def evaluate_dqn(
    env: GridWorld,
    agent: DQNAgent,
    num_episodes: int = 100,
    max_steps_per_episode: int = 100,
    checkpoint_path: str = "checkpoints/dqn_final.pt",
) -> None:
    """Evaluate the trained DQN agent.

    Args:
        env: GridWorld environment.
        agent: DQNAgent to evaluate.
        num_episodes: Number of evaluation episodes.
        max_steps_per_episode: Maximum steps per episode.
        checkpoint_path: Path to load the model from.
    """
    # Load checkpoint
    if os.path.exists(checkpoint_path):
        weights = np.load(checkpoint_path, allow_pickle=True)
        for (w1, b1), (w2, b2) in zip(agent.network.weights, weights):
            w1[:] = w2.copy()
            b1[:] = b2.copy()
        print(f"Loaded model from {checkpoint_path}")
    else:
        print(f"Checkpoint not found: {checkpoint_path}")
        return

    # Disable training mode
    agent.set_training_mode(False)

    episode_rewards = []
    episode_lengths = []

    for episode in range(num_episodes):
        observation, _ = env.reset()
        state = agent._encode_state(observation)
        total_reward = 0.0
        step = 0

        while step < max_steps_per_episode:
            action = agent.act(observation)
            next_observation, reward, done, info = env.step(action)
            next_state = agent._encode_state(next_observation)
            state = next_state
            total_reward += reward
            step += 1

            if done:
                break

            observation = next_observation

        episode_rewards.append(total_reward)
        episode_lengths.append(step)

    avg_reward = np.mean(episode_rewards)
    avg_length = np.mean(episode_lengths)
    success_rate = sum(1 for r in episode_rewards if r > 0) / num_episodes

    print(f"\nEvaluation Results ({num_episodes} episodes):")
    print(f"  Average Reward: {avg_reward:.2f}")
    print(f"  Average Length: {avg_length:.1f}")
    print(f"  Success Rate: {success_rate:.2%}")


def main() -> None:
    """Main entry point for training and evaluation."""
    parser = argparse.ArgumentParser(description="Train and evaluate DQN agent")
    parser.add_argument("--train", action="store_true", help="Train the agent")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate the agent")
    parser.add_argument("--episodes", type=int, default=1000, help="Number of episodes")
    parser.add_argument("--steps", type=int, default=100, help="Max steps per episode")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/dqn_final.pt",
                        help="Path to checkpoint for evaluation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--hidden-layers", type=str, default="64,32",
                        help="Hidden layer sizes (comma-separated)")
    parser.add_argument("--grid-size", type=int, default=10, help="Grid size")
    parser.add_argument("--obstacles", type=int, default=10, help="Number of obstacles")

    args = parser.parse_args()

    # Create environment
    config = GridConfig(
        width=args.grid_size,
        height=args.grid_size,
        goal_position=(args.grid_size - 1, args.grid_size - 1),
        seed=args.seed,
    )
    env = GridWorld(config=config)

    # Create agent
    hidden_layers = tuple(int(x) for x in args.hidden_layers.split(","))
    dqn_config = DQNConfig(
        seed=args.seed,
        hidden_layers=hidden_layers,
    )
    agent = DQNAgent(config=dqn_config)

    if args.train:
        train_dqn(
            env=env,
            agent=agent,
            num_episodes=args.episodes,
            max_steps_per_episode=args.steps,
            save_dir="checkpoints",
        )

    if args.evaluate:
        evaluate_dqn(
            env=env,
            agent=agent,
            num_episodes=100,
            max_steps_per_episode=args.steps,
            checkpoint_path=args.checkpoint,
        )


if __name__ == "__main__":
    main()
