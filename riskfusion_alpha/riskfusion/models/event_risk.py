import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
import lightgbm as lgb
from riskfusion.config import get_config
from riskfusion.utils.logging import get_logger

logger = get_logger("event_risk_model")

class EventRiskModel:
    """
    NLP Model to predict High Impact Events.
    Input: Title + Description
    Output: Probability of High Impact (Label=1)
    """
    def __init__(self):
        self.config = get_config()
        self.pipeline = None
        self.model_path = Path(self.config.params['paths']['models']) / "event_risk_model.pkl"
        
    def train(self, labeled_events: pd.DataFrame):
        """
        Train on labeled events.
        cols: title, description, high_impact
        """
        if labeled_events.empty:
            logger.warning("No data to train EventRiskModel.")
            return

        logger.info(f"Training EventRiskModel on {len(labeled_events)} events...")
        
        # Prepare Text
        X = labeled_events['title'].fillna('') + " " + labeled_events['description'].fillna('')
        y = labeled_events['high_impact']
        
        if y.sum() == 0:
            logger.warning("No positive labels found. Skipping training.")
            return
            
        # Pipeline: TF-IDF -> LGBM
        # Tokenizer params tailored for finance news (keep caps? maybe not. keep numbers? yes)
        vectorizer = TfidfVectorizer(
            max_features=5000, 
            stop_words='english', 
            ngram_range=(1, 2)
        )
        
        clf = lgb.LGBMClassifier(
            objective='binary',
            metric='auc',
            n_estimators=100,
            learning_rate=0.05,
            is_unbalance=True # Important for rare events
        )
        
        self.pipeline = Pipeline([
            ('tfidf', vectorizer),
            ('clf', clf)
        ])
        
        self.pipeline.fit(X, y)
        self.save()
        logger.info("EventRiskModel trained and saved.")

    def predict(self, events: pd.DataFrame) -> np.ndarray:
        """
        Predict prob of high impact.
        Returns array of probabilities [0, 1].
        """
        if self.pipeline is None:
            self.load()
            
        if events.empty:
            return np.array([])
            
        text = events['title'].fillna('') + " " + events['description'].fillna('')
        # Predict proba
        # Classes are [0, 1] usually
        try:
            probs = self.pipeline.predict_proba(text)[:, 1]
            return probs
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return np.zeros(len(events))

    def save(self):
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)
        
    def load(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        self.pipeline = joblib.load(self.model_path)
