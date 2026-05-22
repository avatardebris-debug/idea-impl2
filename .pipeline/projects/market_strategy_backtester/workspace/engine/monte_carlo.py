"""Monte Carlo simulator for equity curve uncertainty.

Supports bootstrap resampling (default) and parametric (normal distribution) methods.
"""

import numpy as np
import pandas as pd


class MonteCarloSimulator:
    """Monte Carlo simulator that generates alternative equity curves.

    Attributes:
        n_simulations: Number of simulations to run (default: 1000).
        seed: Random seed for reproducibility (default: 42).
        method: MC method — "bootstrap" or "parametric" (default: "bootstrap").
    """

    def __init__(
        self,
        n_simulations: int = 1000,
        seed: int = 42,
        method: str = "bootstrap",
    ):
        self.n_simulations = n_simulations
        self.seed = seed
        self.method = method

    def run(
        self,
        per_trade_returns: pd.Series,
        base_equity_curve: pd.Series,
    ) -> pd.DataFrame:
        """Run Monte Carlo simulations.

        Args:
            per_trade_returns: Series of per-trade returns from the backtest.
            base_equity_curve: Original equity curve (used for bootstrap reference).

        Returns:
            DataFrame with columns sim_0, sim_1, ... each containing an equity curve.
        """
        rng = np.random.default_rng(self.seed)
        n_trades = len(per_trade_returns)
        n_equity_points = len(base_equity_curve)

        if self.method == "bootstrap":
            simulation_curves = self._bootstrap_simulate(rng, per_trade_returns, n_equity_points)
        elif self.method == "parametric":
            simulation_curves = self._parametric_simulate(rng, per_trade_returns, n_equity_points)
        else:
            raise ValueError(f"Unknown MC method: {self.method}")

        return simulation_curves

    def _bootstrap_simulate(
        self,
        rng: np.random.Generator,
        returns: pd.Series,
        n_trades: int,
    ) -> pd.DataFrame:
        """Bootstrap resampling: resample returns with replacement."""
        n = len(returns)
        curves = np.zeros((self.n_simulations, n_trades))

        for i in range(self.n_simulations):
            # Resample with replacement
            sampled = rng.choice(returns, size=n_trades, replace=True)
            curves[i] = (1 + sampled).cumprod()

        return pd.DataFrame(curves.T, columns=[f"sim_{i}" for i in range(self.n_simulations)])

    def _parametric_simulate(
        self,
        rng: np.random.Generator,
        returns: pd.Series,
        n_trades: int,
    ) -> pd.DataFrame:
        """Parametric simulation: assume normal distribution fitted to returns."""
        mean = returns.mean()
        std = returns.std()

        if std == 0:
            # If no variance, all simulations are the same
            curves = np.ones((self.n_simulations, n_trades))
            for i in range(self.n_simulations):
                curves[i] = (1 + mean) ** np.arange(1, n_trades + 1)
            return pd.DataFrame(curves, columns=[f"sim_{i}" for i in range(self.n_simulations)])

        simulated_returns = rng.normal(loc=mean, scale=std, size=(self.n_simulations, n_trades))
        curves = (1 + simulated_returns).cumprod(axis=1)

        return pd.DataFrame(curves, columns=[f"sim_{i}" for i in range(self.n_simulations)])
