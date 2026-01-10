import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from typing import List, Tuple

class WindowedDataset(Dataset):
    """
    PyTorch Dataset for sliding window time-series data.
    """
    def __init__(self, features: pd.DataFrame, feature_cols: List[str], target_col: str, window_size: int = 10):
        self.window_size = window_size
        
        # Sort by ticker, then date to ensure contiguous windows
        # Note: This assumes single ticker or pre-grouped data. 
        # For multi-ticker, we need to be careful not to window across tickers.
        # MVP: Group by ticker and concat windows? Or just iterate carefully.
        
        # Robust approach: 
        # 1. Group by ticker.
        # 2. For each group, create sliding windows.
        # 3. Concatenate all windows. (Memory intensive for huge data, good for alpha)
        
        self.X = []
        self.y = []
        
        # Optimize: Use numpy striding or just loop for MVP clarity
        grouped = features.groupby('ticker')
        
        for ticker, group in grouped:
            group = group.sort_values('date')
            x_vals = group[feature_cols].values.astype(np.float32)
            y_vals = group[target_col].values.astype(np.float32)
            
            if len(x_vals) <= window_size:
                continue
                
            # Create windows
            # Shape: (N_samples, window_size, n_features)
            # Use stride_tricks for efficiency if needed, but simple loop is safer for now
            for i in range(len(x_vals) - window_size):
                self.X.append(x_vals[i : i+window_size])
                self.y.append(y_vals[i+window_size-1]) # Predict NEXT step? Or aligned with last step?
                # Usually target is 'forward return' aligned at t.
                # If target_col is 'target_fwd_5d', it is known at t (label).
                # So we take the target corresponding to the last timestamp in window.
                
        self.X = np.array(self.X)
        self.y = np.array(self.y)
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return torch.from_numpy(self.X[idx]), torch.tensor(self.y[idx])
