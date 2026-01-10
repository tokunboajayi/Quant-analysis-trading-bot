// shared/telemetry/types.ts
// TelemetryFrame v1.0 - The "CAN bus" contract

export type ExecutionMode = "PAPER" | "LIVE";
export type RegimeState = "clear" | "rain" | "storm";

export type PipelineStage =
  | "ingest_prices"
  | "ingest_events"
  | "build_features"
  | "predict"
  | "construct_portfolio"
  | "execute"
  | "report";

export type PipelineStatus = "ok" | "degraded" | "failed" | "stale";
export type StageStatus = "ok" | "running" | "failed" | "skipped";

export type WarningCode =
  | "VAR_CAP"
  | "EVENT_OVERLAY"
  | "DRIFT"
  | "DATA_DEGRADED"
  | "OVERTRADING"
  | "LIQUIDITY_FILTER"
  | "CLUSTER_CAP"
  | "META_FILTER"
  | "MODEL_GATE_FAILED"
  | "EXECUTION_REJECTS"
  | "LATENCY_SPIKE";

export type Direction = "up" | "down" | "unknown";

export interface Gauge {
  value: number;          // normalized 0..1
  raw?: number;           // actual raw metric
  unit?: string;          // e.g. "%", "bps", "$"
  trend_1d?: number;
  trend_5d?: number;
  confidence?: number;    // 0..1
}

export interface WarningItem {
  code: WarningCode;
  severity: 1 | 2 | 3;
  message?: string;
}

export interface ProviderHealth {
  name: string;
  status: "up" | "degraded" | "down";
  latency_ms?: number;
  error_rate_1h?: number;
  rate_limit_remaining?: number;
  last_success_ts?: string;
  message?: string;
}

export interface HazardEvent {
  id: string;
  ts_utc: string;
  ticker: string;
  source: string;
  kind: "headline" | "filing";
  title: string;
  direction: Direction;
  risk_prob: number;      // 0..1
  neg_prob?: number;      // 0..1
  impact_bucket?: "small" | "medium" | "large";
  eta_seconds: number;    // for animation
  features_date: string;
}

export interface WeightChange {
  ticker: string;
  weight_prev: number;
  weight_new: number;
  delta: number;
  reason_codes: WarningCode[];
}

export interface PortfolioFlowNode {
  id: string;
  label: string;
  weight: number;
  weight_change_1d?: number;
}

export interface PortfolioFlowEdge {
  from: string;
  to: string;
  value: number;
}

export interface PortfolioFlow {
  nodes: PortfolioFlowNode[];
  edges: PortfolioFlowEdge[];
  concentration_hhi?: number;
  max_cluster_exposure?: number;
}

export interface ModelHealth {
  name: string;
  stage: "prod" | "staging" | "candidate" | "none";
  status: "ok" | "degraded" | "failed";
  health: number;
  drift_psi?: number;
  calibration_error?: number;
  last_train_ts?: string;
  model_id?: string;
  message?: string;
}

export interface ExecutionSnapshot {
  alpaca_account_equity?: number;
  positions_count?: number;
  orders_open?: number;
  rejects_1d?: number;
  fills_1d?: number;
  est_slippage_bps_1d?: number;
  last_order_ts?: string;
}

export interface PnLStrip {
  equity: number;
  drawdown: number;
  return_1d?: number;
  return_5d?: number;
  return_mtd?: number;
  return_ytd?: number;
}

export interface TelemetryFrame {
  schema_version: "1.0";
  ts_utc: string;
  trading_date: string;
  execution_mode: ExecutionMode;

  // Pipeline
  pipeline_status: PipelineStatus;
  pipeline_last_run_ts?: string;
  pipeline_stage_status: Record<PipelineStage, StageStatus>;
  pipeline_latency_ms?: Record<PipelineStage, number>;
  pipeline_message?: string;

  // Car Gauges
  speed_alpha: Gauge;
  rpm_turnover: Gauge;
  traction_risk: Gauge;
  brake_var_pressure: Gauge;

  // Weather
  regime_state: RegimeState;
  regime_confidence?: number;

  // Warnings + Hazards
  warnings: WarningItem[];
  hazards: HazardEvent[];

  // Portfolio
  portfolio_flow: PortfolioFlow;
  top_weight_changes: WeightChange[];

  // Health
  models: ModelHealth[];
  providers: ProviderHealth[];

  // Execution
  execution: ExecutionSnapshot;
  pnl: PnLStrip;

  // Meta
  run_id?: string;
  config_hash?: string;
}
