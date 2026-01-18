#!/usr/bin/env python3
"""
Quick script to verify routes are registered correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Checking imports...")
    from app.api import overshoot_test
    print(f"✅ overshoot_test module imported")
    print(f"   Router: {overshoot_test.router}")
    
    # Check routes
    routes = [route for route in overshoot_test.router.routes]
    print(f"\n📋 Routes found: {len(routes)}")
    for route in routes:
        print(f"   {route.methods} {route.path}")
    
    print("\n✅ Router is ready to be mounted!")
    print("\n💡 If you're still getting 404:")
    print("   1. Make sure the server was restarted after adding the router")
    print("   2. Check server logs for import errors")
    print("   3. Visit http://localhost:8000/docs to see all endpoints")
    
except Exception as e:
    print(f"❌ Error importing router: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
