"""SFTTrainer with WeightedRandomSampler from corpus train_weight."""

from __future__ import annotations

from typing import Any


def build_weighted_sampler(dataset: Any, weight_column: str = "train_weight"):
    import torch
    from torch.utils.data import WeightedRandomSampler

    weights = [
        max(float(dataset[i][weight_column]), 1e-6)
        for i in range(len(dataset))
    ]
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
