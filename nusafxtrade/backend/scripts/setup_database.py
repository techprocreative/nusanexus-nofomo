#!/usr/bin/env python3
"""
Database Setup Script for NusaNexus NoFOMO
Automates the complete Supabase database setup process
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles database setup and migration execution"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize the database setup with Supabase client"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
    
    def get_migration_files(self) -> List[Path]:
        """Get all migration files sorted by name"""
        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            migration_files.append(file_path)
        return sorted(migration_files)
    
    async def execute_migration(self, file_path: Path) -> bool:
        """Execute a single migration file"""
        try:
            logger.info(f"Executing migration: {file_path.name}")
            
            # Read SQL content
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            # Execute each statement
            for statement in statements:
                if statement:
                    try:
                        self.supabase.rpc('execute_sql', {'sql': statement}).execute()
                        logger.debug(f"Statement executed: {statement[:100]}...")
                    except Exception as e:
                        # Some statements might fail (like extensions that already exist)
                        logger.warning(f"Statement failed (might be expected): {str(e)[:200]}")
            
            logger.info(f"✓ Migration completed: {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Migration failed: {file_path.name} - {str(e)}")
            return False
    
    async def verify_migration(self) -> bool:
        """Verify that the database schema is properly set up"""
        try:
            logger.info("Verifying database schema...")
            
            # Check if core tables exist
            tables_to_check = [
                'users', 'bots', 'strategies', 'trades', 'logs',
                'ai_analyses', 'backtest_results', 'plans', 'invoices', 'subscriptions'
            ]
            
            for table in tables_to_check:
                try:
                    self.supabase.table(table).select('id').limit(1).execute()
                    logger.info(f"✓ Table '{table}' exists")
                except Exception as e:
                    logger.error(f"✗ Table '{table}' missing or not accessible: {str(e)}")
                    return False
            
            logger.info("✓ Database verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            return False
    
    async def setup_database(self, skip_verification: bool = False) -> bool:
        """Setup the complete database schema"""
        logger.info("Starting database setup for NusaNexus NoFOMO...")
        
        # Get migration files
        migration_files = self.get_migration_files()
        if not migration_files:
            logger.error("No migration files found!")
            return False
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        # Execute migrations
        success_count = 0
        for migration_file in migration_files:
            if await self.execute_migration(migration_file):
                success_count += 1
            else:
                logger.error(f"Stopping execution due to failed migration: {migration_file.name}")
                return False
        
        logger.info(f"✓ Successfully executed {success_count}/{len(migration_files)} migrations")
        
        # Verify setup unless skipped
        if not skip_verification:
            if await self.verify_migration():
                logger.info("✓ Database setup completed successfully!")
                return True
            else:
                logger.error("✗ Database verification failed")
                return False
        else:
            logger.info("✓ Database setup completed (verification skipped)")
            return True


async def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Setup NusaNexus NoFOMO database')
    parser.add_argument('--skip-verification', action='store_true', 
                       help='Skip database verification after setup')
    parser.add_argument('--url', type=str, 
                       help='Supabase URL (overrides environment variable)')
    parser.add_argument('--key', type=str, 
                       help='Supabase anon key (overrides environment variable)')
    
    args = parser.parse_args()
    
    # Get Supabase credentials
    supabase_url = args.url or os.getenv('SUPABASE_URL')
    supabase_key = args.key or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables or use --url and --key arguments")
        logger.info("Example:")
        logger.info("  export SUPABASE_URL='https://your-project.supabase.co'")
        logger.info("  export SUPABASE_ANON_KEY='your-anon-key'")
        sys.exit(1)
    
    # Initialize and run setup
    db_setup = DatabaseSetup(supabase_url, supabase_key)
    
    success = await db_setup.setup_database(skip_verification=args.skip_verification)
    
    if success:
        logger.info("Database setup completed successfully! 🎉")
        logger.info("Next steps:")
        logger.info("1. Set up your Supabase project with the migration files")
        logger.info("2. Configure your application to use the new database schema")
        logger.info("3. Run the sample data migration if you want test data")
        sys.exit(0)
    else:
        logger.error("Database setup failed! ❌")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
