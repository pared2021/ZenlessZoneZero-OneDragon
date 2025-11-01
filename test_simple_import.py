#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的导入测试
"""

import sys
import os

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

print(f"Project root: {project_root}")
print(f"Src path: {src_path}")
print(f"Src path exists: {os.path.exists(src_path)}")

try:
    print("Testing zzz_od import...")
    import zzz_od
    print("✓ zzz_od imported successfully")
    
    print("Testing intelligent_decision import...")
    import zzz_od.intelligent_decision
    print("✓ zzz_od.intelligent_decision imported successfully")
    
    print("Testing decision_engine import...")
    from zzz_od.intelligent_decision.decision_engine import DecisionEngine, DecisionState, DecisionContext
    print("✓ DecisionEngine classes imported successfully")
    
    print("Testing DecisionEngine instantiation...")
    engine = DecisionEngine("test_engine")
    print(f"✓ DecisionEngine created: {engine.engine_id}")
    
    print("Testing DecisionEngine methods...")
    state = engine.get_state()
    print(f"✓ Engine state: {state}")
    
    print("\n🎉 All tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)