"""Visualization utilities for the GridWorld agent system."""

from __future__ import annotations

from typing import Optional

import numpy as np

from gameagent.agent import BaseAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import Action


def plot_training_curves(
    rewards: list[float],
    steps: list[int],
    save_path: Optional[str] = None,
    title: str = "Training Curves"
) -> None:
    """Plot training curves for rewards and steps.

    Args:
        rewards: List of rewards per episode.
        steps: List of steps per episode.
        save_path: Optional path to save the plot.
        title: Title for the plot.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['Arial']
    except ImportError:
        print("matplotlib not available. Install with: pip install matplotlib")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Plot rewards
    ax1.plot(rewards, label='Reward', color='blue', linewidth=1.5)
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Reward')
    ax1.set_title('Rewards Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot steps
    ax2.plot(steps, label='Steps', color='green', linewidth=1.5)
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Steps')
    ax2.set_title('Steps Per Episode')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    else:
        plt.show()


def render_grid(
    env: GridWorld,
    agent: Optional[BaseAgent] = None,
    title: Optional[str] = None
) -> None:
    """Render the current grid state.

    Args:
        env: GridWorld environment.
        agent: Optional agent to show policy.
        title: Optional plot title.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib import rcParams
        rcParams['font.family'] = 'sans-serif'
        rcParams['font.sans-serif'] = ['Arial']
    except ImportError:
        print("matplotlib not available. Install with: pip install matplotlib")
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title(title or "GridWorld State", fontsize=14, fontweight='bold')
    ax.set_xlim(0, env.config.width)
    ax.set_ylim(env.config.height, 0)
    ax.set_aspect('equal')
    ax.axis('off')

    # Draw grid
    for i in range(env.config.width + 1):
        ax.axhline(i, color='gray', linewidth=0.5)
        ax.axvline(i, color='gray', linewidth=0.5)

    # Draw cells
    cell_width = 1.0 / env.config.width
    cell_height = 1.0 / env.config.height

    for row in range(env.config.height):
        for col in range(env.config.width):
            x = col * cell_width
            y = row * cell_height

            # Determine cell color based on content
            if (row, col) == env.config.goal_position:
                color = 'lightgreen'
            elif (row, col) in env.config.obstacles:
                color = 'lightcoral'
            elif (row, col) == env.agent_position:
                color = 'lightblue'
            else:
                color = 'white'

            rect = plt.Rectangle(
                (x, y), cell_width, cell_height,
                facecolor=color, edgecolor='black', linewidth=1
            )
            ax.add_patch(rect)

            # Add labels
            if (row, col) == env.config.goal_position:
                ax.text(
                    x + cell_width/2, y + cell_height/2,
                    'G', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black'
                )
            elif (row, col) in env.config.obstacles:
                ax.text(
                    x + cell_width/2, y + cell_height/2,
                    'X', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black'
                )
            elif (row, col) == env.agent_position:
                ax.text(
                    x + cell_width/2, y + cell_height/2,
                    'A', ha='center', va='center',
                    fontsize=12, fontweight='bold', color='black'
                )

    # Add agent position if agent is provided
    if agent is not None and isinstance(agent, BaseAgent):
        try:
            import matplotlib.patches as mpatches
            legend_elements = [
                mpatches.Patch(color='lightgreen', label='Goal'),
                mpatches.Patch(color='lightcoral', label='Obstacle'),
                mpatches.Patch(color='lightblue', label='Agent'),
            ]
            ax.legend(handles=legend_elements, loc='upper right')
        except Exception:
            pass

    plt.tight_layout()
    plt.show()
