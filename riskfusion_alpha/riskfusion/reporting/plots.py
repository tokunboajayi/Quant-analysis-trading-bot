import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

def setup_style():
    plt.style.use('bmh')
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12

def save_plot(fig, output_dir: Path, filename: str):
    path = output_dir / filename
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    return str(path)

def plot_equity_curve(df: pd.DataFrame, output_dir: Path, filename="equity_curve.png"):
    setup_style()
    fig, ax = plt.subplots()
    
    # Needs 'equity_curve' column or cumsum returns
    if 'equity_curve' in df.columns:
        ax.plot(df.index, df['equity_curve'], label='Strategy')
    elif 'returns' in df.columns:
        curve = (1 + df['returns']).cumprod()
        ax.plot(df.index, curve, label='Strategy')
        
    if 'benchmark_returns' in df.columns:
        bench = (1 + df['benchmark_returns']).cumprod()
        ax.plot(df.index, bench, label='Benchmark', alpha=0.7, linestyle='--')
        
    ax.set_title("Equity Curve")
    ax.set_ylabel("Wealth Index")
    ax.legend()
    ax.grid(True)
    return save_plot(fig, output_dir, filename)

def plot_drawdown(df: pd.DataFrame, output_dir: Path, filename="drawdown.png"):
    setup_style()
    fig, ax = plt.subplots()
    
    if 'drawdown' in df.columns:
        dd = df['drawdown']
    elif 'returns' in df.columns:
        curve = (1 + df['returns']).cumprod()
        running_max = curve.cummax()
        dd = (curve - running_max) / running_max
    else:
        return None
        
    ax.fill_between(df.index, dd, 0, color='red', alpha=0.3)
    ax.plot(df.index, dd, color='red', lw=1)
    ax.set_title("Drawdown")
    ax.set_ylabel("Percent from Peak")
    ax.grid(True)
    return save_plot(fig, output_dir, filename)

def plot_rolling_vol(df: pd.DataFrame, output_dir: Path, window=21, filename="rolling_vol_vs_target.png"):
    setup_style()
    fig, ax = plt.subplots()
    
    if 'returns' not in df.columns:
        return None
        
    vol = df['returns'].rolling(window).std() * np.sqrt(252)
    ax.plot(df.index, vol, label=f'{window}D Vol')
    
    # Hardcoded target vol line if we knew it, or just plot realized
    ax.axhline(y=0.15, color='gray', linestyle='--', label='Target 15% (Ref)')
    
    ax.set_title("Realized Volatility (Annualized)")
    ax.legend()
    return save_plot(fig, output_dir, filename)
