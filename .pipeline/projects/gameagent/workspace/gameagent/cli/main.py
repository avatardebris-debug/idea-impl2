"""Command-line interface for GridWorld agent training and evaluation."""

from __future__ import annotations

import argparse
import json
import sys

from gameagent.agent.base import RandomAgent
from gameagent.agent.greedy_agent import GreedyAgent
from gameagent.agent.q_learning import QLearningAgent
from gameagent.env.types import GridConfig
from gameagent.sim.runner import EpisodeRunner
from gameagent.sim.types import SimulationConfig
from gameagent.trainer import GridWorldTrainer, TrainingConfig, TrainingResult


def cmd_train(args: argparse.Namespace) -> int:
    """Run the training command."""
    training_config = TrainingConfig(
        num_episodes=args.episodes,
        grid_width=args.width,
        grid_height=args.height,
        goal_position=(args.height - 1, args.width - 1),
        learning_rate=args.lr,
        discount_factor=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_decay=args.epsilon_decay,
        epsilon_min=args.epsilon_min,
        seed=args.seed,
        save_path=args.save,
        render_every=args.render_every,
    )

    trainer = GridWorldTrainer(training_config)
    result = trainer.train()

    # Save the trained agent
    trainer.save_agent()

    # Run benchmark
    benchmark_results = trainer.run_benchmark()

    # Print summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    for agent_name, metrics in benchmark_results.items():
        print(f"\n{agent_name}:")
        print(f"  Mean Reward: {metrics['mean_reward']:.2f} ± {metrics['std_reward']:.2f}")
        print(f"  Mean Steps: {metrics['mean_steps']:.1f}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")

    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    """Run the simulation command."""
    # Load the trained agent
    if args.agent:
        trainer = GridWorldTrainer(TrainingConfig())
        agent = trainer.load_agent(args.agent)
    else:
        agent = QLearningAgent()

    # Create simulation config
    sim_config = SimulationConfig(
        num_episodes=args.episodes,
        grid_width=args.width,
        grid_height=args.height,
        goal_position=(args.height - 1, args.width - 1),
        seed=args.seed,
        render=args.render,
    )

    # Run simulation
    runner = EpisodeRunner(sim_config, agent=agent)
    results = runner.run_simulation()

    # Print results
    print("\n" + "=" * 50)
    print("SIMULATION RESULTS")
    print("=" * 50)
    print(f"Total Episodes: {results.total_episodes}")
    print(f"Mean Reward: {results.mean_reward:.2f} ± {results.std_reward:.2f}")
    print(f"Mean Steps: {results.mean_steps:.1f}")
    print(f"Success Rate: {results.success_rate:.2%}")

    if args.save_results:
        output_path = args.save_results
        with open(output_path, "w") as f:
            json.dump({
                "total_episodes": results.total_episodes,
                "mean_reward": results.mean_reward,
                "std_reward": results.std_reward,
                "mean_steps": results.mean_steps,
                "success_rate": results.success_rate,
            }, f, indent=2)
        print(f"\nResults saved to {args.save_results}")

    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Run the benchmark command."""
    # Create training config
    training_config = TrainingConfig(
        num_episodes=args.episodes,
        grid_width=args.width,
        grid_height=args.height,
        goal_position=(args.height - 1, args.width - 1),
        learning_rate=args.lr,
        discount_factor=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_decay=args.epsilon_decay,
        epsilon_min=args.epsilon_min,
        seed=args.seed,
        save_path=args.save,
        render_every=args.render_every,
    )

    trainer = GridWorldTrainer(training_config)
    result = trainer.train()
    trainer.save_agent()

    # Run benchmark
    benchmark_results = trainer.run_benchmark()

    # Print summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    for agent_name, metrics in benchmark_results.items():
        print(f"\n{agent_name}:")
        print(f"  Mean Reward: {metrics['mean_reward']:.2f} ± {metrics['std_reward']:.2f}")
        print(f"  Mean Steps: {metrics['mean_steps']:.1f}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="GridWorld Agent System - Train and evaluate RL agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train a Q-learning agent
  python -m gameagent.cli train --episodes 1000

  # Simulate with a trained agent
  python -m gameagent.cli simulate --agent trained_agent.json --episodes 100

  # Run a full benchmark
  python -m gameagent.cli benchmark --episodes 500
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train a Q-learning agent")
    train_parser.add_argument("--episodes", type=int, default=1000, help="Number of training episodes")
    train_parser.add_argument("--width", type=int, default=5, help="Grid width")
    train_parser.add_argument("--height", type=int, default=5, help="Grid height")
    train_parser.add_argument("--lr", type=float, default=0.2, help="Learning rate")
    train_parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    train_parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial epsilon")
    train_parser.add_argument("--epsilon-decay", type=float, default=0.995, help="Epsilon decay rate")
    train_parser.add_argument("--epsilon-min", type=float, default=0.01, help="Minimum epsilon")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    train_parser.add_argument("--save", type=str, default="trained_agent.json", help="Output file for trained agent")
    train_parser.add_argument("--render-every", type=int, default=200, help="Render every N episodes")

    # Simulate command
    sim_parser = subparsers.add_parser("simulate", help="Simulate agent behavior")
    sim_parser.add_argument("--agent", type=str, help="Path to trained agent JSON file")
    sim_parser.add_argument("--episodes", type=int, default=100, help="Number of episodes to simulate")
    sim_parser.add_argument("--width", type=int, default=5, help="Grid width")
    sim_parser.add_argument("--height", type=int, default=5, help="Grid height")
    sim_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    sim_parser.add_argument("--render", action="store_true", help="Render episodes")
    sim_parser.add_argument("--save-results", type=str, help="Save results to JSON file")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run full benchmark")
    bench_parser.add_argument("--episodes", type=int, default=1000, help="Number of training episodes")
    bench_parser.add_argument("--width", type=int, default=5, help="Grid width")
    bench_parser.add_argument("--height", type=int, default=5, help="Grid height")
    bench_parser.add_argument("--lr", type=float, default=0.2, help="Learning rate")
    bench_parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    bench_parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial epsilon")
    bench_parser.add_argument("--epsilon-decay", type=float, default=0.995, help="Epsilon decay rate")
    bench_parser.add_argument("--epsilon-min", type=float, default=0.01, help="Minimum epsilon")
    bench_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    bench_parser.add_argument("--save", type=str, default="trained_agent.json", help="Output file for trained agent")
    bench_parser.add_argument("--render-every", type=int, default=200, help="Render every N episodes")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "train":
        return cmd_train(args)
    elif args.command == "simulate":
        return cmd_simulate(args)
    elif args.command == "benchmark":
        return cmd_benchmark(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
