"""
Cluster Caps - Step 4 of Crazy Quant Ladder
=============================================
Enforces maximum exposure per cluster to control concentration risk.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("cluster_caps")


class ClusterCapEnforcer:
    """
    Enforces cluster-level exposure caps on portfolio weights.
    
    Prevents hidden concentration in correlated assets.
    """
    
    def __init__(self):
        self.config = get_config()
        graph_config = self.config.params.get('graph', {})
        
        self.max_cluster_exposure = graph_config.get('max_cluster_exposure', 0.25)
        self.enabled = graph_config.get('enabled', False)
    
    def apply_caps(
        self,
        weights: pd.DataFrame,
        cluster_labels: pd.Series
    ) -> pd.DataFrame:
        """
        Apply cluster exposure caps to portfolio weights.
        
        Args:
            weights: DataFrame with 'weight' column, ticker as index
            cluster_labels: Series mapping ticker to cluster_id
        
        Returns:
            Adjusted weights DataFrame
        """
        if not self.enabled:
            return weights
        
        result = weights.copy()
        
        # Align cluster labels to weights
        aligned_clusters = cluster_labels.reindex(weights.index)
        
        # Handle missing cluster assignments
        if aligned_clusters.isna().any():
            logger.warning("Some tickers missing cluster assignment")
            aligned_clusters = aligned_clusters.fillna(-1)  # Unknown cluster
        
        # Calculate cluster exposures
        cluster_weights = result['weight'].groupby(aligned_clusters).sum()
        
        logger.info(f"Cluster exposures before caps: {cluster_weights.to_dict()}")
        
        # Identify clusters exceeding cap
        excess_clusters = cluster_weights[cluster_weights > self.max_cluster_exposure]
        
        if len(excess_clusters) == 0:
            result['cluster_cap_applied'] = False
            return result
        
        # Scale down weights in excess clusters
        for cluster_id, cluster_exposure in excess_clusters.items():
            scale_factor = self.max_cluster_exposure / cluster_exposure
            
            mask = (aligned_clusters == cluster_id)
            result.loc[mask, 'weight'] *= scale_factor
            
            logger.info(f"Cluster {cluster_id}: scaled by {scale_factor:.2f} "
                       f"({cluster_exposure:.2%} -> {self.max_cluster_exposure:.2%})")
        
        result['cluster_cap_applied'] = aligned_clusters.isin(excess_clusters.index)
        
        # Log result
        new_cluster_weights = result['weight'].groupby(aligned_clusters).sum()
        logger.info(f"Cluster exposures after caps: {new_cluster_weights.to_dict()}")
        
        return result
    
    def compute_concentration_index(
        self,
        weights: pd.Series,
        cluster_labels: pd.Series
    ) -> float:
        """
        Compute cluster concentration index (HHI-like).
        
        Lower is more diversified, higher is more concentrated.
        """
        aligned_clusters = cluster_labels.reindex(weights.index).fillna(-1)
        cluster_weights = weights.groupby(aligned_clusters).sum()
        
        # Herfindahl-Hirschman Index
        hhi = (cluster_weights ** 2).sum()
        
        return hhi


def apply_cluster_caps(
    weights: pd.DataFrame,
    returns: pd.DataFrame
) -> pd.DataFrame:
    """
    Convenience function to compute clusters and apply caps.
    
    Args:
        weights: DataFrame with 'weight' column
        returns: Historical returns for clustering
    
    Returns:
        Weights with cluster caps applied
    """
    from riskfusion.features.graph_features import GraphFeatureBuilder, is_graph_enabled
    
    if not is_graph_enabled():
        return weights
    
    # Build graph features (includes clustering)
    builder = GraphFeatureBuilder()
    graph_features = builder.compute_features(returns)
    
    # Apply caps
    enforcer = ClusterCapEnforcer()
    return enforcer.apply_caps(weights, graph_features['cluster_id'])
