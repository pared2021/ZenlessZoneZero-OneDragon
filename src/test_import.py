#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback

try:
    print("Testing import of zzz_od.intelligent_decision.strategy_manager...")
    import zzz_od.intelligent_decision.strategy_manager
    print("Import successful!")
except Exception as e:
    print(f"Import error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
try:
    print("\nTesting import of zzz_od.intelligent_decision.decision_engine...")
    import zzz_od.intelligent_decision.decision_engine
    print("Import successful!")
except Exception as e:
    print(f"Import error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()