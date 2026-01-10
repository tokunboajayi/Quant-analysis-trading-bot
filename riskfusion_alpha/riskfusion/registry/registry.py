import shutil
import json
import os
from pathlib import Path
from typing import Literal
from datetime import datetime
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("registry")

STAGES = ["candidates", "staging", "prod"]

class ModelRegistry:
    def __init__(self):
        self.config = get_config()
        self.root = Path(self.config.params['paths']['raw']).parent / "registry"
        for s in STAGES:
            (self.root / s).mkdir(parents=True, exist_ok=True)
            
    def list_models(self, stage: str = "candidates"):
        if stage not in STAGES:
            raise ValueError(f"Invalid stage: {stage}")
        
        stage_dir = self.root / stage
        models = []
        for d in stage_dir.iterdir():
            if d.is_dir() and (d / "model_card.md").exists():
                models.append(d.name)
        return sorted(models)

    def register_candidate(self, model_artifact_path: str, metrics: dict, config: dict, description: str):
        """
        Register a new trained model as a candidate.
        """
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_dir = self.root / "candidates" / model_id
        target_dir.mkdir()
        
        # 1. Copy Model
        src = Path(model_artifact_path)
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy(src, target_dir / src.name)
        
        # 2. Metadata (simulating Model Card)
        with open(target_dir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        with open(target_dir / "config.yaml", "w") as f:
            # Dump config dict
            import yaml
            yaml.dump(config, f)
            
        with open(target_dir / "model_card.md", "w") as f:
            f.write(f"# Model Card: {model_id}\n\n")
            f.write(f"**Created**: {datetime.now().isoformat()}\n")
            f.write(f"**Description**: {description}\n")
            f.write(f"**Metrics**: {metrics}\n")
            
        logger.info(f"Registered candidate: {model_id}")
        return model_id

    def promote(self, model_id: str, from_stage: str, to_stage: str):
        """
        Promote a model from one stage to another.
        """
        if from_stage not in STAGES or to_stage not in STAGES:
            raise ValueError("Invalid stages")
            
        src_dir = self.root / from_stage / model_id
        if not src_dir.exists():
            raise FileNotFoundError(f"Model {model_id} not found in {from_stage}")
            
        dst_dir = self.root / to_stage / model_id
        if dst_dir.exists():
            logger.warning(f"Model {model_id} already exists in {to_stage}. Overwriting metadata.")
            # Usually we might error, but for idempotency let's just warn or cleanup
            # Ideally immutable.
            pass
            
        # Copy entire directory
        if dst_dir.exists():
             shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        
        logger.info(f"Promoted {model_id} from {from_stage} to {to_stage}")

    def get_model_path(self, model_id: str, stage: str = "prod"):
        """Get absolute path to model artifact in a specific stage."""
        d = self.root / stage / model_id
        # Looking for .pkl or .txt
        for f in d.iterdir():
            if f.suffix in ['.pkl', '.txt']:
                return f
        return None
