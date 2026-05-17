"""Shadow predictor — logs predictions without executing real actions."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """A single shadow-mode prediction."""
    timestamp: float
    action_type: str  # e.g., "product_selection", "pricing", "ad_budget"
    prediction: Dict[str, Any]
    confidence: float
    channel: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "channel": self.channel,
        }


class ShadowPredictor:
    """Makes predictions in shadow mode — logs without executing.

    The predictor logs every prediction with a timestamp and can be
    configured to run alongside any existing agent (rule-based or RL)
    without interfering with real decisions.
    """

    def __init__(
        self,
        enabled: bool = True,
        log_dir: Optional[str] = None,
    ):
        self.enabled = enabled
        self.log_dir = log_dir
        self._predictions: List[Prediction] = []

    def predict(
        self,
        action_type: str,
        prediction: Dict[str, Any],
        confidence: float = 0.5,
        channel: str = "",
    ) -> Prediction:
        """Log a prediction without executing any real action.

        Args:
            action_type: Type of prediction (e.g., "product_selection").
            prediction: The predicted values.
            confidence: Confidence score in [0, 1].
            channel: Channel identifier (e.g., "facebook", "google").

        Returns:
            The logged Prediction object.
        """
        if not self.enabled:
            return Prediction(
                timestamp=time.time(),
                action_type=action_type,
                prediction=prediction,
                confidence=confidence,
                channel=channel,
            )

        pred = Prediction(
            timestamp=time.time(),
            action_type=action_type,
            prediction=prediction,
            confidence=max(0.0, min(1.0, confidence)),
            channel=channel,
        )
        self._predictions.append(pred)
        logger.debug(
            f"Shadow prediction logged: type={action_type}, "
            f"confidence={confidence:.3f}, channel={channel}"
        )
        return pred

    def get_predictions(
        self,
        action_type: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[Prediction]:
        """Retrieve logged predictions, optionally filtered.

        Args:
            action_type: Filter by action type.
            since: Filter by timestamp (epoch seconds).

        Returns:
            List of matching predictions.
        """
        results = self._predictions
        if action_type is not None:
            results = [p for p in results if p.action_type == action_type]
        if since is not None:
            results = [p for p in results if p.timestamp >= since]
        return results

    def clear(self) -> None:
        """Clear all logged predictions."""
        self._predictions.clear()
        logger.debug("Shadow predictions cleared")

    @property
    def prediction_count(self) -> int:
        """Total number of logged predictions."""
        return len(self._predictions)
