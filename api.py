"""
Flask API for serving permit data to the frontend
"""

import time
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import (
    get_connection,
    get_permit_stats,
    get_permits_by_type,
    get_permits_by_date,
    search_permits
)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Simple in-memory cache for geocoded addresses
geocode_cache = {}


@app.route('/api/permits', methods=['GET'])
def get_permits():
    """
    Get all permits with optional filtering

    Query params:
    - permit_type: Filter by permit type
    - limit: Maximum number of results (default 100)
    - offset: Number of results to skip (default 0)
    - search: Search term for work description
    """
    permit_type = request.args.get('permit_type')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    search_term = request.args.get('search')

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Build query
            sql = """
                SELECT
                    id, permit_number, permit_type, status, list_status,
                    application_date, issue_date, completed_date,
                    primary_location, specific_location,
                    work_description, type_of_work,
                    parcel_id, parcel_address, folio_number,
                    contractors, url, type_specific_data, scraped_at
                FROM permits
                WHERE 1=1
            """
            params = []

            if permit_type:
                sql += " AND permit_type = %s"
                params.append(permit_type)

            if search_term:
                sql += " AND (work_description ILIKE %s OR primary_location ILIKE %s)"
                params.extend([f'%{search_term}%', f'%{search_term}%'])

            sql += " ORDER BY scraped_at DESC, id DESC"
            sql += f" LIMIT {limit} OFFSET {offset}"

            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]

            permits = []
            for row in cur.fetchall():
                permit = dict(zip(columns, row))
                # Convert dates to strings
                for key in ['application_date', 'issue_date', 'completed_date', 'scraped_at']:
                    if permit.get(key):
                        permit[key] = str(permit[key])
                # Merge type_specific_data
                if permit.get('type_specific_data'):
                    permit['type_specific_data'] = dict(permit['type_specific_data'])
                permits.append(permit)

            # Get total count
            count_sql = "SELECT COUNT(*) FROM permits WHERE 1=1"
            count_params = []
            if permit_type:
                count_sql += " AND permit_type = %s"
                count_params.append(permit_type)
            if search_term:
                count_sql += " AND (work_description ILIKE %s OR primary_location ILIKE %s)"
                count_params.extend([f'%{search_term}%', f'%{search_term}%'])

            cur.execute(count_sql, count_params)
            total = cur.fetchone()[0]

            return jsonify({
                'permits': permits,
                'total': total,
                'limit': limit,
                'offset': offset
            })
    finally:
        conn.close()


@app.route('/api/permits/<permit_number>', methods=['GET'])
def get_permit(permit_number):
    """Get a single permit by permit number"""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id, permit_number, permit_type, status, list_status,
                    application_date, issue_date, completed_date,
                    primary_location, specific_location,
                    work_description, type_of_work,
                    parcel_id, parcel_address, folio_number,
                    contractors, url, type_specific_data, scraped_at
                FROM permits
                WHERE permit_number = %s
            """, (permit_number,))

            row = cur.fetchone()
            if not row:
                return jsonify({'error': 'Permit not found'}), 404

            columns = [desc[0] for desc in cur.description]
            permit = dict(zip(columns, row))

            # Convert dates to strings
            for key in ['application_date', 'issue_date', 'completed_date', 'scraped_at']:
                if permit.get(key):
                    permit[key] = str(permit[key])

            if permit.get('type_specific_data'):
                permit['type_specific_data'] = dict(permit['type_specific_data'])

            return jsonify(permit)
    finally:
        conn.close()


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get permit statistics"""
    try:
        stats = get_permit_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/permit-types', methods=['GET'])
def get_permit_types():
    """Get list of all permit types"""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT permit_type, COUNT(*) as count
                FROM permits
                GROUP BY permit_type
                ORDER BY count DESC
            """)
            types = [{'type': row[0], 'count': row[1]} for row in cur.fetchall()]
            return jsonify(types)
    finally:
        conn.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


def geocode_address(address, city=None):
    """
    Geocode an address using Nominatim (OpenStreetMap)
    Returns (lat, lng) or None if not found
    Constrains search to British Columbia, Canada
    """
    if not address or address.strip() == '':
        return None

    # Check cache first
    cache_key = address.lower().strip()
    if cache_key in geocode_cache:
        return geocode_cache[cache_key]

    try:
        # Append city and province to improve accuracy
        if city:
            full_address = f"{address}, {city}, British Columbia, Canada"
        else:
            full_address = f"{address}, British Columbia, Canada"

        # Use Nominatim API (free, but rate-limited)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': full_address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'ca'  # Restrict to Canada
        }
        headers = {
            'User-Agent': 'PermitFinder/1.0 (permit tracking application)'
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()

        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])

            # Verify the result is within British Columbia bounds
            # BC roughly: lat 48.3-60.0, lon -139.0 to -114.0
            if 48.0 <= lat <= 60.5 and -140.0 <= lon <= -114.0:
                result = (lat, lon)
                geocode_cache[cache_key] = result
                return result
            else:
                # Result is outside BC, reject it
                print(f"Geocoding rejected (outside BC): '{address}' -> ({lat}, {lon})")
                geocode_cache[cache_key] = None
                return None

        geocode_cache[cache_key] = None
        return None

    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")
        return None


@app.route('/api/permits/geocoded', methods=['GET'])
def get_permits_with_coordinates():
    """
    Get permits with pre-computed geocoded coordinates for map display.
    Returns both mapped permits (with coordinates) and unmapped permits (failed/pending geocoding).
    Uses pre-computed coordinates from database - instant loading!
    """
    permit_type = request.args.get('permit_type')
    limit = request.args.get('limit', 100, type=int)

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Get mapped permits (with coordinates)
            if permit_type:
                sql_mapped = """
                    SELECT
                        id, permit_number, permit_type, status,
                        application_date, issue_date,
                        primary_location, work_description,
                        contractors, url, source_city,
                        latitude, longitude
                    FROM permits
                    WHERE latitude IS NOT NULL
                    AND longitude IS NOT NULL
                    AND geocode_status = 'success'
                    AND permit_type = %s
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                cur.execute(sql_mapped, (permit_type, limit))
            else:
                sql_mapped = """
                    SELECT
                        id, permit_number, permit_type, status,
                        application_date, issue_date,
                        primary_location, work_description,
                        contractors, url, source_city,
                        latitude, longitude
                    FROM permits
                    WHERE latitude IS NOT NULL
                    AND longitude IS NOT NULL
                    AND geocode_status = 'success'
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                cur.execute(sql_mapped, (limit,))

            columns = [desc[0] for desc in cur.description]
            mapped_permits = []

            for row in cur.fetchall():
                permit = dict(zip(columns, row))
                # Convert dates
                for key in ['application_date', 'issue_date']:
                    if permit.get(key):
                        permit[key] = str(permit[key])
                # Convert coordinates to lat/lng for frontend
                permit['lat'] = float(permit.pop('latitude'))
                permit['lng'] = float(permit.pop('longitude'))
                mapped_permits.append(permit)

            # Get unmapped permits (failed or pending geocoding)
            if permit_type:
                sql_unmapped = """
                    SELECT
                        id, permit_number, permit_type, status,
                        application_date, issue_date,
                        primary_location, work_description,
                        contractors, url, source_city, geocode_status
                    FROM permits
                    WHERE (geocode_status = 'failed' OR geocode_status = 'pending' OR geocode_status IS NULL)
                    AND primary_location IS NOT NULL
                    AND primary_location != ''
                    AND permit_type = %s
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                cur.execute(sql_unmapped, (permit_type, limit))
            else:
                sql_unmapped = """
                    SELECT
                        id, permit_number, permit_type, status,
                        application_date, issue_date,
                        primary_location, work_description,
                        contractors, url, source_city, geocode_status
                    FROM permits
                    WHERE (geocode_status = 'failed' OR geocode_status = 'pending' OR geocode_status IS NULL)
                    AND primary_location IS NOT NULL
                    AND primary_location != ''
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                cur.execute(sql_unmapped, (limit,))

            columns = [desc[0] for desc in cur.description]
            unmapped_permits = []

            for row in cur.fetchall():
                permit = dict(zip(columns, row))
                for key in ['application_date', 'issue_date']:
                    if permit.get(key):
                        permit[key] = str(permit[key])
                unmapped_permits.append(permit)

            return jsonify({
                'permits': mapped_permits,
                'unmapped': unmapped_permits,
                'total': len(mapped_permits),
                'total_unmapped': len(unmapped_permits)
            })
    finally:
        conn.close()


@app.route('/api/geocode', methods=['GET'])
def geocode():
    """Geocode a single address"""
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'Address required'}), 400

    coords = geocode_address(address)
    if coords:
        return jsonify({'lat': coords[0], 'lng': coords[1], 'address': address})
    else:
        return jsonify({'error': 'Could not geocode address'}), 404


if __name__ == '__main__':
    print("Starting Permit API server...")
    print("API available at http://localhost:5000")
    app.run(debug=True, port=5000)
