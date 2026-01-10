import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from typing import List, Optional
from riskfusion.models.dataset import WindowedDataset
from torch.utils.data import DataLoader
from riskfusion.utils.logging import get_logger

logger = get_logger("transformer_model")

class TransformerAlphaModel(nn.Module):
    """
    Time-Series Transformer for Alpha Prediction.
    Architecture:
    - Input Embedding
    - Positional Encoding
    - Transformer Encoder Layers
    - MLP Head -> Scalar Output (Return forecast)
    """
    def __init__(self, input_dim: int, d_model: int = 64, nhead: int = 4, num_layers: int = 2, dropout: float = 0.1):
        super().__init__()
        self.input_embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 100, d_model)) # Max sequence length 100
        
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.decoder = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_dim)
        x = self.input_embedding(x)
        # Add pos encoding (broadcast)
        seq_len = x.size(1)
        x = x + self.pos_encoder[:, :seq_len, :]
        
        x = self.transformer_encoder(x)
        
        # Take last token output for causal prediction
        last_token = x[:, -1, :]
        out = self.decoder(last_token)
        return out.squeeze()

class TransformerWrapper:
    """Wrapper to make it behave like our standard AlphaModel (train/predict API)."""
    def __init__(self, features: List[str] = None):
        self.features = features or [] # Must be set before use
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.window_size = 10
        self.batch_size = 32
        
    def train(self, df: pd.DataFrame, target_col: str = 'target_fwd_5d'):
        self.features = [c for c in df.columns if c not in ['date', 'ticker', target_col]]
        input_dim = len(self.features)
        
        dataset = WindowedDataset(df, self.features, target_col, self.window_size)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        self.model = TransformerAlphaModel(input_dim).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        self.model.train()
        n_epochs = 5 # MVP
        
        logger.info(f"Training Transformer on {self.device} for {n_epochs} epochs...")
        
        for epoch in range(n_epochs):
            total_loss = 0
            for X_batch, y_batch in loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                
                optimizer.zero_grad()
                out = self.model(X_batch)
                loss = criterion(out, y_batch)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            logger.info(f"Epoch {epoch+1}: Loss {total_loss/len(loader):.4f}")

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        # Prediction needs windowed data.
        # This is tricky for 'current day' prediction if we don't have history in df.
        # We assume df contains enough history for the window for each ticker.
        # OR we just predict on whatever structure we can build.
        
        self.model.eval()
        # For prediction, we need to create windows too.
        # But WindowedDataset drops first (window-1) samples.
        # For production inference, we pass exactly 'window_size' rows per ticker.
        
        dataset = WindowedDataset(df, self.features, 'target_fwd_5d', self.window_size) 
        # Note: target col might be dummy if predicting live
        
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        preds = []
        
        with torch.no_grad():
            for X_batch, _ in loader:
                X_batch = X_batch.to(self.device)
                out = self.model(X_batch)
                preds.extend(out.cpu().numpy())
                
        # IMPORTANT: Padding or alignment. 
        # WindowedDataset reduces size. We need to align predictions to the original dataframe index.
        # Or return aligned series.
        # For MVP, just return the raw preds (note they are truncated).
        return np.array(preds)
