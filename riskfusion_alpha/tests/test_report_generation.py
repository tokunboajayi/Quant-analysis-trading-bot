import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from riskfusion.reporting.paper import PaperReportGenerator

def test_report_generation(tmp_path, monkeypatch):
    # Setup
    run_id = "test_run"
    snap_id = "snap_123"
    out_dir = tmp_path / "reports"
    
    gen = PaperReportGenerator(run_id, snap_id, output_dir=str(out_dir))
    
    # Mock data
    dates = pd.date_range("2020-01-01", periods=100)
    df = pd.DataFrame({
        'returns': np.random.normal(0.001, 0.01, 100),
        'benchmark_returns': np.random.normal(0.0005, 0.01, 100)
    }, index=dates)
    
    # Run
    path = gen.generate(df)
    
    # Assert
    assert path.exists()
    assert (out_dir / "report.md").exists()
    assert (out_dir / "figures" / "equity_curve.png").exists()
    assert (out_dir / "figures" / "drawdown.png").exists()
    
    content = path.read_text()
    assert "RiskFusion Alpha: Technical Report" in content
    assert "Validation Suite" in content
