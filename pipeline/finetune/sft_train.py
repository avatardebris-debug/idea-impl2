#!/usr/bin/env python3
"""
pipeline/finetune/sft_train.py
SFT fine-tune on merged corpus JSONL with per-sample train_weight.

Requires optional deps (GPU recommended):
    pip install torch transformers datasets trl peft accelerate

Usage:
    # Inspect corpus + tier breakdown (no GPU)
    python -m pipeline.finetune.sft_train --dry-run

    # Export Alpaca "text" field for axolotl / LLaMA-Factory
    python -m pipeline.finetune.sft_train --export-formatted

    # Train with QLoRA (example — adjust model for your GPU)
    python -m pipeline.finetune.sft_train --train --model Qwen/Qwen2.5-Coder-1.5B-Instruct
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

from pipeline.finetune.corpus_dataset import (
    default_sft_path,
    load_weighted_sft_dataset,
    load_weighted_sft_records,
    sampler_weights_for_trainer,
)
from pipeline.finetune.formatting import record_to_text
from pipeline.finetune.weighted_trainer import validate_record_weights


def _tier_report(records: list[dict]) -> None:
    tiers = Counter(r.get("train_tier", "?") for r in records)
    total_w = sum(float(r.get("train_weight", 0)) for r in records)
    print(f"  Rows: {len(records)}")
    print(f"  Sum(train_weight): {total_w:.1f}")
    print("  By tier:", ", ".join(f"{k}={v}" for k, v in sorted(tiers.items())))


def cmd_dry_run(path: pathlib.Path, min_weight: float) -> None:
    records = load_weighted_sft_records(path, min_weight=min_weight)
    print(f"\nCorpus: {path}")
    _tier_report(records)
    if not records:
        print("  No records after filtering.")
        return
    validate_record_weights(records)
    w = sampler_weights_for_trainer(records)
    if w:
        print(f"  Weight range: {min(w):.3f} .. {max(w):.3f}")
    sample = records[0]
    print(f"  Sample id: {sample.get('id', '?')[:60]}")
    print(f"  Prompt chars: {len(record_to_text(sample))}")


def cmd_export_formatted(path: pathlib.Path, out: pathlib.Path, min_weight: float) -> pathlib.Path:
    records = load_weighted_sft_records(path, min_weight=min_weight)
    weights = validate_record_weights(records)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for rec, weight in zip(records, weights, strict=True):
            row = {
                "text": record_to_text(rec),
                "train_weight": float(weight),
                "train_tier": rec.get("train_tier"),
                "id": rec.get("id"),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} formatted rows -> {out}")
    return out


def cmd_train(
    path: pathlib.Path,
    *,
    model_name: str,
    output_dir: pathlib.Path,
    min_weight: float,
    max_steps: int,
    batch_size: int,
    learning_rate: float,
    max_seq_length: int,
    use_lora: bool,
) -> None:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import LoraConfig
        from trl import SFTConfig
    except ImportError as exc:
        print(
            "Missing training dependencies. Install:\n"
            "  pip install torch transformers datasets trl peft accelerate",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    from pipeline.finetune.weighted_trainer import WeightedSFTTrainer

    records = load_weighted_sft_records(path, min_weight=min_weight)
    if not records:
        print("No training records after min_weight filter.", file=sys.stderr)
        raise SystemExit(1)
    validate_record_weights(records)

    dataset = load_weighted_sft_dataset(path, min_weight=min_weight)

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict = {
        "trust_remote_code": True,
        "torch_dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    }
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)

    peft_config = None
    if use_lora:
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )

    def formatting_func(example):
        return record_to_text(example)

    training_args = SFTConfig(
        output_dir=str(output_dir),
        max_steps=max_steps,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        logging_steps=10,
        save_steps=max(max_steps // 2, 50),
        save_total_limit=2,
        bf16=torch.cuda.is_available(),
        report_to=[],
        max_length=max_seq_length,
        packing=False,
    )

    trainer = WeightedSFTTrainer.create(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        formatting_func=formatting_func,
        peft_config=peft_config,
    )

    print(f"Training {len(dataset)} samples (weighted sampler) -> {output_dir}")
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="SFT train on pipeline finetune corpus")
    mode = parser.add_mutually_exclusive_group()
    parser.add_argument("--corpus", type=pathlib.Path, default=None, help="sft JSONL path")
    parser.add_argument("--min-weight", type=float, default=0.0)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--export-formatted", metavar="PATH", nargs="?", const="auto")
    mode.add_argument("--train", action="store_true")
    parser.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("finetune_runs/sft_corpus"))
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-seq-length", type=int, default=4096)
    parser.add_argument("--no-lora", action="store_true", help="Full fine-tune (needs more VRAM)")
    args = parser.parse_args()

    corpus = args.corpus or default_sft_path(weighted=True)
    if not corpus.exists() and not args.corpus:
        corpus = default_sft_path(weighted=False)

    if args.dry_run:
        cmd_dry_run(corpus, args.min_weight)
        return

    if args.export_formatted is not None:
        out = (
            corpus.parent / "sft_task_formatted.jsonl"
            if args.export_formatted == "auto"
            else pathlib.Path(args.export_formatted)
        )
        cmd_export_formatted(corpus, out, args.min_weight)
        return

    if args.train:
        cmd_train(
            corpus,
            model_name=args.model,
            output_dir=args.output_dir,
            min_weight=args.min_weight,
            max_steps=args.max_steps,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_seq_length=args.max_seq_length,
            use_lora=not args.no_lora,
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
