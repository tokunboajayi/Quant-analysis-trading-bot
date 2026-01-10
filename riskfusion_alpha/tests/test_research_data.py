import pytest
import pandas as pd
import numpy as np
import shutil
from pathlib import Path
from riskfusion.research.snapshot import SnapshotManager
from riskfusion.research.leakage_checks import LeakageDetector, LeakageError

def test_leakage_future_peeking():
    # Construct leakage
    df = pd.DataFrame({
        'price': [100, 101, 102, 103],
        'target': [0.01, 0.01, 0.01, 0] # dummy
    })
    # Perfect correlation not present yet
    # Let's make 'feature' = target * 100
    df['feature_leaky'] = df['target'] * 100
    
    # 1. Check
    with pytest.raises(LeakageError):
        LeakageDetector.check_future_peeking(df, ['feature_leaky'])

    # 2. Safe feature
    df['feature_safe'] = np.random.randn(4)
    LeakageDetector.check_future_peeking(df, ['feature_safe'])

def test_snapshot_lifecycle(tmp_path, monkeypatch):
    # Mock config path
    from riskfusion.config import Config
    
    # Create temp data dir
    d = tmp_path / "data"
    d.mkdir()
    (d/"raw").mkdir()
    
    # Patch get_config to return temp paths
    def mock_get_config():
        return Config() # Default, but we interpret paths relative if possible? 
        # Actually Config logic is hardcoded to absolute paths in some places, 
        # or relative to cwd.
        # Let's simple use the class directly with patch
        pass

    # Easier: Just verify SnapshotManager logic if we point it to tmp_path
    # We need to subclass or patch __init__
    
    # Real integration test with the actual class structure:
    # It assumes project structure. Let's just run it if environment allows.
    mgr = SnapshotManager()
    mgr.root_dir = tmp_path / "snapshots" # Override root
    mgr.root_dir.mkdir()
    
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    sid = mgr.create_snapshot(df, "test snap")
    
    assert (mgr.root_dir / sid / "features.parquet").exists()
    assert (mgr.root_dir / sid / "metadata.json").exists()
    
    loaded = mgr.load_snapshot(sid)
    pd.testing.assert_frame_equal(df, loaded)
    
    snaps = mgr.list_snapshots()
    assert len(snaps) == 1
    assert snaps[0]['id'] == sid
