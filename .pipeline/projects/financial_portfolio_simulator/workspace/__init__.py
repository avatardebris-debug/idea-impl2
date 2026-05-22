"""Financial Portfolio Simulator — Monte Carlo risk analysis for stock and crypto portfolios."""

__version__ = "0.1.0"

from financial_portfolio_simulator.api import run_simulation
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.models.portfolio import Portfolio
from financial_portfolio_simulator.models.position import Position
from financial_portfolio_simulator.simulators.gbm import GBM
from financial_portfolio_simulator.simulators.market_simulator import MarketSimulator
from financial_portfolio_simulator.simulators.portfolio_simulator import PortfolioSimulator, SimulationResult
from financial_portfolio_simulator.strategies.base import Strategy
from financial_portfolio_simulator.strategies.buy_and_hold import BuyAndHold
from financial_portfolio_simulator.exceptions import (
    InvalidAssetError,
    InvalidPortfolioError,
    SimulationError,
    StrategyError,
    SimulatorError,
)

__all__ = [
    "run_simulation",
    "Asset",
    "Portfolio",
    "Position",
    "GBM",
    "MarketSimulator",
    "PortfolioSimulator",
    "SimulationResult",
    "Strategy",
    "BuyAndHold",
    "SimulatorError",
    "InvalidAssetError",
    "InvalidPortfolioError",
    "SimulationError",
    "StrategyError",
]
