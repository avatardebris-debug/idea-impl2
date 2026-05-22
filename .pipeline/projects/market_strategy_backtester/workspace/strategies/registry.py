"""Strategy registry and factory for creating strategies by name."""

from typing import Dict, Type, Any

from market_strategy_backtester.strategies.base import Strategy
from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.strategies.rsi_strategy import RSIStrategy
from market_strategy_backtester.strategies.macd_strategy import MACDStrategy
from market_strategy_backtester.strategies.bollinger_bands_strategy import BollingerBandsStrategy


# Registry mapping strategy names to their classes
STRATEGY_REGISTRY: Dict[str, Type[Strategy]] = {
    "sma_crossover": SMACrossoverStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger_bands": BollingerBandsStrategy,
}


def get_available_strategies() -> list[str]:
    """Return a list of available strategy names."""
    return list(STRATEGY_REGISTRY.keys())


def create_strategy(name: str, **params: Any) -> Strategy:
    """Create a strategy instance by name.

    Args:
        name: Strategy name (e.g., 'sma_crossover', 'rsi', 'macd', 'bollinger_bands').
        **params: Strategy-specific parameters.

    Returns:
        A Strategy instance.

    Raises:
        ValueError: If the strategy name is not registered.
    """
    if name not in STRATEGY_REGISTRY:
        available = ", ".join(get_available_strategies())
        raise ValueError(
            f"Unknown strategy '{name}'. Available strategies: {available}"
        )
    return STRATEGY_REGISTRY[name](**params)


def get_strategy_info(name: str) -> dict:
    """Get metadata about a registered strategy.

    Args:
        name: Strategy name.

    Returns:
        Dictionary with strategy metadata.

    Raises:
        ValueError: If the strategy name is not registered.
    """
    if name not in STRATEGY_REGISTRY:
        available = ", ".join(get_available_strategies())
        raise ValueError(
            f"Unknown strategy '{name}'. Available strategies: {available}"
        )

    cls = STRATEGY_REGISTRY[name]
    sig_params = {}
    for param_name, param in cls.__init__.__annotations__.items():
        if param_name == "return":
            continue
        default = cls.__init__.__defaults__[cls.__init__.__code__.co_varnames.index(param_name) - 1] \
            if param_name in cls.__init__.__code__.co_varnames and cls.__init__.__defaults__ \
            else None
        sig_params[param_name] = {"type": param.__name__ if hasattr(param, "__name__") else str(param)}

    return {
        "name": name,
        "class": cls.__name__,
        "description": cls.__doc__.strip().split("\n")[0] if cls.__doc__ else "",
        "parameters": sig_params,
    }
