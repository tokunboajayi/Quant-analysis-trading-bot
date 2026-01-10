from typing import Dict, List
from riskfusion.utils.logging import get_logger

logger = get_logger("gates")

class GateError(Exception):
    pass

class QualityGates:
    """
    Defines thresholds for model promotion.
    """
    
    @staticmethod
    def check_candidate_gates(metrics: Dict[str, float]):
        """
        Gates for Candidate -> Staging.
        """
        THRESHOLD_IC = 0.01
        
        if 'mean_ic' not in metrics:
            logger.warning("No 'mean_ic' metric found. Skipping IC check.")
        elif metrics['mean_ic'] < THRESHOLD_IC:
            raise GateError(f"Mean IC {metrics['mean_ic']:.4f} < {THRESHOLD_IC}")
            
        # Add more...
        logger.info("Candidate Gates Passed.")
        return True

    @staticmethod
    def check_production_gates(metrics: Dict[str, float], validation_report: Dict = None):
        """
        Gates for Staging -> Prod.
        Stricter.
        """
        THRESHOLD_IC = 0.015
        
        if metrics.get('mean_ic', 0) < THRESHOLD_IC:
            raise GateError(f"Mean IC {metrics.get('mean_ic'):.4f} < {THRESHOLD_IC}")
            
        logger.info("Production Gates Passed.")
        return True
