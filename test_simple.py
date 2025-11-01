#!/usr/bin/env python3

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing individual module imports...")

# Test basic zzz_od import without intelligent_decision
try:
    import zzz_od
    print("✓ zzz_od base package imported")
except Exception as e:
    print(f"❌ zzz_od base package failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test individual modules directly
modules_to_test = [
    'zzz_od.intelligent_decision.strategy_manager',
    'zzz_od.intelligent_decision.decision_engine',
    'zzz_od.intelligent_decision.config_manager',
    'zzz_od.intelligent_decision.performance_monitor',
    'zzz_od.intelligent_decision.recognition_enhancer',
    'zzz_od.intelligent_decision.intelligent_operator'
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {module_name} imported successfully")
    except Exception as e:
        print(f"❌ {module_name} failed: {e}")
        import traceback
        traceback.print_exc()
        print()

print("\nModule import test completed.")