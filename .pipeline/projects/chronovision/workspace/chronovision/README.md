# Chronovision — Financial World Model

A dynamic state-space representation of the financial world that propagates states through a graph of entities and uses ML to predict future movements.

## Architecture

```
chronovision/
├── src/
│   ├── data/          # Data loading and SEC filing import
│   ├── model/         # Entity, StateSpace, GraphBuilder, Updater
│   ├── predictor/     # LSTM, Ensemble predictors
│   ├── orchestrator/  # Workflow and Runner
│   └── cli.py         # Command-line interface
├── tests/             # Test suite
├── requirements.txt   # Dependencies
└── README.md          # This file
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the full pipeline

```bash
python -m chronovision run --tickers AAPL MSFT GOOGL
```

### Run a single prediction

```bash
python -m chronovision predict --ticker AAPL
```

### Get pipeline status

```bash
python -m chronovision status
```

## Features

- **Dynamic State-Space**: Real-time representation of financial entities
- **Graph-Based Propagation**: States propagate through entity relationships
- **ML Predictions**: LSTM-based predictions with ensemble methods
- **SEC Filing Integration**: Import and analyze SEC filings
- **CLI Interface**: Easy command-line access

## Testing

```bash
pytest
```

## License

MIT
