#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

print("Testing individual module imports...")

# Test 1: Basic zzz_od import
try:
    import zzz_od
    print("✓ zzz_od imported successfully")
except Exception as e:
    print(f"❌ zzz_od import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: intelligent_decision package
try:
    import zzz_od.intelligent_decision
    print("✓ zzz_od.intelligent_decision imported successfully")
except Exception as e:
    print(f"❌ zzz_od.intelligent_decision import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Individual modules
modules_to_test = [
    'decision_engine',
    'strategy_manager', 
    'config_manager',
    'performance_monitor',
    'recognition_enhancer',
    'intelligent_operator'
]

for module_name in modules_to_test:
    try:
        module = __import__(f'zzz_od.intelligent_decision.{module_name}', fromlist=[module_name])
        print(f"✓ {module_name} imported successfully")
    except Exception as e:
        print(f"❌ {module_name} import failed: {e}")
        import traceback
        traceback.print_exc()
        print("---")

print("Import testing completed.")