"""
Crazy Quant Ladder - Full Verification Script
==============================================
Checks all components are properly implemented.
"""
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path

def check_files():
    """Verify all required files exist."""
    print("=" * 60)
    print("1. FILE VERIFICATION")
    print("=" * 60)
    
    required_files = {
        # PR1: Distributional Alpha
        "riskfusion/models/alpha_quantiles.py": "PR1",
        "tests/test_alpha_quantiles.py": "PR1",
        "docs/step1_distributional_alpha.md": "PR1",
        
        # PR2: Meta-Labeler
        "riskfusion/labeling/meta_labels.py": "PR2",
        "riskfusion/models/meta_labeler.py": "PR2",
        "tests/test_meta_labeler.py": "PR2",
        "docs/step2_meta_labeler.md": "PR2",
        
        # PR3: CVXPY Optimizer
        "riskfusion/portfolio/covariance.py": "PR3",
        "riskfusion/portfolio/optimizer_cvxpy.py": "PR3",
        "tests/test_optimizer_cvxpy.py": "PR3",
        "docs/step3_cvxpy_optimizer.md": "PR3",
        
        # PR4: Graph/Cluster
        "riskfusion/features/graph_features.py": "PR4",
        "riskfusion/portfolio/cluster_caps.py": "PR4",
        "tests/test_graph_cluster.py": "PR4",
        "docs/step4_graph_cluster.md": "PR4",
        
        # PR5: Multi-Task Event
        "riskfusion/models/event_risk_multitask.py": "PR5",
        "tests/test_event_multitask.py": "PR5",
        "docs/step5_event_multitask.md": "PR5",
        
        # PR6: Regime
        "riskfusion/models/regime_model.py": "PR6",
        "riskfusion/portfolio/strategy_selector.py": "PR6",
        "tests/test_regime.py": "PR6",
        "docs/step6_regime_switching.md": "PR6",
        
        # PR7: Online Learning
        "riskfusion/research/online_learning.py": "PR7",
        "tests/test_online_learning.py": "PR7",
        "docs/step7_online_learning.md": "PR7",
        
        # Shared
        "docs/crazy_quant_ladder.md": "ALL",
        "riskfusion/research/ablation.py": "ALL",
    }
    
    missing = []
    for file, pr in required_files.items():
        path = Path(file)
        if path.exists():
            print(f"  ✅ [{pr}] {file}")
        else:
            print(f"  ❌ [{pr}] {file} MISSING")
            missing.append(file)
    
    print(f"\nTotal: {len(required_files) - len(missing)}/{len(required_files)} files present")
    return len(missing) == 0

def check_config():
    """Verify config flags exist."""
    print("\n" + "=" * 60)
    print("2. CONFIG FLAGS")
    print("=" * 60)
    
    import yaml
    with open("configs/default.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    flags = [
        ("alpha.use_quantiles", config.get('alpha', {}).get('use_quantiles')),
        ("meta.enabled", config.get('meta', {}).get('enabled')),
        ("optimizer.method", config.get('optimizer', {}).get('method')),
        ("graph.enabled", config.get('graph', {}).get('enabled')),
        ("event.multitask", config.get('event', {}).get('multitask')),
        ("regime.enabled", config.get('regime', {}).get('enabled')),
        ("online_learning.enabled", config.get('online_learning', {}).get('enabled')),
    ]
    
    all_present = True
    for flag, value in flags:
        if value is not None:
            print(f"  ✅ {flag}: {value}")
        else:
            print(f"  ❌ {flag}: MISSING")
            all_present = False
    
    return all_present

def check_imports():
    """Verify all modules can be imported."""
    print("\n" + "=" * 60)
    print("3. IMPORT VERIFICATION")
    print("=" * 60)
    
    modules = [
        "riskfusion.models.alpha_quantiles",
        "riskfusion.models.meta_labeler",
        "riskfusion.models.event_risk_multitask",
        "riskfusion.models.regime_model",
        "riskfusion.labeling.meta_labels",
        "riskfusion.portfolio.covariance",
        "riskfusion.portfolio.optimizer_cvxpy",
        "riskfusion.portfolio.cluster_caps",
        "riskfusion.portfolio.strategy_selector",
        "riskfusion.features.graph_features",
        "riskfusion.research.online_learning",
        "riskfusion.research.ablation",
    ]
    
    import importlib
    all_ok = True
    for mod in modules:
        try:
            importlib.import_module(mod)
            print(f"  ✅ {mod}")
        except Exception as e:
            print(f"  ❌ {mod}: {e}")
            all_ok = False
    
    return all_ok

def check_feature_flags():
    """Verify feature flag functions work."""
    print("\n" + "=" * 60)
    print("4. FEATURE FLAG FUNCTIONS")
    print("=" * 60)
    
    from riskfusion.models.alpha_quantiles import is_quantiles_enabled
    from riskfusion.models.meta_labeler import is_meta_enabled
    from riskfusion.portfolio.optimizer_cvxpy import is_cvxpy_enabled
    from riskfusion.features.graph_features import is_graph_enabled
    from riskfusion.models.event_risk_multitask import is_multitask_enabled
    from riskfusion.models.regime_model import is_regime_enabled
    from riskfusion.research.online_learning import is_online_learning_enabled
    
    flags = [
        ("is_quantiles_enabled()", is_quantiles_enabled()),
        ("is_meta_enabled()", is_meta_enabled()),
        ("is_cvxpy_enabled()", is_cvxpy_enabled()),
        ("is_graph_enabled()", is_graph_enabled()),
        ("is_multitask_enabled()", is_multitask_enabled()),
        ("is_regime_enabled()", is_regime_enabled()),
        ("is_online_learning_enabled()", is_online_learning_enabled()),
    ]
    
    print("  All flags should be FALSE (default):")
    all_false = True
    for name, value in flags:
        status = "✅" if value == False else "⚠️"
        print(f"  {status} {name} = {value}")
        if value != False:
            all_false = False
    
    return all_false

def main():
    print("\n" + "=" * 60)
    print("    CRAZY QUANT LADDER - FULL VERIFICATION")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Files", check_files()))
    results.append(("Config", check_config()))
    results.append(("Imports", check_imports()))
    results.append(("Feature Flags", check_feature_flags()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
    else:
        print("⚠️ SOME VERIFICATIONS FAILED - SEE ABOVE")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
