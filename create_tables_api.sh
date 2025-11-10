#!/bin/bash

# Supabase credentials
SUPABASE_URL="https://pghkuuedtkgqdhkivrmg.supabase.co"
SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnaGt1dWVkdGtncWRoa2l2cm1nIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjczNzYwMSwiZXhwIjoyMDc4MzEzNjAxfQ.SnQ6xYUJj8I3a_EAtodv99aT32emkN56JXmXU8rAqns"

echo "🚀 Creating database tables via Supabase API..."
echo "================================================"

# Read the SQL file
SQL_FILE="deployment/database/schema.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found!"
    exit 1
fi

echo "📄 Reading SQL file: $SQL_FILE"
echo ""

# Execute SQL via Supabase API
# Note: We need to use the SQL Editor API or PostgREST
# For now, let's provide instructions to use the dashboard

echo "📝 INSTRUCTIONS TO CREATE TABLES:"
echo "================================================"
echo ""
echo "The SQL schema is ready in: $SQL_FILE"
echo ""
echo "To apply the schema, please follow these steps:"
echo ""
echo "1. Open Supabase SQL Editor:"
echo "   https://supabase.com/dashboard/project/pghkuuedtkgqdhkivrmg/sql/new"
echo ""
echo "2. Copy the contents from:"
echo "   $PWD/$SQL_FILE"
echo ""
echo "3. Paste into SQL Editor and click 'Run'"
echo ""
echo "================================================"
echo ""
echo "⏱️  Alternative: Use this command if you have postgres installed:"
echo ""
echo "PGPASSWORD='<your-db-password>' psql -h db.pghkuuedtkgqdhkivrmg.supabase.co -U postgres -d postgres -f $SQL_FILE"
echo ""
echo "You can find your database password in:"
echo "https://supabase.com/dashboard/project/pghkuuedtkgqdhkivrmg/settings/database"
echo ""
