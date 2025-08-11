#!/usr/bin/env python3
"""
Setup script for Company Management System
"""

import os
import subprocess
import sys

def create_env_file():
    """Create .env file from template"""
    env_content = """# Database Configuration
PG_DSN=postgresql://postgres:postgres@localhost:5432/similarweb

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Similarweb Configuration (optional)
SIMILARWEB_BATCH_API_KEY=your_similarweb_batch_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("⚠️  Please edit .env file with your actual API keys")

def check_dependencies():
    """Check if required dependencies are installed"""
    required = ['psql', 'python3', 'pip']
    missing = []
    
    for dep in required:
        try:
            subprocess.run([dep, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(dep)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install the missing dependencies and run setup again")
        return False
    
    print("✅ All required dependencies found")
    return True

def install_python_deps():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def check_postgres():
    """Check PostgreSQL connection"""
    try:
        # Try to connect to PostgreSQL
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/similarweb")
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except ImportError:
        print("❌ psycopg2 not installed")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("Please ensure PostgreSQL is running and accessible")
        return False

def run_schema():
    """Run database schema"""
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/similarweb")
        
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        
        conn.commit()
        conn.close()
        print("✅ Database schema created")
        return True
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Company Management System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Install Python dependencies
    if not install_python_deps():
        return
    
    # Create .env file
    create_env_file()
    
    # Check PostgreSQL
    if not check_postgres():
        print("\n📋 Next steps:")
        print("1. Install and start PostgreSQL")
        print("2. Create database 'similarweb'")
        print("3. Install pgvector extension")
        print("4. Update .env file with your credentials")
        print("5. Run setup again")
        return
    
    # Run schema
    if not run_schema():
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your OpenAI API key")
    print("2. Run: python data_loader.py")
    print("3. Run: python company_management_api.py")
    print("4. Open web_interface.html in your browser")
    print("\n📚 See README.md for detailed instructions")

if __name__ == "__main__":
    main()
