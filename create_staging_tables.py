"""Create Supabase staging tables using psycopg2"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Get database URL
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("DATABASE_URL not found in environment")
    exit(1)

# Read migration file
with open("supabase/migrations/003_data_staging_tables.sql", "r") as f:
    migration_sql = f.read()

try:
    # Connect to database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    print("Running migration to create staging tables...")
    
    # Execute migration
    cur.execute(migration_sql)
    
    # Commit changes
    conn.commit()
    
    print("Migration completed successfully!")
    
    # Verify tables were created
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('raw_data_staging', 'vector_sync_status', 'api_fetch_history')
    """)
    
    tables = cur.fetchall()
    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check view
    cur.execute("""
        SELECT viewname 
        FROM pg_views 
        WHERE schemaname = 'public' 
        AND viewname = 'ingestion_status'
    """)
    
    view = cur.fetchone()
    if view:
        print(f"  - {view[0]} (view)")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error running migration: {e}")
    import traceback
    traceback.print_exc()