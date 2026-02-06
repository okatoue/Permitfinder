#!/usr/bin/env python
"""
Database Setup Script for Permit Finder

This script helps you set up the PostgreSQL database for storing permit data.

Usage:
    python setup_db.py

Prerequisites:
    1. PostgreSQL must be installed and running
    2. You need a database user with permissions to create databases
    3. Set environment variables or update DB_CONFIG in database.py
"""

import os
import sys

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Error: psycopg2 is not installed.")
    print("Run: pip install psycopg2-binary")
    sys.exit(1)


def create_database():
    """Create the permits database if it doesn't exist"""

    # Connection settings for creating the database
    # Connect to the default 'postgres' database first
    admin_config = {
        'host': os.environ.get('PERMIT_DB_HOST', 'localhost'),
        'port': os.environ.get('PERMIT_DB_PORT', '5432'),
        'database': 'postgres',  # Connect to default database
        'user': os.environ.get('PERMIT_DB_USER', 'postgres'),
        'password': os.environ.get('PERMIT_DB_PASSWORD', ''),
    }

    db_name = os.environ.get('PERMIT_DB_NAME', 'permits')

    print(f"Connecting to PostgreSQL at {admin_config['host']}:{admin_config['port']}...")

    try:
        # Connect to postgres database to create our database
        conn = psycopg2.connect(**admin_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cur.fetchone()

        if exists:
            print(f"Database '{db_name}' already exists.")
        else:
            print(f"Creating database '{db_name}'...")
            cur.execute(f'CREATE DATABASE {db_name}')
            print(f"Database '{db_name}' created successfully!")

        cur.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        print(f"\nConnection Error: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is installed and running")
        print("  2. Your credentials are correct")
        print("  3. Set environment variables:")
        print("     PERMIT_DB_HOST (default: localhost)")
        print("     PERMIT_DB_PORT (default: 5432)")
        print("     PERMIT_DB_USER (default: postgres)")
        print("     PERMIT_DB_PASSWORD")
        print("     PERMIT_DB_NAME (default: permits)")
        return False


def init_schema():
    """Initialize the database schema"""

    from database import init_database

    print("\nInitializing database schema...")
    try:
        init_database()
        return True
    except Exception as e:
        print(f"Error initializing schema: {e}")
        return False


def verify_setup():
    """Verify the database setup by running a test query"""

    from database import get_connection

    print("\nVerifying database setup...")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Check if permits table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'permits'
            )
        """)
        table_exists = cur.fetchone()[0]

        if table_exists:
            # Get table info
            cur.execute("""
                SELECT COUNT(*) FROM permits
            """)
            count = cur.fetchone()[0]
            print(f"  permits table exists with {count} records")

            # Check indexes
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'permits'
            """)
            indexes = [row[0] for row in cur.fetchall()]
            print(f"  {len(indexes)} indexes created")

            # Check views
            cur.execute("""
                SELECT viewname FROM pg_views
                WHERE schemaname = 'public'
                AND viewname LIKE '%permits%'
            """)
            views = [row[0] for row in cur.fetchall()]
            print(f"  {len(views)} views created: {', '.join(views)}")

            cur.close()
            conn.close()
            return True
        else:
            print("  Error: permits table not found!")
            return False

    except Exception as e:
        print(f"  Verification error: {e}")
        return False


def main():
    """Main setup routine"""

    print("=" * 60)
    print("Permit Finder Database Setup")
    print("=" * 60)

    # Step 1: Create database
    print("\nStep 1: Create Database")
    print("-" * 40)
    if not create_database():
        print("\nSetup failed at database creation.")
        sys.exit(1)

    # Step 2: Initialize schema
    print("\nStep 2: Initialize Schema")
    print("-" * 40)
    if not init_schema():
        print("\nSetup failed at schema initialization.")
        sys.exit(1)

    # Step 3: Verify setup
    print("\nStep 3: Verify Setup")
    print("-" * 40)
    if not verify_setup():
        print("\nSetup verification failed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)
    print("\nYou can now run the scraper:")
    print("  python scraper.py")
    print("\nOr check database stats:")
    print("  python database.py stats")


if __name__ == '__main__':
    main()
