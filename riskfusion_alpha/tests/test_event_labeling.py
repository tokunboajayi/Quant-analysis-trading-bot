import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from riskfusion.labeling.event_impact import EventLabeler

@patch("riskfusion.labeling.event_impact.FeatureStore")
def test_label_events(mock_store_cls):
    # Setup Mock Data using List of Dicts (Foolproof)
    
    # 1. Prices
    # SPY: 5 days, 1% growth
    dates = pd.date_range('2023-01-01', periods=5, freq='B')
    prices_data = []
    
    # SPY
    for i, d in enumerate(dates):
        prices_data.append({
            'date': d,
            'ticker': 'SPY',
            'close': 100.0 * (1.01)**i
        })
        
    # AAPL
    # Day 0,1: 100
    # Day 2: 100 (Close)
    # Day 3: 110 (Close). Jump happens Day 2->3.
    # Day 4: 110.
    for i, d in enumerate(dates):
        price = 100.0
        if i >= 3:
            price = 110.0
        prices_data.append({
            'date': d,
            'ticker': 'AAPL',
            'close': price
        })
        
    prices = pd.DataFrame(prices_data)
    
    # 2. News
    # Event 1: Day 2 Before Close (10:00) -> Effective Day 2
    # Event 2: Day 2 After Close (18:00) -> Effective Day 3
    day2 = dates[2]
    evt1_ts = day2 + pd.Timedelta(hours=10)
    evt2_ts = day2 + pd.Timedelta(hours=18)
    
    news_data = [
        {
            'event_id': 'evt1',
            'timestamp': evt1_ts,
            'ticker': 'AAPL',
            'title': 'AM News',
            'description': 'Desc',
            'provider': 'test'
        },
        {
            'event_id': 'evt2',
            'timestamp': evt2_ts,
            'ticker': 'AAPL',
            'title': 'PM News',
            'description': 'Desc',
            'provider': 'test'
        }
    ]
    news_df = pd.DataFrame(news_data)
    filings_df = pd.DataFrame()
    
    # Mock Store
    mock_store = mock_store_cls.return_value
    mock_store.load_raw_prices.return_value = prices
    mock_store.load_raw_news.return_value = news_df
    mock_store.load_raw_filings.return_value = filings_df
    mock_store.processed_path = MagicMock()
    
    # Run Labeler
    lab = EventLabeler()
    labeled = lab.label_events()
    
    # Assertions
    assert not labeled.empty
    
    # Evt 1 (AM): Effective Day 2.
    # Return at Day 2 (Close 2 -> Close 3) is 100->110 (10%).
    # SPY Return is 1%.
    # AR = |10% - 1%| = 9%. High Impact.
    r1 = labeled[labeled['event_id'] == 'evt1'].iloc[0]
    assert r1['high_impact'] == 1
    assert r1['ar_1d'] > 0.05
    
    # Evt 2 (PM): Effective Day 3.
    # Return at Day 3 (Close 3 -> Close 4) is 110->110 (0%).
    # AR = |0% - 1%| = 1%. Low Impact (<2%).
    r2 = labeled[labeled['event_id'] == 'evt2'].iloc[0]
    assert r2['high_impact'] == 0
    assert r2['ar_1d'] < 0.02
