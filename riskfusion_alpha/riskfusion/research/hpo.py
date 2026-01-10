import optuna
import pandas as pd
import numpy as np
from riskfusion.models.alpha_model import AlphaModel
from riskfusion.features.store import FeatureStore
from riskfusion.utils.logging import get_logger

logger = get_logger("hpo")

def objective(trial):
    # 1. Suggest Params
    params = {
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2),
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'num_leaves': trial.suggest_int('num_leaves', 20, 100),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True)
    }
    
    # 2. Load Data
    store = FeatureStore()
    df = store.load_features()
    
    if df.empty:
        logger.warning("No features found for HPO.")
        raise optuna.TrialPruned()
        
    try:
        # Simple Time Split Cross Validation
        dates = df['date'].sort_values().unique()
        if len(dates) < 10:
             logger.warning("Not enough dates for split.")
             raise optuna.TrialPruned()

        split_idx = int(len(dates) * 0.8)
        split_date = dates[split_idx]
        
        train_df = df[df['date'] < split_date]
        valid_df = df[df['date'] >= split_date]
        
        if train_df.empty or valid_df.empty:
            logger.warning("Insufficient data for split.")
            raise optuna.TrialPruned()

        # 3. Train
        model = AlphaModel(**params)
        model.train(train_df)
        
        # 4. Evaluate (IC)
        # Handle cases where predict returns scalar or mismatch
        preds = model.predict(valid_df.set_index('ticker'))
        
        # Ensure preds match valid_df index
        if len(preds) != len(valid_df):
            logger.error(f"Prediction length mismatch: {len(preds)} vs {len(valid_df)}")
            raise ValueError("Prediction mismatch")

        valid_df = valid_df.copy() # Avoid SettingWithCopy
        valid_df['pred'] = preds
        
        # IC per day
        # Handle if target is all NaN or constant
        ic_series = valid_df.groupby('date').apply(lambda x: x['pred'].corr(x['target_fwd_5d']))
        mean_ic = ic_series.mean()
        
        if np.isnan(mean_ic):
            logger.warning("NaN IC calculated.")
            return 0.0

        logger.info(f"Trial {trial.number}: Mean IC {mean_ic:.4f}")
        return mean_ic

    except Exception as e:
        logger.error(f"Trial failed with error: {e}", exc_info=True)
        raise e

def run_hpo(n_trials=10):
    logger.info(f"Starting HPO with {n_trials} trials...")
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    
    logger.info("Best Params:")
    logger.info(study.best_params)
    
    # Save best params?
    # import json
    # with open("best_params.json", 'w') as f:
    #     json.dump(study.best_params, f)
        
    return study.best_params
