"""
Database module for Permit Finder
Handles PostgreSQL connection and permit data operations
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json, execute_values

# Load environment variables from .env file in the same directory as this script
_script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_script_dir, '.env'))


# Database configuration - can be overridden by environment variables
DB_CONFIG = {
    'host': os.environ.get('PERMIT_DB_HOST', 'localhost'),
    'port': os.environ.get('PERMIT_DB_PORT', '5432'),
    'database': os.environ.get('PERMIT_DB_NAME', 'permits'),
    'user': os.environ.get('PERMIT_DB_USER', 'postgres'),
    'password': os.environ.get('PERMIT_DB_PASSWORD', ''),
}

# Core fields that are stored as dedicated columns
CORE_FIELDS = {
    'permit_number',
    'permit_type',
    'status',
    'list_status',
    'application_date',
    'issue_date',
    'completed_date',
    'list_created_date',
    'list_issue_date',
    'list_completed_date',
    'primary_location',
    'specific_location',
    'list_location',
    'parcel_id',
    'parcel_address',
    'folio_number',
    'work_description',
    'type_of_work',
    'contractors',
    'url',
    'source_city',
}


def get_connection():
    """Get a database connection using the configured settings"""
    return psycopg2.connect(**DB_CONFIG)


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse a date string in various formats to ISO format (YYYY-MM-DD)

    Handles formats like:
    - "Feb 01, 2026"
    - "Feb, 01, 2026"
    - "2026-02-01"
    """
    if not date_str or date_str.strip() == '' or date_str == '(None)':
        return None

    date_str = date_str.strip()

    # Try ISO format first
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        pass

    # Try "Mon dd, yyyy" format (e.g., "Feb 01, 2026")
    try:
        dt = datetime.strptime(date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Try "Mon, dd, yyyy" format (e.g., "Feb, 01, 2026")
    try:
        dt = datetime.strptime(date_str, '%b, %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Try other common formats
    formats = [
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%B %d, %Y',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    # If all parsing fails, return None
    print(f"Warning: Could not parse date '{date_str}'")
    return None


def prepare_permit_data(permit: Dict) -> tuple:
    """
    Prepare permit data for database insertion

    Separates core fields from type-specific fields,
    parses dates, and returns a tuple ready for insertion.
    """
    # Extract core fields
    core_data = {}
    type_specific = {}

    for key, value in permit.items():
        if key in CORE_FIELDS:
            core_data[key] = value
        else:
            # Store in type_specific_data JSONB column
            if value and value != '(None)':
                type_specific[key] = value

    # Parse date fields
    date_fields = [
        'application_date', 'issue_date', 'completed_date',
        'list_created_date', 'list_issue_date', 'list_completed_date'
    ]

    for field in date_fields:
        if field in core_data:
            core_data[field] = parse_date(core_data.get(field))

    return core_data, type_specific


def insert_permit(conn, permit: Dict) -> Optional[int]:
    """
    Insert a single permit into the database

    Returns the ID of the inserted permit, or None if insert failed.
    Uses ON CONFLICT to handle duplicates (updates existing record).
    """
    core_data, type_specific = prepare_permit_data(permit)

    sql = """
        INSERT INTO permits (
            permit_number, permit_type, status, list_status,
            application_date, issue_date, completed_date,
            list_created_date, list_issue_date, list_completed_date,
            primary_location, specific_location, list_location,
            parcel_id, parcel_address, folio_number,
            work_description, type_of_work, contractors, url,
            source_city, type_specific_data
        ) VALUES (
            %(permit_number)s, %(permit_type)s, %(status)s, %(list_status)s,
            %(application_date)s, %(issue_date)s, %(completed_date)s,
            %(list_created_date)s, %(list_issue_date)s, %(list_completed_date)s,
            %(primary_location)s, %(specific_location)s, %(list_location)s,
            %(parcel_id)s, %(parcel_address)s, %(folio_number)s,
            %(work_description)s, %(type_of_work)s, %(contractors)s, %(url)s,
            %(source_city)s, %(type_specific_data)s
        )
        ON CONFLICT (permit_number) DO UPDATE SET
            permit_type = EXCLUDED.permit_type,
            status = EXCLUDED.status,
            list_status = EXCLUDED.list_status,
            application_date = EXCLUDED.application_date,
            issue_date = EXCLUDED.issue_date,
            completed_date = EXCLUDED.completed_date,
            list_created_date = EXCLUDED.list_created_date,
            list_issue_date = EXCLUDED.list_issue_date,
            list_completed_date = EXCLUDED.list_completed_date,
            primary_location = EXCLUDED.primary_location,
            specific_location = EXCLUDED.specific_location,
            list_location = EXCLUDED.list_location,
            parcel_id = EXCLUDED.parcel_id,
            parcel_address = EXCLUDED.parcel_address,
            folio_number = EXCLUDED.folio_number,
            work_description = EXCLUDED.work_description,
            type_of_work = EXCLUDED.type_of_work,
            contractors = EXCLUDED.contractors,
            url = EXCLUDED.url,
            source_city = EXCLUDED.source_city,
            type_specific_data = EXCLUDED.type_specific_data,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
    """

    # Build params dict with all fields
    params = {
        'permit_number': core_data.get('permit_number'),
        'permit_type': core_data.get('permit_type'),
        'status': core_data.get('status'),
        'list_status': core_data.get('list_status'),
        'application_date': core_data.get('application_date'),
        'issue_date': core_data.get('issue_date'),
        'completed_date': core_data.get('completed_date'),
        'list_created_date': core_data.get('list_created_date'),
        'list_issue_date': core_data.get('list_issue_date'),
        'list_completed_date': core_data.get('list_completed_date'),
        'primary_location': core_data.get('primary_location'),
        'specific_location': core_data.get('specific_location'),
        'list_location': core_data.get('list_location'),
        'parcel_id': core_data.get('parcel_id'),
        'parcel_address': core_data.get('parcel_address'),
        'folio_number': core_data.get('folio_number'),
        'work_description': core_data.get('work_description'),
        'type_of_work': core_data.get('type_of_work'),
        'contractors': core_data.get('contractors'),
        'url': core_data.get('url'),
        'source_city': core_data.get('source_city', 'Vancouver'),
        'type_specific_data': Json(type_specific) if type_specific else Json({}),
    }

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error inserting permit {params.get('permit_number')}: {e}")
        conn.rollback()
        return None


def insert_permits_batch(conn, permits: List[Dict]) -> int:
    """
    Insert multiple permits in a batch

    Returns the number of successfully inserted permits.
    """
    inserted_count = 0

    for permit in permits:
        permit_id = insert_permit(conn, permit)
        if permit_id:
            inserted_count += 1

    conn.commit()
    return inserted_count


def save_permits_to_db(permits_by_type: Dict[str, List[Dict]]) -> Dict[str, int]:
    """
    Save all permits to the database, organized by type

    Returns a dict mapping permit type to count of inserted permits.
    """
    results = {}

    try:
        conn = get_connection()

        for permit_type, permits in permits_by_type.items():
            if not permits:
                continue

            print(f"  Saving {len(permits)} {permit_type}s to database...")
            count = insert_permits_batch(conn, permits)
            results[permit_type] = count
            print(f"  Saved {count} {permit_type}s")

        conn.close()

    except Exception as e:
        print(f"Database error: {e}")
        raise

    return results


def get_permits_by_type(permit_type: str, limit: int = 100) -> List[Dict]:
    """Retrieve permits of a specific type from the database"""
    conn = get_connection()

    sql = """
        SELECT
            id, permit_number, permit_type, status, list_status,
            application_date, issue_date, completed_date,
            primary_location, specific_location, work_description,
            contractors, url, type_specific_data, scraped_at
        FROM permits
        WHERE permit_type = %s
        ORDER BY scraped_at DESC
        LIMIT %s
    """

    try:
        with conn.cursor() as cur:
            cur.execute(sql, (permit_type, limit))
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                permit = dict(zip(columns, row))
                # Merge type_specific_data into the main dict
                if permit.get('type_specific_data'):
                    permit.update(permit['type_specific_data'])
                    del permit['type_specific_data']
                results.append(permit)
            return results
    finally:
        conn.close()


def get_permits_by_date(date: str, permit_type: Optional[str] = None) -> List[Dict]:
    """Retrieve permits scraped on a specific date"""
    conn = get_connection()

    sql = """
        SELECT
            id, permit_number, permit_type, status,
            application_date, issue_date, completed_date,
            primary_location, work_description, contractors, url,
            type_specific_data, scraped_at
        FROM permits
        WHERE DATE(scraped_at) = %s
    """
    params = [date]

    if permit_type:
        sql += " AND permit_type = %s"
        params.append(permit_type)

    sql += " ORDER BY permit_type, scraped_at DESC"

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                permit = dict(zip(columns, row))
                if permit.get('type_specific_data'):
                    permit.update(permit['type_specific_data'])
                    del permit['type_specific_data']
                results.append(permit)
            return results
    finally:
        conn.close()


def get_permit_stats() -> Dict:
    """Get summary statistics about permits in the database"""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Total count
            cur.execute("SELECT COUNT(*) FROM permits")
            total = cur.fetchone()[0]

            # Count by type
            cur.execute("""
                SELECT permit_type, COUNT(*)
                FROM permits
                GROUP BY permit_type
                ORDER BY COUNT(*) DESC
            """)
            by_type = dict(cur.fetchall())

            # Recent scrape info
            cur.execute("""
                SELECT DATE(scraped_at) as date, COUNT(*)
                FROM permits
                GROUP BY DATE(scraped_at)
                ORDER BY date DESC
                LIMIT 7
            """)
            recent_scrapes = [(str(row[0]), row[1]) for row in cur.fetchall()]

            return {
                'total_permits': total,
                'by_type': by_type,
                'recent_scrapes': recent_scrapes,
            }
    finally:
        conn.close()


def search_permits(
    query: str,
    permit_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Search permits by work description using full-text search
    """
    conn = get_connection()

    sql = """
        SELECT
            id, permit_number, permit_type, status,
            application_date, primary_location, work_description,
            contractors, url,
            ts_rank(to_tsvector('english', COALESCE(work_description, '')),
                    plainto_tsquery('english', %s)) AS rank
        FROM permits
        WHERE to_tsvector('english', COALESCE(work_description, ''))
              @@ plainto_tsquery('english', %s)
    """
    params = [query, query]

    if permit_type:
        sql += " AND permit_type = %s"
        params.append(permit_type)

    sql += " ORDER BY rank DESC LIMIT %s"
    params.append(limit)

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def init_database():
    """
    Initialize the database by running the schema.sql file

    This creates all tables, indexes, and views.
    """
    import os

    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("Database schema initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    # When run directly, initialize the database
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        print("Initializing database schema...")
        init_database()
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        print("Fetching permit statistics...")
        stats = get_permit_stats()
        print(f"\nTotal permits: {stats['total_permits']}")
        print("\nPermits by type:")
        for ptype, count in stats['by_type'].items():
            print(f"  {ptype}: {count}")
        print("\nRecent scrapes:")
        for date, count in stats['recent_scrapes']:
            print(f"  {date}: {count} permits")
    else:
        print("Usage:")
        print("  python database.py init   - Initialize database schema")
        print("  python database.py stats  - Show permit statistics")
