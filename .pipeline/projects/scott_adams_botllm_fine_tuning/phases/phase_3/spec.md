## Phase 3: Fine-Tuning Pipeline (Parallel Track)

**Description**: Build a fine-tuning pipeline to create a model that natively generates Scott Adams-style content. This is the higher-quality but higher-effort path.

**Deliverable**:
- Fine-tuning dataset: 1000+ instruction-tuning pairs (topic → Scott Adams-style text)
- LoRA fine-tuned model checkpoint (based on Llama 3 8B or Mistral 7B)
- Training pipeline scripts (data prep, training, evaluation)
- Model serving interface compatible with the `sacbot` package

**Dependencies**: Phase 1 (corpus), Phase 2 (evaluation framework)

**Success Criteria**:
- Fine-tuned model achieves ≥ 60% "possibly Scott Adams" in blind human evaluation (improvement over prompt-engineered baseline)
- Training completes on a single GPU (≤ 48 hours for LoRA on 8B model)
- Model generates coherent, on-topic content (≥ 90% coherence rating from 5+ raters)
- Fine-tuned model outperforms prompt-engineered version on automated style metrics

**Tasks**:
- [ ] Task 16: Instruction dataset creation — convert corpus to instruction-tuning pairs
- [ ] Task 17: Data augmentation — paraphrase, style transfer, synthetic examples
- [ ] Task 18: Model selection — evaluate Llama 3 8B vs Mistral 7B as base models
- [ ] Task 19: LoRA fine-tuning — configure and run training
- [ ] Task 20: Model evaluation — automated + human evaluation against baseline
- [ ] Task 21: Model serving — integrate fine-tuned model into `sacbot` package
- [ ] Task 22: Compare prompt vs fine-tuned — A/B evaluation report

---

