"""
Pydantic models for TelemetryFrame v1.0
======================================
Backend validation + serialization
"""
from __future__ import annotations
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict

ExecutionMode = Literal["PAPER", "LIVE"]
RegimeState = Literal["clear", "rain", "storm"]
PipelineStage = Literal[
    "ingest_prices", "ingest_events", "build_features",
    "predict", "construct_portfolio", "execute", "report"
]
PipelineStatus = Literal["ok", "degraded", "failed", "stale"]
StageStatus = Literal["ok", "running", "failed", "skipped"]
WarningCode = Literal[
    "VAR_CAP", "EVENT_OVERLAY", "DRIFT", "DATA_DEGRADED",
    "OVERTRADING", "LIQUIDITY_FILTER", "CLUSTER_CAP",
    "META_FILTER", "MODEL_GATE_FAILED", "EXECUTION_REJECTS", "LATENCY_SPIKE"
]
Direction = Literal["up", "down", "unknown"]


class Gauge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float = Field(ge=0.0, le=1.0)
    raw: Optional[float] = None
    unit: Optional[str] = None
    trend_1d: Optional[float] = None
    trend_5d: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class WarningItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: WarningCode
    severity: Literal[1, 2, 3]
    message: Optional[str] = None


class ProviderHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    status: Literal["up", "degraded", "down"]
    latency_ms: Optional[float] = Field(default=None, ge=0.0)
    error_rate_1h: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rate_limit_remaining: Optional[float] = Field(default=None, ge=0.0)
    last_success_ts: Optional[str] = None
    message: Optional[str] = None


class HazardEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    ts_utc: str
    ticker: str
    source: str
    kind: Literal["headline", "filing"]
    title: str
    direction: Direction
    risk_prob: float = Field(ge=0.0, le=1.0)
    neg_prob: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    impact_bucket: Optional[Literal["small", "medium", "large"]] = None
    eta_seconds: float = Field(ge=0.0)
    features_date: str


class WeightChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str
    weight_prev: float
    weight_new: float
    delta: float
    reason_codes: List[WarningCode]


class PortfolioFlowNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    weight: float = Field(ge=0.0, le=1.0)
    weight_change_1d: Optional[float] = None


class PortfolioFlowEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_node: str = Field(alias="from")
    to: str
    value: float = Field(ge=0.0, le=1.0)


class PortfolioFlow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodes: List[PortfolioFlowNode]
    edges: List[PortfolioFlowEdge]
    concentration_hhi: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_cluster_exposure: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ModelHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    stage: Literal["prod", "staging", "candidate", "none"]
    status: Literal["ok", "degraded", "failed"]
    health: float = Field(ge=0.0, le=1.0)
    drift_psi: Optional[float] = None
    calibration_error: Optional[float] = None
    last_train_ts: Optional[str] = None
    model_id: Optional[str] = None
    message: Optional[str] = None


class ExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alpaca_account_equity: Optional[float] = None
    positions_count: Optional[int] = Field(default=None, ge=0)
    orders_open: Optional[int] = Field(default=None, ge=0)
    rejects_1d: Optional[int] = Field(default=None, ge=0)
    fills_1d: Optional[int] = Field(default=None, ge=0)
    est_slippage_bps_1d: Optional[float] = None
    last_order_ts: Optional[str] = None


class PnLStrip(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equity: float
    drawdown: float
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    return_mtd: Optional[float] = None
    return_ytd: Optional[float] = None


class TelemetryFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    ts_utc: str
    trading_date: str
    execution_mode: ExecutionMode

    pipeline_status: PipelineStatus
    pipeline_last_run_ts: Optional[str] = None
    pipeline_stage_status: Dict[PipelineStage, StageStatus]
    pipeline_latency_ms: Optional[Dict[PipelineStage, float]] = None
    pipeline_message: Optional[str] = None

    speed_alpha: Gauge
    rpm_turnover: Gauge
    traction_risk: Gauge
    brake_var_pressure: Gauge

    regime_state: RegimeState
    regime_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    warnings: List[WarningItem]
    hazards: List[HazardEvent]

    portfolio_flow: PortfolioFlow
    top_weight_changes: List[WeightChange]

    models: List[ModelHealth]
    providers: List[ProviderHealth]

    execution: ExecutionSnapshot
    pnl: PnLStrip

    run_id: Optional[str] = None
    config_hash: Optional[str] = None
