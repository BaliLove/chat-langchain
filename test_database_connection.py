#!/usr/bin/env python3
"""Test database connection with updated .env settings."""

import os
import sys
from urllib.parse import urlparse
import psycopg2

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ dotenv loaded successfully")
except ImportError:
    print("⚠️  dotenv not available, using system environment variables")

def print_env_template():
    """Print the .env file template."""
    print("""
=== .env File Template ===
Create a .env file in the root directory with the following format:

# Database Configuration (Transaction Pooler URL)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Bubble.io Configuration
BUBBLE_APP_URL=https://app.bali.love
BUBBLE_API_TOKEN=[YOUR_BUBBLE_API_TOKEN]

# AI/ML Configuration
OPENAI_API_KEY=[YOUR_OPENAI_API_KEY]
LANGSMITH_API_KEY=[YOUR_LANGSMITH_API_KEY]
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=bali-love-chat

# Pinecone Configuration
PINECONE_API_KEY=[YOUR_PINECONE_API_KEY]
PINECONE_INDEX_NAME=[YOUR_PINECONE_INDEX_NAME]

# Record Manager Database URL (same as DATABASE_URL)
RECORD_MANAGER_DB_URL=postgresql://postgres:[YOUR_PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

IMPORTANT FIXES:
1. Username should be just 'postgres' (not 'postgres.vhwmutruvmgetbnlatal')
2. Use Transaction Pooler URL: aws-0-us-west-1.pooler.supabase.com:6543
3. Replace [YOUR_PASSWORD] with your actual Supabase password
4. Replace [YOUR_BUBBLE_API_TOKEN] with your actual Bubble API token
5. Replace other [YOUR_*] placeholders with your actual values
""")

def test_database_connection():
    """Test the database connection with current environment variables."""
    print("=== Database Connection Test ===")
    
    # Check for database URL environment variable
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    print(f"✓ DATABASE_URL found")
    
    # Parse the URL
    try:
        parsed = urlparse(database_url)
        print(f"✓ Host: {parsed.hostname}")
        print(f"✓ Port: {parsed.port}")
        print(f"✓ Username: {parsed.username}")
        print(f"✓ Database: {parsed.path.lstrip('/')}")
        
        # Check if it's using the correct format
        if parsed.username != 'postgres':
            print(f"⚠️  Username should be 'postgres', but found '{parsed.username}'")
        
        if parsed.hostname and 'pooler.supabase.com' not in parsed.hostname:
            print(f"⚠️  Make sure you're using the transaction pooler URL")
            
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False
    
    # Test the connection
    try:
        print(f"\n📡 Testing database connection...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Simple test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        if version:
            print(f"✅ PostgreSQL version: {version[0]}")
        else:
            print("⚠️  Could not retrieve PostgreSQL version")
        
        # Test table existence
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("⚠️  No tables found in public schema")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_other_env_vars():
    """Check for other relevant environment variables."""
    print("\n=== Other Environment Variables ===")
    
    env_vars = [
        'BUBBLE_APP_URL',
        'BUBBLE_API_TOKEN', 
        'OPENAI_API_KEY',
            'LANGSMITH_API_KEY',
    'LANGSMITH_TRACING_V2',
    'LANGSMITH_PROJECT',
        'PINECONE_API_KEY',
        'PINECONE_INDEX_NAME',
        'RECORD_MANAGER_DB_URL'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var or 'TOKEN' in var:
                print(f"✓ {var}: {'*' * 8}...{value[-4:]}")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

if __name__ == "__main__":
    print("Testing database connection with updated .env settings...\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found in current directory")
        print_env_template()
        sys.exit(1)
    else:
        print("✓ .env file found")
    
    # Test database connection
    db_success = test_database_connection()
    
    # Check other environment variables
    check_other_env_vars()
    
    if db_success:
        print("\n🎉 Database connection test passed!")
        sys.exit(0)
    else:
        print("\n💥 Database connection test failed!")
        print("\nIf you need to create/update your .env file, here's the template:")
        print_env_template()
        sys.exit(1) 