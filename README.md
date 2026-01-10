# 📈 RiskFusion: Complete System Guide

A comprehensive guide to understanding this quantitative trading system — from plain English concepts to mathematical foundations to technical architecture.

---

# Part 1: How It Works (For Everyone)

## 🎯 What Does This System Do?

**In one sentence:** It uses math and machine learning to decide which stocks to buy, how much to buy, and when to sell — automatically.

Think of it like a **smart autopilot for investing**:
- A human pilot (you) sets the destination and rules
- The autopilot (RiskFusion) handles the moment-to-moment decisions
- A dashboard shows you exactly what's happening in real-time

![QuantDash Screenshot](file:///C:/Users/olato/.gemini/antigravity/brain/35297e3a-6c07-4b8c-82df-5e619b7d80f9/uploaded_image_1768075655450.png)

---

## 🧩 The Big Picture

```
    STEP 1              STEP 2              STEP 3              STEP 4
   ┌────────┐         ┌────────┐         ┌────────┐         ┌────────┐
   │ Gather │   ──▶   │ Analyze│   ──▶   │ Decide │   ──▶   │ Execute│
   │  Data  │         │  Data  │         │  Trades│         │  Trades│
   └────────┘         └────────┘         └────────┘         └────────┘
   
   Get stock          Find patterns       Optimize           Buy/sell
   prices, news       using ML           the portfolio      through
   earnings           predictions                           broker
```

---

## 🔍 Step 1: Gathering Data

### What we collect:
| Data Type | What It Is | Why It Matters |
|-----------|------------|----------------|
| **Prices** | Stock prices every day | See how stocks are moving |
| **News** | Headlines about companies | Good/bad news affects prices |
| **Earnings** | Company profit reports | Major events cause big moves |

### The Types (for developers):
```python
Ticker = str          # "AAPL", "MSFT"
Price = float         # 150.25
Volume = int          # 1_000_000

class PriceBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
```

---

## 🔢 Step 2: Feature Engineering (Finding Patterns)

We transform raw data into **"features"** — numbers that describe what's happening.

### The Math (Simple):

| Feature | Plain English | Formula |
|---------|---------------|---------|
| **1-Day Return** | "How much did it move yesterday?" | `(Today - Yesterday) / Yesterday` |
| **20-Day Volatility** | "How jumpy is this stock?" | `std(last 20 days) × √252` |
| **Momentum** | "Is it on a winning streak?" | `avg(5 days) / avg(20 days) - 1` |

### The Math (Formal):
```
Return:     r = (P_t - P_{t-1}) / P_{t-1}
Volatility: σ = √[(1/n) × Σ(rᵢ - μ)²] × √252
            (annualized standard deviation)
```

### The Types:
```python
# Feature matrix: each row is a stock, each column is a feature
features: pd.DataFrame  # shape: (n_stocks, 50+ features)

class FeatureVector:
    ret_1d: float       # 1-day return
    ret_5d: float       # 5-day return
    vol_20d: float      # 20-day volatility
    momentum: float     # momentum score
    # ... 50+ features
```

---

## 🧠 Step 3: Machine Learning (The Prediction)

The system uses **XGBoost** (a type of AI) to predict which stocks will go up.

### How it works (simplified):
1. **Training:** Show the computer thousands of past examples
2. **Learning:** It finds patterns ("when momentum is high AND volatility is low → stocks go up")
3. **Predicting:** For new data, it predicts returns

### The Math (Simple):
```
Prediction = weighted_sum_of_features

Example:
  Expected Return = 0.3 × momentum + 0.2 × value - 0.1 × volatility
```

### The Math (Formal):
```
XGBoost builds an ensemble of decision trees:

  ŷ = Σ f_k(x)   where each f_k is a tree
  
Loss function:
  L = Σ(yᵢ - ŷᵢ)² + λ × complexity
      ↑              ↑
   Accuracy      Regularization
```

### The Types:
```python
# Input: feature matrix
X: np.ndarray[float64]  # shape: (n_stocks, n_features)

# Output: predicted returns
predictions: np.ndarray[float64]  # shape: (n_stocks,)

class AlphaPrediction:
    ticker: str
    expected_return: float  # e.g., 0.02 for 2%
    confidence: float       # 0 to 1
```

---

## ⚖️ Step 4: Portfolio Optimization (How Much to Buy?)

Knowing a stock might go up isn't enough. We need to decide **how much** to invest.

### The Problem:
- Apple looks good → buy 100% Apple? ❌ Too risky!
- All tech stocks look good → buy all tech? ❌ If tech crashes, you lose everything

### The Solution: Diversification + Math

```
BAD PORTFOLIO                    GOOD PORTFOLIO
┌─────────────────────────┐     ┌───┬───┬───┬───┬───┐
│       AAPL 100%         │     │10%│10%│ 8%│ 7%│...│
└─────────────────────────┘     └───┴───┴───┴───┴───┘

If Apple drops 20%,             If Apple drops 20%,
you lose 20%.                   you lose only 2%.
```

### The Math (Simple):
```
Find weights that:
  - Maximize expected return
  - Minimize risk
  - Stay within limits
```

### The Math (Formal):
```
Maximize:   α'w - λ × w'Σw
            ↑        ↑
         Return    Risk

Subject to:
  Σ wᵢ = 1              (weights sum to 1)
  0 ≤ wᵢ ≤ 0.10         (no single stock > 10%)
  w'Σw ≤ σ²_max         (total risk under limit)

Where:
  w = weight vector
  α = expected returns
  Σ = covariance matrix
  λ = risk aversion
```

### The Types:
```python
# Covariance matrix (how stocks move together)
cov_matrix: np.ndarray[float64]  # shape: (n_stocks, n_stocks)

# Optimal weights
weights: np.ndarray[float64]  # shape: (n_stocks,)
# Example: [0.10, 0.08, 0.07, 0.07, ...]

class PortfolioWeights:
    weights: dict[str, float]  # {"AAPL": 0.10, "MSFT": 0.08}
    concentration_hhi: float   # diversity score
```

---

## 📊 Key Metrics Explained

| Metric | Plain English | Good Value | Formula |
|--------|---------------|------------|---------|
| **Alpha (IC)** | How good are predictions? | > 0.05 | `correlation(predicted, actual)` |
| **Sharpe Ratio** | Return per unit of risk | > 1.0 | `(Return - RiskFree) / Volatility` |
| **Drawdown** | Worst loss from peak | < -10% | `(Current - Peak) / Peak` |
| **VaR** | Worst expected 1-day loss | < 2.5% | 5th percentile of returns |

### Why IC = 0.05 is good:
> Even a tiny edge, applied consistently across thousands of trades, compounds into significant returns.

### The Types:
```python
class MetricValue:
    value: float      # normalized 0-1
    raw: float        # actual value
    unit: str         # "IC", "%", etc.
    confidence: float
```

---

## 🌦️ Market Regimes

Markets behave differently at different times:

| Regime | What's Happening | Our Strategy |
|--------|------------------|--------------|
| **☀️ Clear** | Calm, predictable | Trade normally |
| **🌧️ Rain** | Some uncertainty | Reduce risk |
| **⛈️ Storm** | High volatility | Go defensive |

### The Math (Hidden Markov Model):
```
Transition Matrix:
              To Clear  To Rain  To Storm
From Clear  [   0.90     0.08     0.02   ]
From Rain   [   0.15     0.75     0.10   ]
From Storm  [   0.10     0.20     0.70   ]
```

### The Types:
```python
regime_state: Literal['clear', 'rain', 'storm']
regime_confidence: float  # 0.0 to 1.0
```

---

# Part 2: System Architecture

## 📁 Folder Structure

```
finance ai/
├── riskfusion_alpha/     # 🧠 Backend Engine (Python)
│   └── The quantitative trading brain
│
└── quant-car/            # 📊 Dashboard (TypeScript)
    └── Real-time visualization
```

---

## 🧠 RiskFusion Alpha (Backend)

### Directory Structure
```
riskfusion_alpha/
├── riskfusion/
│   ├── cli.py                  # Command-line interface
│   ├── daily_runner.py         # Orchestrates pipeline
│   │
│   ├── providers/              # DATA SOURCES
│   │   ├── polygon_client.py   # Market data
│   │   ├── alpaca_client.py    # Broker API
│   │   └── marketaux_client.py # News
│   │
│   ├── features/               # FEATURE ENGINEERING
│   │   ├── builder.py          # Build features
│   │   └── drift_detector.py   # Monitor drift
│   │
│   ├── models/                 # ML MODELS
│   │   ├── alpha_model.py      # Return prediction
│   │   ├── regime_model.py     # Market state
│   │   └── meta_labeler.py     # Confidence
│   │
│   ├── portfolio/              # OPTIMIZATION
│   │   └── optimizer.py        # CVXPY optimization
│   │
│   ├── execution/              # TRADING
│   │   └── alpaca_executor.py  # Execute orders
│   │
│   └── reporting/              # OUTPUT
│       └── telemetry_writer.py # Write JSON
│
└── data/outputs/               # Generated data
    └── telemetry/              # JSON frames
```

### Pipeline Flow
```
┌─────────────────────────────────────────────────────────────────────┐
│                        DAILY PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│  1. INGEST    → Fetch prices, news                                 │
│  2. FEATURES  → Build 50+ features                                 │
│  3. PREDICT   → ML models → alpha scores                           │
│  4. OPTIMIZE  → Convex optimization → weights                      │
│  5. EXECUTE   → Send orders to Alpaca                              │
│  6. REPORT    → Write telemetry JSON                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Quant-Car (Dashboard)

### Directory Structure
```
quant-car/
├── apps/
│   ├── api/                    # FASTAPI BACKEND
│   │   └── app/
│   │       ├── main.py         # API server
│   │       └── routes/
│   │           ├── telemetry.py
│   │           ├── research.py
│   │           └── incidents.py
│   │
│   └── cockpit/                # NEXT.JS FRONTEND
│       └── src/
│           ├── app/            # Pages
│           │   ├── quant/      # Main dashboard
│           │   ├── research/   # Analytics
│           │   └── ops/        # Health
│           │
│           ├── components/     # React components
│           │   ├── Shell.tsx   # Grid layout
│           │   ├── Panel.tsx   # Containers
│           │   └── ...
│           │
│           └── quant/
│               └── visuals/    # Pixi charts
│                   ├── SankeyFlow.ts
│                   ├── EquityRibbon.ts
│                   └── ...
│
└── docker-compose.yml          # Container orchestration
```

---

## 🔄 Data Flow

```
EXTERNAL APIs     →    RISKFUSION    →    QUANT-CAR
┌─────────┐           ┌──────────┐       ┌─────────┐
│ Polygon │──prices──▶│          │       │ FastAPI │
│ Alpaca  │──orders──▶│  Python  │──────▶│   API   │
│Marketaux│──news────▶│  Engine  │       └────┬────┘
└─────────┘           └────┬─────┘            │
                           │                  ▼
                           ▼              ┌─────────┐
                    ┌──────────────┐      │ Next.js │───▶ Browser
                    │ telemetry/   │      │ PixiJS  │    (60fps)
                    │ latest.json  │      └─────────┘
                    └──────────────┘
```

---

## 📋 Telemetry Schema

The JSON that connects everything:

```json
{
  "ts_utc": "2026-01-10T18:00:00Z",
  "trading_date": "20260110",
  "execution_mode": "PAPER",
  "pipeline_status": "ok",
  
  "speed_alpha": { "value": 0.63, "unit": "IC" },
  "pnl": { "equity": 100000, "drawdown": -0.012 },
  
  "portfolio_flow": {
    "nodes": [{ "id": "AAPL", "weight": 0.10 }]
  },
  
  "regime_state": "storm",
  "warnings": [{ "code": "DRIFT", "severity": 3 }],
  "models": [{ "name": "alpha", "health": 0.85 }]
}
```

### TypeScript Types:
```typescript
interface TelemetryFrame {
  ts_utc: string
  trading_date: string
  execution_mode: 'PAPER' | 'LIVE'
  pipeline_status: 'ok' | 'running' | 'failed'
  
  speed_alpha: MetricValue
  pnl: { equity: number; drawdown: number }
  
  portfolio_flow: {
    nodes: PortfolioNode[]
    edges: PortfolioEdge[]
  }
  
  regime_state: 'clear' | 'rain' | 'storm'
  warnings: Warning[]
  models: ModelHealth[]
}
```

---

## 🚀 Running the System

### Development
```bash
# Terminal 1: RiskFusion pipeline
cd riskfusion_alpha
python -m riskfusion.cli run --mode paper

# Terminal 2: API server
cd quant-car/apps/api
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd quant-car/apps/cockpit
npm run dev
```

### Docker
```bash
cd quant-car
docker-compose up --build
```

Open **http://localhost:3000/quant**

---

## 🎯 Summary

| Component | Role | Key Tech |
|-----------|------|----------|
| **RiskFusion** | Trading engine | Python, XGBoost, CVXPY |
| **Quant-Car API** | Data server | FastAPI |
| **Quant-Car Cockpit** | Dashboard | Next.js, PixiJS |

**The system:**
1. Collects data → builds features → predicts returns
2. Optimizes portfolio using convex math
3. Executes trades, writes telemetry
4. Dashboard polls at 2Hz, renders at 60fps

This is a **production-grade quantitative trading system** with institutional-quality monitoring.

---

## 📖 Glossary

| Term | Simple Definition |
|------|-------------------|
| **Alpha** | Excess return beyond market average |
| **Volatility** | How much prices jump around |
| **Sharpe Ratio** | Return divided by risk |
| **Drawdown** | Biggest drop from peak |
| **VaR** | Worst expected loss on bad day |
| **Regime** | Market "mood" (calm/stressed) |
| **Covariance** | How stocks move together |
| **Convex Optimization** | Math for finding best portfolio |
