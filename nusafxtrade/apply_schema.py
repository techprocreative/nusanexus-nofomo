#!/usr/bin/env python3
"""
Apply database schema to Supabase
"""

import os
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://pghkuuedtkgqdhkivrmg.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnaGt1dWVkdGtncWRoa2l2cm1nIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjczNzYwMSwiZXhwIjoyMDc4MzEzNjAxfQ.SnQ6xYUJj8I3a_EAtodv99aT32emkN56JXmXU8rAqns"

# Read SQL file
with open('deployment/database/schema.sql', 'r') as f:
    sql_content = f.read()

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("📦 Applying database schema to Supabase...")
print(f"🔗 URL: {SUPABASE_URL}")

# Split SQL into individual statements
statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

success_count = 0
error_count = 0

for i, statement in enumerate(statements, 1):
    if not statement:
        continue
    
    try:
        # Skip comments and empty lines
        if statement.startswith('--') or len(statement) < 10:
            continue
        
        print(f"\n[{i}/{len(statements)}] Executing statement...")
        print(f"Preview: {statement[:100]}...")
        
        # Execute via REST API (direct SQL execution)
        # Note: Supabase Python client doesn't support direct SQL execution
        # We'll use the PostgREST API with RPC
        
        # For now, let's try creating tables one by one
        # This is a workaround since Supabase client doesn't have execute_sql
        
        # Import to postgres using REST API
        import requests
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json"
            },
            json={"query": statement}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Success")
            success_count += 1
        else:
            print(f"⚠️  Warning: {response.status_code} - {response.text[:200]}")
            # Some statements might fail if already exist, continue anyway
            if "already exists" in response.text.lower():
                success_count += 1
            else:
                error_count += 1
            
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"ℹ️  Already exists, skipping...")
            success_count += 1
        else:
            print(f"❌ Error: {error_msg[:200]}")
            error_count += 1

print(f"\n{'='*60}")
print(f"✅ Success: {success_count}")
print(f"❌ Errors: {error_count}")
print(f"📊 Total: {len(statements)}")
print(f"{'='*60}")

if error_count == 0:
    print("\n🎉 Database schema applied successfully!")
else:
    print(f"\n⚠️  Completed with {error_count} errors (some might be expected)")
