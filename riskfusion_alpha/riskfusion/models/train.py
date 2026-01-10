from riskfusion.features.store import FeatureStore
from riskfusion.models.alpha_model import AlphaModel
# from riskfusion.models.vol_model import VolModel
# from riskfusion.models.tail_model import TailModel
from riskfusion.utils.logging import setup_logging, get_logger

logger = get_logger("train_all")

def train_models():
    store = FeatureStore()
    logger.info("Loading features...")
    df = store.load_features()
    
    if df.empty:
        logger.error("No features found. Run 'riskfusion features' first.")
        return

    # Train Alpha
    am = AlphaModel()
    am.train(df)
    
    # Train Vol (Stub)
    # vm = VolModel()
    # vm.train(df)

if __name__ == "__main__":
    setup_logging()
    train_models()
