"""Dashboard panels."""

from src.dashboard.tickers import DashboardTicker


class DashboardPanel:
    """Base panel class."""

    def __init__(self):
        self._ticker = None

    def bind_ticker(self, ticker: DashboardTicker):
        self._ticker = ticker

    def update_from_bound_ticker(self):
        if self._ticker is not None:
            self.update(self._ticker)

    def update(self, ticker: DashboardTicker):
        pass

    def render_data(self) -> dict:
        return {}

    def get_visual_encoding(self) -> dict:
        return {}


class WinRatePanel(DashboardPanel):
    """Win rate gauge panel."""

    def __init__(self):
        super().__init__()
        self.gauge_value = 0.0

    def update(self, ticker: DashboardTicker):
        self.gauge_value = ticker.current_win_rate.value

    def render_data(self) -> dict:
        return {"gauge_value": self.gauge_value}

    def get_visual_encoding(self) -> dict:
        return {"type": "gauge", "value": self.gauge_value}


class BankrollCurvePanel(DashboardPanel):
    """Bankroll curve panel."""

    def __init__(self):
        super().__init__()
        self.bankroll = 0.0
        self.peak_bankroll = 0.0
        self.drawdown = 0.0
        self.history = []

    def update(self, ticker: DashboardTicker):
        self.bankroll = ticker.bankroll_history.bankroll
        self.peak_bankroll = ticker.bankroll_history.peak_bankroll
        self.drawdown = ticker.bankroll_history.drawdown
        self.history = ticker.bankroll_history.history

    def render_data(self) -> dict:
        return {
            "bankroll": self.bankroll,
            "peak_bankroll": self.peak_bankroll,
            "drawdown": self.drawdown,
            "history": self.history,
        }

    def get_visual_encoding(self) -> dict:
        return {"type": "curve", "bankroll": self.bankroll}


class NashEquilibriumPanel(DashboardPanel):
    """Nash equilibrium distance panel."""

    def __init__(self):
        super().__init__()
        self.distance = 0.0
        self.current_strategy = "unknown"
        self.nash_strategy = "nash_equilibrium"

    def update(self, ticker: DashboardTicker):
        self.distance = ticker.nash_distance.distance
        self.current_strategy = ticker.nash_distance.current_strategy
        self.nash_strategy = ticker.nash_distance.nash_strategy

    def render_data(self) -> dict:
        return {
            "distance": self.distance,
            "current_strategy": self.current_strategy,
            "nash_strategy": self.nash_strategy,
        }

    def get_visual_encoding(self) -> dict:
        return {"type": "distance", "distance": self.distance}
