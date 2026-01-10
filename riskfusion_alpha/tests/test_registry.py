import pytest
import shutil
from pathlib import Path
from riskfusion.registry.registry import ModelRegistry
from riskfusion.research.gates import QualityGates, GateError

def test_registry_flow(tmp_path, monkeypatch):
    # Mock paths
    from riskfusion.config import Config
    
    reg = ModelRegistry()
    reg.root = tmp_path / "registry"
    for s in ["candidates", "staging", "prod"]:
        (reg.root / s).mkdir(parents=True)
        
    # Create dummy artifact
    metric_file = tmp_path / "model.pkl"
    metric_file.write_text("dummy model")
    
    # Register
    mid = reg.register_candidate(str(metric_file), {"mean_ic": 0.05}, {}, "test model")
    
    assert (reg.root / "candidates" / mid / "model.pkl").exists()
    assert mid in reg.list_models("candidates")
    
    # Promote
    reg.promote(mid, "candidates", "staging")
    assert mid in reg.list_models("staging")

def test_gates():
    # Pass
    metrics = {"mean_ic": 0.02}
    assert QualityGates.check_candidate_gates(metrics)
    
    # Fail
    metrics_bad = {"mean_ic": 0.005}
    with pytest.raises(GateError):
        QualityGates.check_candidate_gates(metrics_bad)
