import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger
from riskfusion.utils.hashing import compute_hash

logger = get_logger("snapshot")

class SnapshotManager:
    def __init__(self):
        self.config = get_config()
        self.root_dir = Path(self.config.params['paths']['raw']).parent / "snapshots"
        self.root_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_id(self):
        # YYYYMMDD_YYYYMMDD_<hash>
        # We don't have date range easily available without data, so use Timestamp + Random
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        r = hashlib.sha256(os.urandom(10)).hexdigest()[:6]
        return f"{ts}_{r}"

    def create_snapshot(self, features_df: pd.DataFrame, description: str = "") -> str:
        """
        Create an immutable snapshot of the feature set.
        Returns the snapshot ID.
        """
        logger.info("Creating data snapshot...")
        snap_id = self._generate_id()
        snap_dir = self.root_dir / snap_id
        snap_dir.mkdir()
        
        # 1. Save Data
        logger.info(f"Saving features to {snap_dir}...")
        feats_path = snap_dir / "features.parquet"
        features_df.to_parquet(feats_path)
        
        # 2. Hash
        data_hash = compute_hash(features_df)
        
        # 3. Metadata
        metadata = {
            "id": snap_id,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "data_shape": features_df.shape,
            "data_hash": data_hash,
            "columns": list(features_df.columns),
            "config_snapshot": self.config.params,
            # In a real git repo, we'd grab the git commit too
        }
        
        with open(snap_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2, default=str)
            
        logger.info(f"Snapshot created: {snap_id}")
        return snap_id

    def list_snapshots(self):
        """List all snapshots."""
        snaps = []
        if not self.root_dir.exists():
            return []
            
        for d in self.root_dir.iterdir():
            if d.is_dir() and (d / "metadata.json").exists():
                try:
                    with open(d / "metadata.json", "r") as f:
                        meta = json.load(f)
                    snaps.append(meta)
                except Exception:
                    continue
        return sorted(snaps, key=lambda x: x['created_at'], reverse=True)

    def load_snapshot(self, snap_id: str) -> pd.DataFrame:
        """Load features from a snapshot."""
        snap_dir = self.root_dir / snap_id
        if not snap_dir.exists():
            raise FileNotFoundError(f"Snapshot {snap_id} not found.")
            
        return pd.read_parquet(snap_dir / "features.parquet")

    def get_metadata(self, snap_id: str) -> dict:
        snap_dir = self.root_dir / snap_id
        if not snap_dir.exists():
            raise FileNotFoundError(f"Snapshot {snap_id} not found.")
            
        with open(snap_dir / "metadata.json", "r") as f:
            return json.load(f)
