"""
Incidents Routes - Anomaly detection and postmortems
"""
from fastapi import APIRouter
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
import json
import uuid

from pydantic import BaseModel

from app.settings import settings


router = APIRouter(prefix="/incidents", tags=["incidents"])

# Incident store path
INCIDENTS_DIR = Path("./data/incidents")


class Incident(BaseModel):
    id: str
    run_id: str
    opened_ts: str
    closed_ts: Optional[str] = None
    severity: int  # 1-3
    type: str  # PNL_SHOCK, DRAWDOWN_SPIKE, etc.
    metric_name: str
    observed_value: float
    expected_value: float
    threshold: float
    short_summary: str
    drivers: List[str] = []


@router.get("/index")
async def list_incidents(run_id: Optional[str] = None):
    """List incidents, optionally filtered by run_id."""
    incidents = []
    
    # Check for stored incidents
    if INCIDENTS_DIR.exists():
        for jsonl_file in INCIDENTS_DIR.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        inc = json.loads(line)
                        if run_id is None or inc.get("run_id") == run_id:
                            incidents.append(inc)
    
    # If no incidents found, return demo data
    if not incidents:
        incidents = [
            {
                "id": "inc_001",
                "run_id": "20260110",
                "opened_ts": "2026-01-10T10:30:00Z",
                "severity": 2,
                "type": "DRIFT_BREACH",
                "metric_name": "drift_psi",
                "observed_value": 1.29,
                "expected_value": 0.2,
                "threshold": 0.5,
                "short_summary": "High PSI on ret_1d, rsi features",
                "drivers": ["ret_1d PSI: 1.29", "rsi PSI: 2.82", "Market regime: STORM"],
            },
            {
                "id": "inc_002",
                "run_id": "20260109",
                "opened_ts": "2026-01-09T14:15:00Z",
                "closed_ts": "2026-01-09T15:00:00Z",
                "severity": 3,
                "type": "VAR_BREACH",
                "metric_name": "var_pressure",
                "observed_value": 0.92,
                "expected_value": 0.5,
                "threshold": 0.9,
                "short_summary": "VaR pressure exceeded threshold for 15 minutes",
                "drivers": ["Volatility spike in Tech sector", "NVDA position >5%"],
            },
        ]
    
    return {"incidents": sorted(incidents, key=lambda x: x.get("opened_ts", ""), reverse=True)}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get full incident details."""
    # Search for incident
    if INCIDENTS_DIR.exists():
        for jsonl_file in INCIDENTS_DIR.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        inc = json.loads(line)
                        if inc.get("id") == incident_id:
                            return inc
    
    # Return demo incident
    return {
        "id": incident_id,
        "run_id": "20260110",
        "opened_ts": "2026-01-10T10:30:00Z",
        "severity": 2,
        "type": "DRIFT_BREACH",
        "metric_name": "drift_psi",
        "observed_value": 1.29,
        "expected_value": 0.2,
        "threshold": 0.5,
        "short_summary": "High PSI on ret_1d, rsi features",
        "drivers": ["ret_1d PSI: 1.29", "rsi PSI: 2.82", "Market regime: STORM"],
        "context": {
            "top_weight_changes": [
                {"ticker": "NVDA", "delta": 0.01},
                {"ticker": "XOM", "delta": -0.007},
            ],
            "warnings": ["DRIFT", "VAR_CAP"],
        },
    }


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    """Get telemetry timestamps covering incident window."""
    # Would return frame timestamps from replay store
    return {
        "incident_id": incident_id,
        "start_ts": "2026-01-10T10:25:00Z",
        "end_ts": "2026-01-10T10:45:00Z",
        "frame_count": 40,
    }


@router.get("/{incident_id}/report.md")
async def get_incident_report(incident_id: str):
    """Generate markdown postmortem report."""
    inc = await get_incident(incident_id)
    
    report = f"""# Incident Postmortem: {inc['type']}

## Summary
{inc['short_summary']}

## Timeline
- **Opened**: {inc['opened_ts']}
- **Closed**: {inc.get('closed_ts', 'Ongoing')}
- **Severity**: {'🔴' * inc['severity']}{'⚪' * (3 - inc['severity'])}

## Impact
- **Metric**: {inc['metric_name']}
- **Observed**: {inc['observed_value']}
- **Expected**: {inc['expected_value']}
- **Threshold**: {inc['threshold']}
- **Deviation**: {((inc['observed_value'] / inc['expected_value'] - 1) * 100):.1f}%

## Root Cause Analysis
"""
    
    for i, driver in enumerate(inc.get('drivers', []), 1):
        report += f"{i}. {driver}\n"
    
    report += """
## Remediation
1. Monitor drift metrics more closely during volatile periods
2. Consider regime-aware feature normalization
3. Review PSI threshold for high-volatility features

## Follow-ups
- [ ] Retrain model with recent data
- [ ] Adjust PSI threshold configuration
- [ ] Add regime-based gating
"""
    
    return {"markdown": report}


@router.post("/create")
async def create_incident(incident: Incident):
    """Create a new incident (internal use)."""
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    incident_file = INCIDENTS_DIR / f"{incident.run_id}.jsonl"
    
    with open(incident_file, "a") as f:
        f.write(json.dumps(incident.dict()) + "\n")
    
    return {"status": "created", "id": incident.id}
