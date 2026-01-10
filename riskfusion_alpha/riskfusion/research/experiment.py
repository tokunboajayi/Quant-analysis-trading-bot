import json
import shutil
from pathlib import Path
from datetime import datetime
import uuid
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("experiment")

class ExperimentTracker:
    def __init__(self, exp_name=None):
        self.config = get_config()
        self.root = Path(self.config.params['paths']['raw']).parent / "experiments"
        self.root.mkdir(parents=True, exist_ok=True)
        
        # ID: YYYYMMDD_HHMMSS_<short_uuid>
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.id = f"{ts}_{str(uuid.uuid4())[:6]}"
        if exp_name:
            self.id = f"{ts}_{exp_name}_{str(uuid.uuid4())[:4]}"
            
        self.exp_dir = self.root / self.id
        self.exp_dir.mkdir()
        (self.exp_dir / "artifacts").mkdir()
        
        self.metrics = {}
        self.params = {}
        
    def log_params(self, params: dict):
        self.params.update(params)
        self._save_json("params.json", self.params)
        
    def log_metrics(self, metrics: dict):
        self.metrics.update(metrics)
        self._save_json("metrics.json", self.metrics)
        
    def log_artifact(self, path: str):
        src = Path(path)
        if src.exists():
            dst = self.exp_dir / "artifacts" / src.name
            shutil.copy(src, dst)
            
    def _save_json(self, filename, data):
        with open(self.exp_dir / filename, "w") as f:
            json.dump(data, f, indent=2)
            
    def end(self):
        logger.info(f"Experiment {self.id} finished. Metrics: {self.metrics}")
