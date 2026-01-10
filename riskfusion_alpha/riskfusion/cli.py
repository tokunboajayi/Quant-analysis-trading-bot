import argparse
import sys
from riskfusion.utils.logging import setup_logging
from riskfusion.config import get_config

def main():
    parser = argparse.ArgumentParser(description="RiskFusion Alpha CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest
    ingest_parser = subparsers.add_parser("ingest", help="Download Data")
    ingest_parser.add_argument("--start", help="Start date YYYY-MM-DD")
    ingest_parser.add_argument("--end", help="End date YYYY-MM-DD")
    
    # Feature Engineering (stub)
    feat_parser = subparsers.add_parser("features", help="Compute Features")
    
    # Train (stub)
    train_parser = subparsers.add_parser("train", help="Train Models")
    
    # Run Daily
    daily_parser = subparsers.add_parser("run_daily", help="Execute Daily Pipeline")
    daily_parser.add_argument("--date", help="Target date YYYY-MM-DD")

    # Backtest
    bt_parser = subparsers.add_parser("backtest", help="Run Backtest")
    bt_parser.add_argument("--start", help="Start date")
    bt_parser.add_argument("--end", help="End date")

    # Audit Status
    audit_parser = subparsers.add_parser("audit_status", help="Check Run Status")
    audit_parser.add_argument("--date", help="Date YYYY-MM-DD")
    
    
    # Snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Manage Data Snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snap_cmd")
    
    snap_create = snap_sub.add_parser("create", help="Create new snapshot from current features")
    snap_create.add_argument("--desc", help="Description", default="")
    
    snap_list = snap_sub.add_parser("list", help="List snapshots")
    
    snap_show = snap_sub.add_parser("show", help="Show snapshot details")
    snap_show.add_argument("id", help="Snapshot ID")

    # Walkforward
    wf_parser = subparsers.add_parser("walkforward", help="Run Walk-Forward Analysis")
    wf_parser.add_argument("--start_days", type=int, default=750)
    wf_parser.add_argument("--test_days", type=int, default=63)
    
    # Registry
    reg_parser = subparsers.add_parser("registry", help="Model Registry")
    reg_sub = reg_parser.add_subparsers(dest="reg_cmd")
    
    reg_list = reg_sub.add_parser("list", help="List models")
    reg_list.add_argument("--stage", default="candidates", choices=["candidates", "staging", "prod"])
    
    reg_promote = reg_sub.add_parser("promote", help="Promote model")
    reg_promote.add_argument("--id", required=True)
    reg_promote.add_argument("--to", required=True, choices=["staging", "prod"])

    # Validation
    val_parser = subparsers.add_parser("validate_research", help="Run Research Validation")
    val_parser.add_argument("--n_permutes", type=int, default=5)

    # Reporting
    rep_parser = subparsers.add_parser("report_paper", help="Generate Paper Report")
    rep_parser.add_argument("--run_id", required=True)
    rep_parser.add_argument("--snapshot_id", required=True)
    
    # HPO
    hpo_parser = subparsers.add_parser("hpo", help="Run Hyperparameter Optimization")
    hpo_parser.add_argument("--n_trials", type=int, default=10)

    # Ablation (Crazy Quant Ladder)
    abl_parser = subparsers.add_parser("ablation", help="Run Ablation Study (compare baseline vs steps)")
    abl_parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    abl_parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    abl_parser.add_argument("--steps", default="0,1", help="Comma-separated step numbers (e.g., 0,1,2)")

    args = parser.parse_args()
    
    setup_logging()
    
    if args.command == "ingest":
        from riskfusion.ingest.ingest_prices import ingest_prices
        from riskfusion.ingest.ingest_events import ingest_all_events
        print("Running Ingestion...")
        ingest_prices(args.start, args.end)
        ingest_all_events(args.start, args.end)
        print("Ingestion Complete.")
        
    elif args.command == "features":
        from riskfusion.features.build_features import build_features
        print("Building Features...")
        build_features()
        
    elif args.command == "train":
        from riskfusion.models.train import train_models
        print("Training Models...")
        train_models()

    elif args.command == "backtest":
        from riskfusion.backtest.engine import Backtester
        print("Running Backtest...")
        bt = Backtester(args.start, args.end)
        res = bt.run()
        print("Backtest Complete.")
        if res is not None:
             print(res.tail())
             res.to_csv("data/outputs/backtest_results.csv")
        
    elif args.command == "run_daily":
        from riskfusion.daily_runner import run_daily_pipeline
        print("Daily runner starting...")
        run_daily_pipeline(args.date if hasattr(args, 'date') else None)

    elif args.command == "audit_status":
        import pandas as pd
        from pathlib import Path
        config = get_config()
        out_path = Path(config.params['paths']['outputs'])
        
        date_str = args.date
        if not date_str:
            print("Please provide --date")
            return
            
        report = out_path / f"monitoring_report_{date_str}.md"
        if report.exists():
            print(f"--- Status for {date_str} ---")
            print(report.read_text(encoding='utf-8'))
        else:
            print(f"No report found for {date_str}")

    elif args.command == "snapshot":
        from riskfusion.research.snapshot import SnapshotManager
        from riskfusion.features.store import FeatureStore
        
        mgr = SnapshotManager()
        
        if args.snap_cmd == "create":
            store = FeatureStore()
            df = store.load_features()
            if df.empty:
                print("No features found to snapshot.")
                return
            sid = mgr.create_snapshot(df, args.desc)
            print(f"Snapshot created: {sid}")
            
        elif args.snap_cmd == "list":
            snaps = mgr.list_snapshots()
            for s in snaps:
                print(f"{s['id']} | {s['created_at']} | {s['description']}")
                
        elif args.snap_cmd == "show":
            meta = mgr.get_metadata(args.id)
            import json
            print(json.dumps(meta, indent=2))

    elif args.command == "walkforward":
        from riskfusion.research.walkforward import WalkForwardRunner
        from riskfusion.features.store import FeatureStore
        
        store = FeatureStore()
        df = store.load_features()
        if df.empty:
            print("No features.")
            return
            
        runner = WalkForwardRunner(df, initial_train_days=args.start_days, test_size_days=args.test_days)
        print("Starting Walk-Forward...")
        res = runner.run()
        print(res)


    elif args.command == "registry":
        from riskfusion.registry.registry import ModelRegistry
        from riskfusion.research.gates import QualityGates
        
        reg = ModelRegistry()
        
        if args.reg_cmd == "list":
            models = reg.list_models(args.stage)
            print(f"Models in {args.stage}:")
            for m in models:
                print(f" - {m}")
                
        elif args.reg_cmd == "promote":
            # Identify current stage? Simplified: promote works from candidates->staging or staging->prod
            # But here we just say from everything to Target.
            # Let's search where it is
            src_stage = None
            if args.to == "staging":
                src_stage = "candidates"
            elif args.to == "prod":
                src_stage = "staging"
                
            # Load Metrics
            import json
            from pathlib import Path
            # We need to know where the model is. reg.root / src_stage / args.id
            model_dir = reg.root / src_stage / args.id / "metrics.json"
            if not model_dir.exists():
                print("Error: No metrics.json found for model. Cannot verify gates.")
                return
                
            with open(model_dir, "r") as f:
                metrics = json.load(f)
                
            try:
                if args.to == "staging":
                    QualityGates.check_candidate_gates(metrics)
                    print("Candidate Gates Passed.")
                elif args.to == "prod":
                    QualityGates.check_production_gates(metrics)
                    print("Production Gates Passed.")
            except Exception as e:
                print(f"GATE MISTAKE: Promotion blocked. {e}")
                return

            print(f"Promoting {args.id} from {src_stage} to {args.to}...")
            reg.promote(args.id, src_stage, args.to)

    elif args.command == "validate_research":
        from riskfusion.research.validation_suite import ValidationSuite
        from riskfusion.features.store import FeatureStore
        
        store = FeatureStore()
        df = store.load_features()
        if df.empty:
            print("No features.")
            return
            
        print("Running Validation Suite...")
        res = ValidationSuite.permutation_test(df, n_permutes=args.n_permutes)
        print(res)

    elif args.command == "report_paper":
        from riskfusion.reporting.paper import PaperReportGenerator
        
        # Mock results loading (integration would load real backtest csv)
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2020-01-01", periods=252)
        df_res = pd.DataFrame({
            'returns': np.random.normal(0, 0.01, 252)
        }, index=dates)
        
        gen = PaperReportGenerator(args.run_id, args.snapshot_id)
        path = gen.generate(df_res)
        print(f"Report saved to: {path}")

    elif args.command == "hpo":
        from riskfusion.research.hpo import run_hpo
        best_params = run_hpo(n_trials=args.n_trials)
        print("Best Hyperparameters found:")
        print(best_params)

    elif args.command == "ablation":
        from riskfusion.research.ablation import run_ablation
        print(f"Running Ablation Study: steps={args.steps}, {args.start} to {args.end}")
        result = run_ablation(args.start, args.end, args.steps)
        print("\nAblation Results:")
        print(result.to_string(index=False))
        print("\nReport saved to data/outputs/")

if __name__ == "__main__":
    main()
