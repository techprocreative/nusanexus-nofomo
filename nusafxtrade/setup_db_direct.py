#!/usr/bin/env python3
"""
Direct database setup using Supabase client
"""

from supabase import create_client, Client
import time

# Supabase credentials
SUPABASE_URL = "https://pghkuuedtkgqdhkivrmg.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnaGt1dWVkdGtncWRoa2l2cm1nIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjczNzYwMSwiZXhwIjoyMDc4MzEzNjAxfQ.SnQ6xYUJj8I3a_EAtodv99aT32emkN56JXmXU8rAqns"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("🚀 NusaNexus NoFOMO - Database Setup")
print("="*60)
print(f"📡 Connecting to: {SUPABASE_URL}")
print()

# Test connection
print("1️⃣  Testing connection...")
try:
    # Try to query auth.users (should exist in all Supabase projects)
    result = supabase.table('_realtime').select('*').limit(1).execute()
    print("   ✅ Connection successful!")
except Exception as e:
    print(f"   ⚠️  Connection test failed (might be OK): {str(e)[:100]}")

print()
print("2️⃣  Checking existing tables...")

# Function to check if table exists
def table_exists(table_name):
    try:
        supabase.table(table_name).select('id').limit(1).execute()
        return True
    except Exception as e:
        if "does not exist" in str(e).lower() or "relation" in str(e).lower():
            return False
        return False

tables_to_check = ['users', 'bots', 'strategies', 'trades', 'backtest_results', 
                   'ai_analyses', 'logs', 'plans', 'subscriptions', 'invoices']

existing_tables = []
missing_tables = []

for table in tables_to_check:
    exists = table_exists(table)
    if exists:
        print(f"   ✅ Table '{table}' exists")
        existing_tables.append(table)
    else:
        print(f"   ❌ Table '{table}' missing")
        missing_tables.append(table)

print()
print(f"📊 Summary:")
print(f"   Existing: {len(existing_tables)}/{len(tables_to_check)}")
print(f"   Missing: {len(missing_tables)}/{len(tables_to_check)}")
print()

if missing_tables:
    print("⚠️  Missing tables detected!")
    print()
    print("📝 To create tables, you have 3 options:")
    print()
    print("Option 1: Via Supabase Dashboard (SQL Editor)")
    print("   1. Go to: https://supabase.com/dashboard/project/pghkuuedtkgqdhkivrmg/sql/new")
    print("   2. Copy contents from: deployment/database/schema.sql")
    print("   3. Click 'Run' to execute")
    print()
    print("Option 2: Via Supabase CLI (requires psql)")
    print("   supabase db reset --linked")
    print()
    print("Option 3: Manual table creation via REST API")
    print("   (Will be implemented in next version)")
    print()
    
    # Try to access SQL editor URL
    sql_editor_url = f"https://supabase.com/dashboard/project/pghkuuedtkgqdhkivrmg/sql/new"
    print(f"🔗 Quick Link: {sql_editor_url}")
else:
    print("✅ All tables exist!")
    print()
    print("3️⃣  Seeding initial data...")
    
    # Check if plans exist
    try:
        plans = supabase.table('plans').select('*').execute()
        if len(plans.data) == 0:
            print("   📦 Inserting default plans...")
            
            default_plans = [
                {
                    "name": "Free",
                    "description": "Start trading with basic features",
                    "price": 0,
                    "billing_cycle": "monthly",
                    "features": {"bots": 1, "strategies": 3, "ai_credits": 10, "support": "community"},
                    "limits": {"max_bots": 1, "max_strategies": 3, "max_trades_per_day": 50, "ai_generations_per_month": 10},
                    "is_active": True
                },
                {
                    "name": "Pro",
                    "description": "Advanced trading with AI features",
                    "price": 299000,
                    "billing_cycle": "monthly",
                    "features": {"bots": 5, "strategies": "unlimited", "ai_credits": 100, "support": "email", "backtest": True},
                    "limits": {"max_bots": 5, "max_strategies": 999, "max_trades_per_day": 500, "ai_generations_per_month": 100},
                    "is_active": True
                },
                {
                    "name": "Enterprise",
                    "description": "Full access with priority support",
                    "price": 999000,
                    "billing_cycle": "monthly",
                    "features": {"bots": "unlimited", "strategies": "unlimited", "ai_credits": "unlimited", "support": "priority", "backtest": True, "custom_strategies": True},
                    "limits": {"max_bots": 999, "max_strategies": 999, "max_trades_per_day": 9999, "ai_generations_per_month": 999},
                    "is_active": True
                }
            ]
            
            for plan in default_plans:
                try:
                    supabase.table('plans').insert(plan).execute()
                    print(f"   ✅ Plan '{plan['name']}' created")
                except Exception as e:
                    if "duplicate" in str(e).lower():
                        print(f"   ℹ️  Plan '{plan['name']}' already exists")
                    else:
                        print(f"   ❌ Error creating plan '{plan['name']}': {str(e)[:100]}")
        else:
            print(f"   ℹ️  Plans already seeded ({len(plans.data)} plans found)")
    except Exception as e:
        print(f"   ⚠️  Could not seed plans: {str(e)[:100]}")

print()
print("="*60)
print("✅ Database setup check complete!")
print()
