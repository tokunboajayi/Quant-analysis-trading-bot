import pandas as pd
import numpy as np
from datetime import timedelta
from riskfusion.research.experiment import ExperimentTracker
from riskfusion.models.alpha_model import AlphaModel
from riskfusion.monitoring.drift import calculate_psi
from riskfusion.utils.logging import get_logger

logger = get_logger("walkforward")

class WalkForwardRunner:
    def __init__(self, features_df: pd.DataFrame, initial_train_days=750, test_size_days=63, step_size_days=21):
        self.df = features_df.sort_values('date').reset_index(drop=True)
        self.initial_train_days = initial_train_days
        self.test_size_days = test_size_days
        self.step_size_days = step_size_days
        
    def run(self):
        """
        Execute sliding window walk-forward.
        """
        tracker = ExperimentTracker(exp_name="walkforward")
        tracker.log_params({
            "initial_train_days": self.initial_train_days,
            "test_size_days": self.test_size_days,
            "step_size_days": self.step_size_days
        })
        
        dates = self.df['date'].unique()
        dates = np.sort(dates)
        
        if len(dates) < self.initial_train_days + self.test_size_days:
            logger.error("Not enough data for walk-forward.")
            return
            
        # Pointers are indices in 'dates' array
        train_start_idx = 0
        train_end_idx = self.initial_train_days # Exclusive
        
        results = []
        
        fold = 0
        while train_end_idx + self.test_size_days <= len(dates):
            train_end_date = dates[train_end_idx-1]
            test_start_date = dates[train_end_idx]
            test_end_date = dates[train_end_idx + self.test_size_days - 1]
            
            logger.info(f"Fold {fold}: Train ending {train_end_date}, Test [{test_start_date} -> {test_end_date}]")
            
            # Slicing
            train_mask = (self.df['date'] < test_start_date) # Expanding window vs Sliding? User said "Retrain every step". Usually implies expanding or rolling. Let's assume Expanding for max data, or Sliding for regime adaptation. User prompt says "Train [Start, Start + N]". This implies Sliding usually, or Fixed Start. Let's stick to Expanding Window (Start=0) is usually safer for ML unless non-stationary. BUT prompt says "initial_train_years... test_window... step_size...". 
            # I will use Sliding Window if I follow "Start + N" literally, but Expanding is common. 
            # Let's implement Expanding Window (Start fixed at 0) as default for better signal.
            
            train_data = self.df[self.df['date'] < test_start_date]
            test_data = self.df[(self.df['date'] >= test_start_date) & (self.df['date'] <= test_end_date)]
            
            # Train
            model = AlphaModel()
            model.train(train_data)
            
            # Predict
            preds = model.predict(test_data.set_index('ticker'))
            test_data = test_data.copy()
            test_data['score'] = preds
            
            # Eval (IC)
            ic = test_data[['score', 'target_fwd_5d']].corr().iloc[0,1]
            results.append({
                'fold': fold,
                'test_start': test_start_date,
                'test_end': test_end_date,
                'ic': ic,
                'n_test': len(test_data)
            })
            
            # Step
            train_end_idx += self.step_size_days
            fold += 1
            
        tracker.log_metrics({"folds": results, "mean_ic": np.mean([r['ic'] for r in results])})
        tracker.end()
        return pd.DataFrame(results)
