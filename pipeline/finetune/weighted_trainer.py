"""SFTTrainer with WeightedRandomSampler from corpus train_weight."""

from __future__ import annotations

import math
from typing import Any


def _validate_weight_value(
    raw: Any,
    *,
    row_index: int,
    row_id: Any,
    weight_key: str,
) -> float:
    try:
        weight = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid {weight_key} at row={row_index} id={row_id!r}: {raw!r}"
        ) from exc
    if not math.isfinite(weight) or weight < 0:
        raise ValueError(
            f"Invalid {weight_key} at row={row_index} id={row_id!r}: {raw!r}"
        )
    return weight


def validate_record_weights(
    records: list[dict[str, Any]],
    weight_key: str = "train_weight",
) -> list[float]:
    """Validate record weights with explicit row/id context.

    Zero is accepted for legacy data, but sampler code clamps it to a tiny
    positive value so `WeightedRandomSampler` can operate reliably.
    """
    validated: list[float] = []
    for i, rec in enumerate(records):
        validated.append(
            _validate_weight_value(
                rec.get(weight_key),
                row_index=i,
                row_id=rec.get("id", "?"),
                weight_key=weight_key,
            )
        )
    return validated


def build_weighted_sampler(dataset: Any, weight_column: str = "train_weight"):
    import torch
    from torch.utils.data import WeightedRandomSampler

    weights: list[float] = []
    for i in range(len(dataset)):
        rec = dataset[i]
        validated = _validate_weight_value(
            rec.get(weight_column),
            row_index=i,
            row_id=rec.get("id", "?"),
            weight_key=weight_column,
        )
        weights.append(max(validated, 1e-6))
    w_tensor = torch.tensor(weights, dtype=torch.double)
    return WeightedRandomSampler(
        w_tensor,
        num_samples=len(weights),
        replacement=True,
    )


class WeightedSFTTrainer:
    """Lazy wrapper: real class created when trl is installed."""

    @classmethod
    def create(cls, *args, dataset_weights_column: str = "train_weight", **kwargs):
        from trl import SFTTrainer

        class _WeightedSFTTrainer(SFTTrainer):
            def _get_train_sampler(self, train_dataset=None):
                ds = train_dataset if train_dataset is not None else self.train_dataset
                if ds is not None and dataset_weights_column in ds.column_names:
                    return build_weighted_sampler(ds, dataset_weights_column)
                return super()._get_train_sampler(train_dataset)

        return _WeightedSFTTrainer(*args, **kwargs)
