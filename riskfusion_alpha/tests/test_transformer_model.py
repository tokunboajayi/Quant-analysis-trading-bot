import pytest
import torch
import pandas as pd
import numpy as np
import shutil
from riskfusion.models.transformer import TransformerAlphaModel, TransformerWrapper
from riskfusion.models.dataset import WindowedDataset

def test_windowed_dataset():
    # Setup Data
    df = pd.DataFrame({
        'ticker': ['AAPL'] * 20,
        'date': pd.date_range('2020-01-01', periods=20),
        'feat1': np.random.randn(20),
        'feat2': np.random.randn(20),
        'target_fwd_5d': np.random.randn(20)
    })
    
    window = 5
    ds = WindowedDataset(df, ['feat1', 'feat2'], 'target_fwd_5d', window)
    
    # Expected length: 20 - 5 = 15
    assert len(ds) == 15
    
    x, y = ds[0]
    assert x.shape == (5, 2)
    assert isinstance(y, torch.Tensor)

def test_transformer_forward():
    # Batch, Seq, Feat
    x = torch.randn(32, 10, 5) 
    model = TransformerAlphaModel(input_dim=5, d_model=16, nhead=2, num_layers=1)
    
    out = model(x)
    assert out.shape == (32,)

def test_transformer_wrapper_train_predict(tmp_path):
    # Dummy DF
    df = pd.DataFrame({
        'ticker': ['AAPL'] * 50,
        'date': pd.date_range('2020-01-01', periods=50),
        'feat1': np.random.randn(50),
        'feat2': np.random.randn(50),
        'target_fwd_5d': np.random.randn(50)
    })
    
    wrapper = TransformerWrapper()
    # Mock device to CPU for test speed/compatibility
    wrapper.device = torch.device("cpu")
    wrapper.window_size = 5
    wrapper.batch_size = 10
    
    # Train
    wrapper.train(df, 'target_fwd_5d')
    assert wrapper.model is not None
    
    # Predict
    preds = wrapper.predict(df)
    assert len(preds) > 0
    assert isinstance(preds, np.ndarray)
