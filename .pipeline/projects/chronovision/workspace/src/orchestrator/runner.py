"""Runner — executes the Chronovision workflow."""

import logging
from typing import Dict, Any, List, Optional

from chronovision.src.orchestrator.workflow import Workflow, WorkflowStatus
from chronovision.src.data.loader import DataLoader
from chronovision.src.data.sec_importer import SECImporter
from chronovision.src.model.state_space import StateSpace
from chronovision.src.model.graph_builder import GraphBuilder
from chronovision.src.model.updater import Updater
from chronovision.src.predictor.ensemble_predictor import EnsemblePredictor
from chronovision.src.predictor.lstm_predictor import LSTMPredictor

logger = logging.getLogger(__name__)


class Runner:
    """Executes the Chronovision workflow."""
    
    def __init__(self, db_url: Optional[str] = None):
        self.data_loader = DataLoader(db_url)
        self.sec_importer = SECImporter(db_url)
        self.state_space = StateSpace()
        self.graph_builder = GraphBuilder(self.data_loader)
        self.updater = Updater(self.data_loader, self.sec_importer)
        self.predictor = EnsemblePredictor()
        self.workflow: Optional[Workflow] = None
    
    def build_workflow(self, tickers: List[str] = None) -> Workflow:
        """Build the Chronovision workflow."""
        self.workflow = Workflow(
            name="Chronovision",
            description="Financial world model pipeline"
        )
        
        # Step 1: Import data
        self.workflow.add_step(
            "import_data",
            self.sec_importer.import_all_data,
            tickers
        )
        
        # Step 2: Build state space
        self.workflow.add_step(
            "build_state_space",
            self.graph_builder.build_from_companies,
            self.state_space,
            tickers
        )
        
        # Step 3: Prepare training data
        self.workflow.add_step(
            "prepare_training_data",
            self._prepare_training_data,
            tickers
        )
        
        # Step 4: Train predictor
        self.workflow.add_step(
            "train_predictor",
            self._train_predictor
        )
        
        # Step 5: Run predictions
        self.workflow.add_step(
            "run_predictions",
            self._run_predictions,
            tickers
        )
        
        # Step 6: Update state space
        self.workflow.add_step(
            "update_state_space",
            self.updater.update_with_new_prices,
            self.state_space,
            tickers
        )
        
        # Step 7: Propagate and predict
        self.workflow.add_step(
            "propagate_and_predict",
            self.updater.propagate_and_predict,
            self.state_space,
            1
        )
        
        return self.workflow
    
    def run(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Run the full Chronovision workflow."""
        if self.workflow is None:
            self.build_workflow(tickers)
        
        results = self.workflow.run()
        return results
    
    def _prepare_training_data(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Prepare training data for the predictor."""
        if tickers is None:
            tickers = self.data_loader.get_all_tickers()
        
        X_list = []
        y_list = []
        
        for ticker in tickers:
            dataset = self.data_loader.get_prediction_dataset(ticker, lookback=60, horizon=1)
            if dataset["X"].size > 0:
                X_list.append(dataset["X"])
                y_list.append(dataset["y"])
        
        if not X_list:
            return {"X": None, "y": None, "error": "No training data available"}
        
        X = np.vstack(X_list)
        y = np.concatenate(y_list)
        
        return {"X": X, "y": y, "tickers": tickers}
    
    def _train_predictor(self) -> Dict[str, Any]:
        """Train the predictor."""
        if "prepare_training_data" not in self.workflow.context:
            return {"error": "Training data not prepared"}
        
        data = self.workflow.context["prepare_training_data"]
        if data.get("X") is None:
            return {"error": "No training data"}
        
        X = data["X"]
        y = data["y"]
        feature_names = ["price", "volume", "market_cap", "pe_ratio", "eps",
                        "revenue", "net_income", "debt_to_equity", "roe", "beta",
                        "momentum_5d", "momentum_20d", "volatility_20d", "rsi"]
        
        # Create LSTM predictor
        lstm = LSTMPredictor(hidden_dim=64, epochs=50, lr=0.01)
        lstm.train(X, y, feature_names)
        
        # Add to ensemble
        self.predictor.add_predictor(lstm, weight=1.0)
        self.predictor.train(X, y, feature_names)
        
        metrics = self.predictor.evaluate(X, y)
        return {"metrics": metrics, "predictor": self.predictor}
    
    def _run_predictions(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Run predictions for all tickers."""
        if tickers is None:
            tickers = self.data_loader.get_all_tickers()
        
        predictions = {}
        for ticker in tickers:
            entity = self.state_space.get_entity(ticker)
            if entity:
                features = np.array(entity.to_feature_vector()).reshape(1, -1)
                pred = self.predictor.predict_direction(features)
                predictions[ticker] = {
                    "direction": int(pred[0]),
                    "confidence": float(np.max(self.predictor.predict(features))),
                }
        
        return {"predictions": predictions}
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get the current world state."""
        return self.state_space.get_world_state()
    
    def get_predictions(self) -> Dict[str, Any]:
        """Get the latest predictions."""
        if self.workflow and "run_predictions" in self.workflow.context:
            return self.workflow.context["run_predictions"]
        return {}
