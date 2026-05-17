# Runbook: RL Dropshipping System

## Overview

This runbook covers operational procedures for the RL dropshipping system,
including shadow mode, rollout, calibration, monitoring, and feedback loops.

## Table of Contents

1. [Shadow Mode](#shadow-mode)
2. [Rollout Pipeline](#rollout-pipeline)
3. [Calibration](#calibration)
4. [Monitoring & Kill Switch](#monitoring--kill-switch)
5. [Feedback Loop](#feedback-loop)
6. [Emergency Procedures](#emergency-procedures)
7. [Maintenance](#maintenance)

---

## Shadow Mode

### Starting Shadow Mode

```python
from rl_dropshipping.src.shadow import ShadowMode

shadow = ShadowMode(
    agent=agent,
    environment=env,
    evaluation_interval=3600,  # 1 hour
    min_samples=1000,
)
shadow.start()
```

### Monitoring Shadow Mode

- Check evaluation metrics every hour
- Compare RL vs. baseline performance
- Log all predictions for audit

### Stopping Shadow Mode

```python
shadow.stop()
```

---

## Rollout Pipeline

### Creating a Rollout

```python
from rl_dropshipping.src.rollout import RolloutPipeline

pipeline = RolloutPipeline(name="product_recommendation")

# Add phases
pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
pipeline.add_phase("phase_2", "Beta", traffic_fraction=0.1)
pipeline.add_phase("phase_3", "Full", traffic_fraction=1.0)

# Activate phases sequentially
pipeline.activate_phase("phase_1", traffic_fraction=0.01)
# Wait for evaluation...
pipeline.complete_phase("phase_1")
pipeline.activate_phase("phase_2", traffic_fraction=0.1)
# ...
```

### Rollback

```python
pipeline.rollback_phase("phase_2")
```

---

## Calibration

### Using the Calibration Layer

```python
from rl_dropshipping.src.calibration import CalibrationLayer

calibrator = CalibrationLayer(calibration_window=1000)

# Add samples during shadow mode
calibrator.add_sample(score=0.85, label=1)
calibrator.add_sample(score=0.32, label=0)

# Calibrate predictions
raw_score = 0.75
calibrated_score = calibrator.calibrate(raw_score)
```

### Temperature Scaling

```python
scaled_score = calibrator.apply_temperature(raw_score, temperature=1.5)
```

---

## Monitoring & Kill Switch

### Setting Up Monitoring

```python
from rl_dropshipping.src.monitoring import MonitoringDashboard

dashboard = MonitoringDashboard()

# Register metrics
dashboard.register_metric("prediction_latency", window_seconds=3600)
dashboard.register_metric("reward", window_seconds=3600)

# Set thresholds
dashboard.set_threshold("prediction_latency", upper=0.5)  # 500ms
dashboard.set_threshold("reward", lower=-10.0)

# Record metrics
dashboard.record_metric("prediction_latency", 0.23)
dashboard.record_metric("reward", 5.6)
```

### Kill Switch

```python
# Trigger manually
dashboard.trigger_kill_switch("Abnormal reward pattern detected")

# Check status
if dashboard.kill_switch.is_active:
    logger.critical("Kill switch is active! System halted.")

# Reset (requires human confirmation)
dashboard.reset_kill_switch()
```

---

## Feedback Loop

### Collecting Feedback

```python
from rl_dropshipping.src.feedback import FeedbackCollector

collector = FeedbackCollector(max_samples=100000)

# After each action
collector.add_sample(
    state=current_state,
    action=chosen_action,
    reward=observed_reward,
    next_state=next_state,
    done=episode_done,
)
```

### Processing Feedback

```python
from rl_dropshipping.src.feedback import FeedbackProcessor

processor = FeedbackProcessor()

# Process and retrain
stats = processor.process_and_train(
    collector=collector,
    agent=agent,
    n_samples=1000,
)
```

---

## Emergency Procedures

### Kill Switch Activation

1. **Automatic**: System triggers kill switch when thresholds are violated
2. **Manual**: Operator calls `dashboard.trigger_kill_switch(reason)`

### Post-Incident

1. Review kill switch history: `dashboard.kill_switch.get_status()`
2. Analyze alerts: `dashboard.get_alerts(level=AlertLevel.CRITICAL)`
3. Reset kill switch only after human confirmation
4. Document incident and update thresholds if needed

---

## Maintenance

### Daily Checks

- [ ] Review monitoring dashboard
- [ ] Check for critical alerts
- [ ] Verify kill switch status
- [ ] Review shadow mode metrics

### Weekly Tasks

- [ ] Analyze feedback statistics
- [ ] Review calibration quality
- [ ] Check rollout phase progress
- [ ] Update thresholds if needed

### Monthly Tasks

- [ ] Full system health check
- [ ] Review and update runbook
- [ ] Performance benchmarking
- [ ] Security audit
