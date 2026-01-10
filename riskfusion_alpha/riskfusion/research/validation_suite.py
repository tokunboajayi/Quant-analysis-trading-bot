import pandas as pd
import numpy as np
from riskfusion.models.alpha_model import AlphaModel
from riskfusion.utils.logging import get_logger

logger = get_logger("validation_suite")

class ValidationSuite:
    """
    Statistical reality checks for research correctness.
    """
    
    @staticmethod
    def permutation_test(df: pd.DataFrame, n_permutes=5):
        """
        Train models on shuffled labels.
        Accuracy/IC should drop to near zero.
        If it stays high, there is leakage (features contain future info).
        """
        logger.info(f"Running Permutation Test ({n_permutes} rounds)...")
        results = []
        
        # True model
        model = AlphaModel()
        model.train(df)
        preds = model.predict(df.set_index('ticker'))
        true_ic = pd.DataFrame({'s': preds, 't': df['target_fwd_5d']}).corr().iloc[0,1]
        results.append({'type': 'true', 'ic': true_ic})
        
        # Permuted
        for i in range(n_permutes):
            df_perm = df.copy()
            # Shuffle target within date to preserve structure but break signal
            df_perm['target_fwd_5d'] = df_perm.groupby('date')['target_fwd_5d'].transform(np.random.permutation)
            
            p_model = AlphaModel()
            p_model.train(df_perm)
            p_preds = p_model.predict(df_perm.set_index('ticker'))
            
            p_ic = pd.DataFrame({'s': p_preds, 't': df_perm['target_fwd_5d']}).corr().iloc[0,1]
            results.append({'type': 'permuted', 'ic': p_ic})
            logger.info(f"Permutation {i}: IC={p_ic:.4f}")
            
        return pd.DataFrame(results)

    @staticmethod
    def regime_analysis(backtest_results: pd.DataFrame, market_vol: pd.Series):
        """
        Analyze performance in different vol regimes.
        """
        # TODO: Implement regime slicing
        pass
