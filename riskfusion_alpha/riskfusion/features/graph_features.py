"""
Graph Features - Step 4 of Crazy Quant Ladder
==============================================
Clustering and correlation network features for risk control.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("graph_features")


class GraphFeatureBuilder:
    """
    Builds graph/cluster features from correlation structure.
    
    Used for:
    - Detecting hidden concentration risk
    - Cluster-based exposure caps
    - Centrality measures
    """
    
    def __init__(self):
        self.config = get_config()
        graph_config = self.config.params.get('graph', {})
        
        self.correlation_window = graph_config.get('correlation_window', 60)
        self.clustering_method = graph_config.get('clustering_method', 'hierarchical')
        self.n_clusters = graph_config.get('n_clusters', 10)
    
    def compute_features(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Compute graph-based features for each ticker.
        
        Args:
            returns: DataFrame with tickers as columns, dates as index
        
        Returns:
            DataFrame with graph features per ticker
        """
        logger.info("Computing graph features...")
        
        # Compute correlation matrix
        recent = returns.tail(self.correlation_window)
        corr_matrix = recent.corr()
        
        # Handle NaN (tickers with insufficient data)
        corr_matrix = corr_matrix.fillna(0)
        
        tickers = corr_matrix.columns.tolist()
        
        # Cluster assignment
        cluster_labels = self._cluster_tickers(corr_matrix)
        
        # Centrality measures
        centrality = self._compute_centrality(corr_matrix)
        
        # Build feature DataFrame
        features = pd.DataFrame({
            'cluster_id': cluster_labels,
            'centrality': centrality,
            'avg_correlation': corr_matrix.mean(axis=1).values,
            'max_correlation': (corr_matrix - np.eye(len(tickers))).max(axis=1).values,
        }, index=tickers)
        
        logger.info(f"Graph features computed for {len(tickers)} tickers, "
                   f"{len(set(cluster_labels))} clusters")
        
        return features
    
    def _cluster_tickers(self, corr_matrix: pd.DataFrame) -> np.ndarray:
        """
        Cluster tickers based on correlation structure.
        """
        if self.clustering_method == 'hierarchical':
            return self._hierarchical_clustering(corr_matrix)
        elif self.clustering_method == 'spectral':
            return self._spectral_clustering(corr_matrix)
        else:
            # Default: equal-size clusters by ticker order
            n = len(corr_matrix)
            return np.repeat(np.arange(self.n_clusters), n // self.n_clusters + 1)[:n]
    
    def _hierarchical_clustering(self, corr_matrix: pd.DataFrame) -> np.ndarray:
        """Hierarchical clustering using correlation distance."""
        try:
            from scipy.cluster.hierarchy import linkage, fcluster
            from scipy.spatial.distance import squareform
            
            # Convert correlation to distance
            dist_matrix = 1 - corr_matrix.values
            np.fill_diagonal(dist_matrix, 0)
            
            # Ensure symmetry and valid range
            dist_matrix = np.clip(dist_matrix, 0, 2)
            dist_matrix = (dist_matrix + dist_matrix.T) / 2
            
            # Hierarchical clustering
            condensed = squareform(dist_matrix, checks=False)
            Z = linkage(condensed, method='ward')
            labels = fcluster(Z, t=self.n_clusters, criterion='maxclust')
            
            return labels - 1  # 0-indexed
            
        except Exception as e:
            logger.warning(f"Hierarchical clustering failed: {e}")
            return np.zeros(len(corr_matrix), dtype=int)
    
    def _spectral_clustering(self, corr_matrix: pd.DataFrame) -> np.ndarray:
        """Spectral clustering using correlation as affinity."""
        try:
            from sklearn.cluster import SpectralClustering
            
            # Use absolute correlation as affinity
            affinity = np.abs(corr_matrix.values)
            np.fill_diagonal(affinity, 1)
            
            clustering = SpectralClustering(
                n_clusters=self.n_clusters,
                affinity='precomputed',
                random_state=42
            )
            labels = clustering.fit_predict(affinity)
            
            return labels
            
        except Exception as e:
            logger.warning(f"Spectral clustering failed: {e}")
            return np.zeros(len(corr_matrix), dtype=int)
    
    def _compute_centrality(self, corr_matrix: pd.DataFrame) -> np.ndarray:
        """
        Compute degree centrality (sum of absolute correlations).
        High centrality = ticker is correlated with many others.
        """
        # Degree centrality = sum of |correlation| with others
        abs_corr = np.abs(corr_matrix.values)
        np.fill_diagonal(abs_corr, 0)
        centrality = abs_corr.sum(axis=1) / (len(corr_matrix) - 1)
        
        return centrality


def is_graph_enabled() -> bool:
    """Check if graph features are enabled in config."""
    config = get_config()
    return config.params.get('graph', {}).get('enabled', False)
