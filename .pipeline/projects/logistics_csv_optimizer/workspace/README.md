# Logistics CSV Optimizer

A command-line tool and Python API for importing logistics shipment manifests, calculating routing costs, and generating optimized delivery schedules.

## Installation

```bash
pip install .
```

## CLI Usage

### Basic Usage
```bash
logistics-csv-optimizer -i manifest.csv -o output.json
```

### Advanced Usage (Piping)
The tool supports reading from stdin and writing to stdout using `-`.

```bash
cat manifest.csv | logistics-csv-optimizer -i - -o - > output.json
```

## API Usage

The core engine can be integrated into existing Python pipelines.

```python
from logistics_csv_optimizer.api import run_optimization

# Run optimization pipeline directly
result = run_optimization("manifest.csv")

print(f"Total Cost: {result['total_cost']}")
print(f"Number of Scheduled Shipments: {len(result['schedule'])}")
```

## Docker Container

### Build Image
```bash
docker build -t logistics-csv-optimizer .
```

### Run Container
```bash
docker run --rm -v $(pwd):/data logistics-csv-optimizer -i /data/manifest.csv -o /data/output.json
```
