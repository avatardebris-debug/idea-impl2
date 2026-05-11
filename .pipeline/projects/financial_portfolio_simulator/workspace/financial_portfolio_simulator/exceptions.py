"""Custom exceptions for the Financial Portfolio Simulator."""


class SimulatorError(Exception):
    """Base exception for simulator-related errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class ModelError(SimulatorError):
    """Raised when a model encounters an error."""

    pass


class InvalidAssetError(SimulatorError):
    """Raised when an asset specification is invalid."""

    pass


class InvalidPortfolioError(SimulatorError):
    """Raised when a portfolio specification is invalid."""

    pass


class SimulationError(SimulatorError):
    """Raised when a simulation encounters an error."""

    pass


class StrategyError(SimulatorError):
    """Raised when a strategy encounters an error."""

    pass
