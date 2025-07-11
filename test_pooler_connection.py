#!/usr/bin/env python3

import os
import psycopg2
from dotenv import load_dotenv

def test_connection(connection_string, connection_type):
    """Test a database connection"""
    print(f"\n🔄 Testing {connection_type} connection...")
    print(f"Connection string format: {connection_string[:50]}...")
    
    try:
        # Test connection
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Simple test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ {connection_type} connection successful!")
        print(f"PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ {connection_type} connection failed:")
        print(f"Error: {str(e)}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing Supabase Database Connections")
    print("=" * 50)
    
    # Get current connection string
    current_url = os.getenv('RECORD_MANAGER_DB_URL')
    if current_url:
        print(f"Current connection in .env: {current_url[:50]}...")
        
        # Test current connection
        test_connection(current_url, "Current (.env)")
    else:
        print("❌ No RECORD_MANAGER_DB_URL found in .env")
    
    print("\n" + "=" * 50)
    print("📝 To test Transaction Pooler:")
    print("1. Copy the Transaction Pooler connection string from Supabase")
    print("2. Replace [YOUR-PASSWORD] with your actual password")
    print("3. Update your .env file with the new connection string")
    print("4. Run this script again")
    
    print("\n💡 Transaction Pooler URL should look like:")
    print("postgresql://postgres.vhwmutruvmgetbnlat:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres")

if __name__ == "__main__":
    main() 