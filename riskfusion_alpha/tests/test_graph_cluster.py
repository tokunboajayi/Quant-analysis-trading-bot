"""
Tests for Graph Features and Cluster Caps (Step 4)
===================================================
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestGraphFeatureBuilder:
    """Test graph feature computation."""
    
    @patch('riskfusion.features.graph_features.get_config')
    def test_compute_features_returns_dataframe(self, mock_config):
        """Test that compute_features returns proper DataFrame."""
        from riskfusion.features.graph_features import GraphFeatureBuilder
        
        mock_config.return_value.params = {
            'graph': {
                'enabled': True,
                'correlation_window': 60,
                'clustering_method': 'hierarchical',
                'n_clusters': 3
            }
        }
        
        # Create correlated returns
        np.random.seed(42)
        factor = np.random.randn(100)
        returns = pd.DataFrame({
            'A': factor * 0.8 + np.random.randn(100) * 0.2,
            'B': factor * 0.7 + np.random.randn(100) * 0.3,
            'C': -factor * 0.5 + np.random.randn(100) * 0.5,
            'D': np.random.randn(100),
        }) * 0.02
        
        builder = GraphFeatureBuilder()
        features = builder.compute_features(returns)
        
        assert 'cluster_id' in features.columns
        assert 'centrality' in features.columns
        assert 'avg_correlation' in features.columns
        assert len(features) == 4
    
    @patch('riskfusion.features.graph_features.get_config')
    def test_cluster_labels_valid(self, mock_config):
        """Test that cluster labels are valid integers."""
        from riskfusion.features.graph_features import GraphFeatureBuilder
        
        mock_config.return_value.params = {
            'graph': {'correlation_window': 60, 'n_clusters': 3}
        }
        
        np.random.seed(42)
        returns = pd.DataFrame(np.random.randn(100, 5) * 0.02, columns=list('ABCDE'))
        
        builder = GraphFeatureBuilder()
        features = builder.compute_features(returns)
        
        # All cluster IDs should be valid
        assert features['cluster_id'].dtype in [np.int32, np.int64, int]
        assert features['cluster_id'].min() >= 0


class TestClusterCapEnforcer:
    """Test cluster cap enforcement."""
    
    @patch('riskfusion.portfolio.cluster_caps.get_config')
    def test_apply_caps_reduces_excess(self, mock_config):
        """Test that excess cluster exposure is reduced."""
        from riskfusion.portfolio.cluster_caps import ClusterCapEnforcer
        
        mock_config.return_value.params = {
            'graph': {'enabled': True, 'max_cluster_exposure': 0.30}
        }
        
        enforcer = ClusterCapEnforcer()
        
        # Cluster 0 has 50% exposure (exceeds 30% cap)
        weights = pd.DataFrame({
            'weight': [0.25, 0.25, 0.20, 0.15, 0.15]
        }, index=['A', 'B', 'C', 'D', 'E'])
        
        cluster_labels = pd.Series([0, 0, 1, 1, 2], index=['A', 'B', 'C', 'D', 'E'])
        
        result = enforcer.apply_caps(weights, cluster_labels)
        
        # Cluster 0 should be capped at 30%
        cluster_0_weights = result.loc[['A', 'B'], 'weight'].sum()
        assert cluster_0_weights <= 0.31  # With tolerance
    
    @patch('riskfusion.portfolio.cluster_caps.get_config')
    def test_no_change_when_disabled(self, mock_config):
        """Test that weights unchanged when feature disabled."""
        from riskfusion.portfolio.cluster_caps import ClusterCapEnforcer
        
        mock_config.return_value.params = {
            'graph': {'enabled': False, 'max_cluster_exposure': 0.30}
        }
        
        enforcer = ClusterCapEnforcer()
        
        weights = pd.DataFrame({'weight': [0.5, 0.5]}, index=['A', 'B'])
        cluster_labels = pd.Series([0, 0], index=['A', 'B'])
        
        result = enforcer.apply_caps(weights, cluster_labels)
        
        # Weights should be unchanged
        pd.testing.assert_frame_equal(result[['weight']], weights)
    
    @patch('riskfusion.portfolio.cluster_caps.get_config')
    def test_concentration_index(self, mock_config):
        """Test concentration index calculation."""
        from riskfusion.portfolio.cluster_caps import ClusterCapEnforcer
        
        mock_config.return_value.params = {'graph': {'enabled': True}}
        
        enforcer = ClusterCapEnforcer()
        
        # Concentrated portfolio (all in one cluster)
        weights_conc = pd.Series([0.5, 0.5], index=['A', 'B'])
        clusters_conc = pd.Series([0, 0], index=['A', 'B'])
        hhi_conc = enforcer.compute_concentration_index(weights_conc, clusters_conc)
        
        # Diversified portfolio (spread across clusters)
        weights_div = pd.Series([0.25, 0.25, 0.25, 0.25], index=['A', 'B', 'C', 'D'])
        clusters_div = pd.Series([0, 1, 2, 3], index=['A', 'B', 'C', 'D'])
        hhi_div = enforcer.compute_concentration_index(weights_div, clusters_div)
        
        # Concentrated should have higher HHI
        assert hhi_conc > hhi_div


class TestIsGraphEnabled:
    """Test feature flag detection."""
    
    @patch('riskfusion.features.graph_features.get_config')
    def test_flag_off(self, mock_config):
        from riskfusion.features.graph_features import is_graph_enabled
        mock_config.return_value.params = {'graph': {'enabled': False}}
        assert is_graph_enabled() == False
    
    @patch('riskfusion.features.graph_features.get_config')
    def test_flag_on(self, mock_config):
        from riskfusion.features.graph_features import is_graph_enabled
        mock_config.return_value.params = {'graph': {'enabled': True}}
        assert is_graph_enabled() == True
