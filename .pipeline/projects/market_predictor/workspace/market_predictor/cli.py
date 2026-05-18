"""
cli.py — market_predictor CLI.
"""
import argparse, json, pathlib, sys
from market_predictor.predictor import forecast_asset, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="market_predictor")
    parser.add_argument("command", choices=["forecast"])
    parser.add_argument("ticker", help="Asset ticker symbol (e.g. AAPL, BTC-USD)")
    parser.add_argument("--days", type=int, default=30, help="Lookback days (default: 30)")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    print(f"Generating forecast for {args.ticker}...", file=sys.stderr)
    data = forecast_asset(args.ticker, days=args.days, model=args.model)

    out_str = json.dumps(data, indent=2) if args.format == "json" else format_markdown(data)

    if args.output:
        p = pathlib.Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out_str, encoding="utf-8")
        print(f"Saved to {p}", file=sys.stderr)
    else:
        print(out_str)

if __name__ == "__main__":
    main()
