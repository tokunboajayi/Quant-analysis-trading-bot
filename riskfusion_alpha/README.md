<div align="center">

<!-- Animated Header -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:667eea,100:764ba2&height=200&section=header&text=RiskFusion%20Alpha&fontSize=50&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Institutional-Grade%20ML%20Trading%20System&descSize=18&descAlignY=55" width="100%"/>

<!-- Animated Badges -->
<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/XGBoost-ML%20Engine-FF6600?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost"/>
  <img src="https://img.shields.io/badge/Alpaca-Trading%20API-FFCD00?style=for-the-badge&logo=alpaca&logoColor=black" alt="Alpaca"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Tests-Passing-success?style=flat-square" alt="Tests"/>
</p>

<!-- Typing Animation -->
<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=667EEA&center=true&vCenter=true&multiline=true&width=600&height=80&lines=Alpha+Generation+%E2%80%A2+Risk+Management;Event-Driven+Trading+%E2%80%A2+ML+Optimization" alt="Typing SVG" /></a>

</div>

---

## 🚀 What is RiskFusion?

**RiskFusion Alpha** is a production-grade quantitative trading system that combines:

- 🧠 **Machine Learning Alpha** — XGBoost models for cross-sectional stock prediction
- 📊 **Multi-Factor Risk Model** — Volatility forecasting + event risk overlays
- ⚡ **Automated Execution** — Live/Paper trading via Alpaca Markets API
- 🔮 **Regime Detection** — Hidden Markov Models for market state awareness
- 📈 **Real-time Dashboard** — Bloomberg-style monitoring via QuantDash

<div align="center">
  <img src="https://raw.githubusercontent.com/Platane/snk/output/github-contribution-grid-snake-dark.svg" width="100%" alt="Snake animation"/>
</div>

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🎯 Alpha Generation
- Cross-sectional momentum signals
- Sentiment analysis from news
- Technical indicators (RSI, MACD, etc.)
- Graph-based features (sector correlations)

</td>
<td width="50%">

### 🛡️ Risk Management
- CVXPY portfolio optimization
- Inverse volatility weighting
- Event risk overlays (earnings, FDA)
- Position concentration limits

</td>
</tr>
<tr>
<td width="50%">

### 🔬 Research Tools
- Walk-forward backtesting
- Hyperparameter optimization (Optuna)
- Ablation studies
- Feature drift monitoring

</td>
<td width="50%">

### 🏭 Production Ready
- Model registry with staging gates
- Comprehensive audit logging
- SQLite persistence layer
- Docker containerization

</td>
</tr>
</table>

---

## 🏗️ Architecture

```mermaid
graph LR
    subgraph Data Layer
        A[Polygon.io] --> D[Ingest]
        B[Alpaca] --> D
        C[Marketaux] --> D
    end
    
    subgraph Feature Engine
        D --> E[Technical Features]
        D --> F[Sentiment Features]
        D --> G[Event Features]
    end
    
    subgraph ML Models
        E & F & G --> H[Alpha Model]
        E --> I[Vol Model]
        G --> J[Event Risk Model]
    end
    
    subgraph Portfolio
        H & I & J --> K[Optimizer]
        K --> L[OMS]
    end
    
    subgraph Execution
        L --> M[Alpaca Trading]
    end
    
    style H fill:#667eea
    style K fill:#764ba2
    style M fill:#f093fb
```

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/riskfusion-alpha.git
cd riskfusion-alpha
pip install -e .[dev]
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
# - POLYGON_API_KEY
# - ALPACA_API_KEY / ALPACA_SECRET_KEY
```

### 3. Run Daily Pipeline

```bash
# Paper trading (safe)
EXECUTION_MODE=PAPER python -m riskfusion.cli run_daily

# Live trading (real money!)
EXECUTION_MODE=LIVE ALLOW_LIVE_TRADING=1 python -m riskfusion.cli run_daily
```

---

## 📊 CLI Commands

| Command | Description |
|---------|-------------|
| `run_daily` | Execute full pipeline (ingest → predict → trade) |
| `backtest --start 2023-01-01 --end 2024-01-01` | Run historical backtest |
| `ablation --steps 0,1,2,3` | Compare feature ladder ablation |
| `validate_research` | Permutation tests for statistical validity |
| `registry list --stage prod` | View production models |

---

## 🖥️ Dashboard (QuantDash)

The companion dashboard provides real-time monitoring:

<div align="center">

| Feature | Description |
|---------|-------------|
| 📈 **Portfolio View** | Live positions & P&L |
| 🚦 **Pipeline Status** | Step-by-step execution tracker |
| 🎮 **Bot Control** | Start/Stop/Run-Once from UI |
| ⚠️ **Alerts** | Drift detection & warnings |

</div>

---

## 📁 Project Structure

```
riskfusion_alpha/
├── riskfusion/
│   ├── ingest/          # Data ingestion (prices, events)
│   ├── features/        # Feature engineering
│   ├── models/          # ML models (alpha, vol, regime)
│   ├── portfolio/       # Optimization & construction
│   ├── execution/       # Order management (Alpaca)
│   ├── research/        # Backtesting, walk-forward, HPO
│   ├── monitoring/      # Drift detection, reports
│   └── cli.py           # Command-line interface
├── configs/             # YAML configuration
├── data/                # Raw/processed data (gitignored)
├── tests/               # Pytest test suite
└── docs/                # Documentation
```

---

## 🔒 Security

- **API Keys**: Stored in `.env` (gitignored)
- **Live Trading**: Requires explicit `ALLOW_LIVE_TRADING=1`
- **Paper Mode**: Default for safety
- **Audit Logs**: Full run history in SQLite

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### ⭐ Star this repo if you find it useful!

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:667eea,100:764ba2&height=100&section=footer" width="100%"/>

</div>
