"""Chronovision CLI — command-line interface."""

import argparse
import json
import logging
import sys
from typing import Optional

from chronovision.src.orchestrator.runner import Runner


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_pipeline(args: argparse.Namespace) -> None:
    """Run the full Chronovision pipeline."""
    setup_logging(args.verbose)
    logger = logging.getLogger("chronovision")
    
    runner = Runner(db_url=args.db_url)
    
    tickers = args.tickers if args.tickers else None
    
    logger.info("Building Chronovision workflow...")
    workflow = runner.build_workflow(tickers)
    
    logger.info("Running Chronovision pipeline...")
    results = runner.run(tickers)
    
    if results.get("status") == "completed":
        logger.info("Pipeline completed successfully!")
        
        # Print summary
        world_state = runner.get_world_state()
        logger.info(f"World state: {json.dumps(world_state, indent=2)}")
        
        predictions = runner.get_predictions()
        if predictions:
            logger.info(f"Predictions: {json.dumps(predictions, indent=2)}")
    else:
        logger.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)


def run_prediction(args: argparse.Namespace) -> None:
    """Run a single prediction."""
    setup_logging(args.verbose)
    logger = logging.getLogger("chronovision")
    
    runner = Runner(db_url=args.db_url)
    
    # Build and run up to prediction step
    workflow = runner.build_workflow([args.ticker])
    
    # Run only up to prediction
    for step in workflow.steps[:4]:  # Up to train_predictor
        logger.info(f"Running step: {step.name}")
        step.result = step.func(*step.args, **step.kwargs)
        step.status = "completed"
        workflow.context[step.name] = step.result
    
    # Run prediction
    predictions = runner._run_predictions([args.ticker])
    
    if predictions:
        ticker_pred = predictions["predictions"].get(args.ticker, {})
        logger.info(f"Prediction for {args.ticker}: {json.dumps(ticker_pred, indent=2)}")
    else:
        logger.error("No predictions available")
        sys.exit(1)


def run_status(args: argparse.Namespace) -> None:
    """Get pipeline status."""
    setup_logging(args.verbose)
    logger = logging.getLogger("chronovision")
    
    runner = Runner(db_url=args.db_url)
    state = runner.get_world_state()
    logger.info(f"World state: {json.dumps(state, indent=2)}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Chronovision — Financial World Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m chronovision run --tickers AAPL MSFT GOOGL
  python -m chronovision predict --ticker AAPL
  python -m chronovision status
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the full pipeline")
    run_parser.add_argument("--tickers", nargs="+", help="Tickers to process")
    run_parser.add_argument("--db-url", help="Database URL")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Run a single prediction")
    predict_parser.add_argument("--ticker", required=True, help="Ticker to predict")
    predict_parser.add_argument("--db-url", help="Database URL")
    predict_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get pipeline status")
    status_parser.add_argument("--db-url", help="Database URL")
    status_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_pipeline(args)
    elif args.command == "predict":
        run_prediction(args)
    elif args.command == "status":
        run_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
