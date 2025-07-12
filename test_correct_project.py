#!/usr/bin/env python3

import os
import psycopg2
from dotenv import load_dotenv

def test_connection_and_setup():
    """Test connection and show database status"""
    load_dotenv()
    
    print("🔍 Testing Correct Supabase Project Connection")
    print("=" * 55)
    
    # Get connection string
    db_url = os.getenv('RECORD_MANAGER_DB_URL')
    if not db_url:
        print("❌ No RECORD_MANAGER_DB_URL found in .env")
        return False
    
    # Check if it's the correct project
    if 'baliloveagentchat' in db_url:
        print("✅ Connecting to correct project: baliloveagentchat")
    elif 'vhwmutruvmgetbnlatal' in db_url:
        print("❌ Still using old project: vhwmutruvmgetbnlatal")
        print("   Please update to baliloveagentchat connection string")
        return False
    else:
        print(f"⚠️  Unknown project in connection string")
    
    print(f"Connection format: {db_url[:50]}...")
    
    try:
        # Test connection
        print("\n🔄 Testing database connection...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Test basic connectivity
        cursor.execute("SELECT version();")
        version_result = cursor.fetchone()
        if version_result:
            version = version_result[0]
            print(f"✅ Database connection successful!")
            print(f"PostgreSQL version: {version[:60]}...")
        else:
            print("⚠️ Could not get database version")
        
        # Check for existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 Database Status:")
        print(f"Tables found: {len(tables)}")
        if tables:
            print("Existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  No tables found (fresh database)")
        
        # Check for langchain record manager table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'upsertion_record'
            );
        """)
        record_manager_result = cursor.fetchone()
        
        print(f"\n🔧 LangChain Integration:")
        if record_manager_result and record_manager_result[0]:
            print("✅ Record manager table exists")
        else:
            print("ℹ️  Record manager table not found (will be created on first use)")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Success! Your baliloveagentchat database is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed:")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection_and_setup() 