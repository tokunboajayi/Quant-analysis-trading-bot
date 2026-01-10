# Model Registry & Promotion

## Structure
Models exist in `data/registry/` under 3 stages:
1.  **Candidates**: Trained models undergoing evaluation.
2.  **Staging**: Models passed initial gates, running in shadow mode.
3.  **Prod**: The live model used by `daily_runner`.

## Workflow
1.  **Train**: Produces a model artifact.
2.  **Register**:
    ```bash
    # (Internal API)
    reg.register_candidate(path, metrics, config)
    ```
3.  **List**:
    ```bash
    python -m riskfusion.cli registry list --stage candidates
    ```
4.  **Promote**:
    ```bash
    python -m riskfusion.cli registry promote --id <model_id> --to staging
    ```
    *Fail if gates (IC > 0.01) are not met.*

## Gates
Defined in `riskfusion.research.gates`.
- **Candidate Gate**: Mean IC > 0.01.
- **Prod Gate**: Mean IC > 0.015, No critical drift.
