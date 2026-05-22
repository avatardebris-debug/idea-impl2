import os
from typing import Dict, Any, List

from logistics_csv_optimizer.importer import Importer
from logistics_csv_optimizer.calculator import CostCalculator
from logistics_csv_optimizer.scheduler import ScheduleGenerator

def run_optimization(input_source: str) -> Dict[str, Any]:
    """Run the logistics optimization pipeline.
    
    Args:
        input_source: Path to the CSV file or '-' for stdin.
        
    Returns:
        A dictionary containing costed shipments, total cost, and generated schedule.
    """
    # Import
    shipments = Importer.import_csv(input_source)
    
    # Cost calculation
    costed_shipments = CostCalculator.calculate_costs(shipments)
    total = CostCalculator.total_cost(costed_shipments)
    
    # Schedule generation
    schedule = ScheduleGenerator.generate(costed_shipments)
    
    return {
        "shipments": costed_shipments,
        "total_cost": total,
        "schedule": schedule,
    }
