import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import sys
import os

# Add root to string to allow imports if running from dashboard dir
sys.path.append(str(Path(__file__).parent.parent.parent))

from riskfusion.config import get_config

st.set_page_config(page_title="RiskFusion Alpha", layout="wide")

st.title("⚡ RiskFusion Alpha Dashboard")

config = get_config()
output_path = Path(config.params['paths']['outputs'])

# Sidebar
st.sidebar.header("Controls")
selected_date = st.sidebar.date_input("Select Date")

# Convert to YYYYMMDD
date_str = selected_date.strftime("%Y%m%d")
risk_file = output_path / f"daily_risk_sheet_{date_str}.csv"
weights_file = output_path / f"daily_weights_{date_str}.csv"

if risk_file.exists():
    df = pd.read_csv(risk_file)
    st.success(f"Data found for {selected_date}")
    
    # Top Stats
    col1, col2, col3 = st.columns(3)
    portfolio_tickers = df[df['final_weight'] > 0]
    
    col1.metric("Positions", len(portfolio_tickers))
    col2.metric("Top Alpha", f"{df['alpha_score'].max():.4f}")
    col3.metric("Avg Vol Forecast", f"{df['vol_forecast'].mean():.2%}")
    
    # Main Table
    st.subheader("Portfolio Composition")
    st.dataframe(portfolio_tickers.sort_values('final_weight', ascending=False).style.format({
        'final_weight': '{:.2%}',
        'vol_forecast': '{:.2%}',
        'alpha_score': '{:.4f}'
    }))
    
    # Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Weight Allocation")
        fig_pie = px.pie(portfolio_tickers, values='final_weight', names='ticker', title='Portfolio Weights')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.subheader("Alpha vs Volatility")
        fig_scatter = px.scatter(df, x='vol_forecast', y='alpha_score', hover_data=['ticker'], 
                               size='final_weight', title='Risk/Reward Map')
        st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.warning(f"No data found for {selected_date}. Please run the daily pipeline first.")
    
    # Show available dates
    files = sorted(list(output_path.glob("daily_risk_sheet_*.csv")))
    if files:
        st.info("Available dates:")
        dates = [f.name.split('_')[-1].replace('.csv','') for f in files]
        st.write(dates)

# Backtest Section
st.markdown("---")
st.header("Backtest Results")
# Placeholder for backtest loading
# if (output_path / "backtest_metrics.csv").exists(): ...
st.write("Run `riskfusion backtest` to generate reports.")
