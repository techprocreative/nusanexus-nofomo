#!/usr/bin/env python3
"""Verify database tables were created successfully"""

import sys
sys.path.append('backend')

from app.core.database import get_db_client
from app.core.config import settings

print("🔍 Verifying Database Setup...")
print("="*60)

try:
    db_client = get_db_client()
    
    tables_to_check = [
        'users', 'bots', 'strategies', 'trades', 
        'backtest_results', 'ai_analyses', 'logs', 
        'plans', 'subscriptions', 'invoices'
    ]
    
    print(f"📡 Connected to: {settings.supabase_url}")
    print()
    
    existing = []
    missing = []
    
    for table in tables_to_check:
        try:
            result = db_client.client.table(table).select('id').limit(1).execute()
            print(f"✅ Table '{table}' exists")
            existing.append(table)
        except Exception as e:
            if "does not exist" in str(e).lower():
                print(f"❌ Table '{table}' missing")
                missing.append(table)
            else:
                print(f"⚠️  Table '{table}' - {str(e)[:100]}")
    
    print()
    print("="*60)
    print(f"📊 Results:")
    print(f"   ✅ Existing: {len(existing)}/{len(tables_to_check)}")
    print(f"   ❌ Missing: {len(missing)}/{len(tables_to_check)}")
    
    if len(existing) == len(tables_to_check):
        print()
        print("🎉 SUCCESS! All tables created successfully!")
        print()
        
        # Check if plans were seeded
        try:
            plans = db_client.client.table('plans').select('*').execute()
            print(f"📦 Default plans seeded: {len(plans.data)} plans")
            for plan in plans.data:
                print(f"   - {plan['name']}: Rp {plan['price']:,.0f}/{plan['billing_cycle']}")
        except:
            print("⚠️  Plans table empty (need to seed)")
        
        print()
        print("✅ Database ready for use!")
        sys.exit(0)
    else:
        print()
        print(f"❌ ERROR: {len(missing)} tables missing!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
