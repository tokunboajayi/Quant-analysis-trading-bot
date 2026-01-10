# Markdown Templates for RiskFusion Paper

PAPER_TEMPLATE = """
# {title}

**Run ID**: {run_id}  
**Date**: {date}

## 1. Abstract
{abstract}

## 2. Data
{data_section}

## 3. Feature Engineering
{features_section}

## 4. Models
{models_section}

## 5. Portfolio Construction
{portfolio_section}

## 6. Evaluation Protocol
{protocol_section}

## 7. Results
{results_section}

## 8. Ablation Study
{ablation_section}

## 9. Risk & Compliance Checks
{risk_section}

## 10. Limitations
{limitations_section}

## 11. Reproducibility Appendix
{repro_section}
"""

SECTION_DATA = """
- **Universe**: {universe_size} tickers ({universe_desc})
- **Date Range**: {start_date} to {end_date}
- **Sources**: 
  - Prices: {price_source}
  - News: {news_source}
- **Survivorship Bias**: {survivorship_statement}
"""

SECTION_RESULTS = """
### Performance Summary
| Metric | Strategy | Benchmark |
|:-------|:---------|:----------|
| CAGR | {cagr:.1%} | {bench_cagr:.1%} |
| Sharpe | {sharpe:.2f} | {bench_sharpe:.2f} |
| Max DD | {max_dd:.1%} | {bench_max_dd:.1%} |
| Volatility | {vol:.1%} | {bench_vol:.1%} |
| Turnover | {turnover:.2f} | - |

![Equity Curve]({plot_equity})
![Drawdown]({plot_drawdown})
![Rolling Vol]({plot_vol})
"""

SECTION_ABLATION = """
| Component | CAGR | Sharpe | Max DD |
|:----------|:-----|:-------|:-------|
| Alpha Only | {alpha_cagr:.1%} | {alpha_sharpe:.2f} | {alpha_dd:.1%} |
| + Risk | {risk_cagr:.1%} | {risk_sharpe:.2f} | {risk_dd:.1%} |
| + Event (Final) | {final_cagr:.1%} | {final_sharpe:.2f} | {final_dd:.1%} |
"""
