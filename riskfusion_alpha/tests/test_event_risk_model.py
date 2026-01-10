import pytest
import pandas as pd
import numpy as np
import shutil
from pathlib import Path
from riskfusion.models.event_risk import EventRiskModel

def test_event_risk_model(tmp_path):
    # Setup
    df = pd.DataFrame({
        'title': [
            'Company reports record profits', 
            'CEO resigns amid scandal', 
            'Quarterly earnings in line',
            'Merger talks confirmed',
            'Dividend declared'
        ],
        'description': ['Good news', 'Bad news', 'Neutral', 'Big news', 'Regular'],
        'high_impact': [1, 1, 0, 1, 0]
    })
    
    model = EventRiskModel()
    # Mock path to tmp
    model.model_path = tmp_path / "model.pkl"
    
    # Train
    model.train(df)
    assert model.model_path.exists()
    
    # Predict
    test_df = pd.DataFrame({
        'title': ['Profits soar', 'Nothing happened'],
        'description': ['Great', 'Boring']
    })
    
    probs = model.predict(test_df)
    assert len(probs) == 2
    assert isinstance(probs, np.ndarray)
    assert 0.0 <= probs[0] <= 1.0
    
    # Reload
    model2 = EventRiskModel()
    model2.model_path = tmp_path / "model.pkl"
    probs2 = model2.predict(test_df)
    assert np.allclose(probs, probs2)
