"""
Geocoding utility module
- Shared geocoding functions for all scrapers
- Cleans addresses and geocodes to BC, Canada coordinates
"""

import re
import time
import requests
from database import get_connection


def clean_address_for_geocoding(address, city='Vancouver'):
    """
    Clean address for better geocoding results.
    - Removes unit/suite numbers
    - Removes apartment numbers (#3, Unit 12, etc.)
    - Normalizes format
    """
    if not address:
        return None

    addr = str(address).strip()

    # Remove common unit/suite patterns
    patterns = [
        r'\s*#\s*\d+\s*',           # #3, # 123
        r'\s*Unit\s*\d+\s*',        # Unit 12
        r'\s*Suite\s*\d+\s*',       # Suite 100
        r'\s*Apt\.?\s*\d+\s*',      # Apt 5, Apt. 5
        r'\s*-\s*\d+\s*$',          # -123 at end
    ]

    for pattern in patterns:
        addr = re.sub(pattern, ' ', addr, flags=re.IGNORECASE)

    # Clean up whitespace
    addr = re.sub(r'\s+', ' ', addr).strip()

    # Remove trailing commas
    addr = addr.rstrip(',').strip()

    return addr


def geocode_address(address, city='Vancouver'):
    """
    Geocode an address using Nominatim (OpenStreetMap).
    Returns (lat, lng) or None if not found.
    Constrains search to British Columbia, Canada.
    """
    if not address or address.strip() == '':
        return None

    # Skip known bad addresses
    if 'Street Lighting' in address:
        return None

    try:
        # Clean the address first
        clean_addr = clean_address_for_geocoding(address, city)
        if not clean_addr:
            return None

        # Build full address with city and province
        full_address = f"{clean_addr}, {city}, British Columbia, Canada"

        # Use Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': full_address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'ca'
        }
        headers = {
            'User-Agent': 'PermitFinder/1.0 (permit tracking application)'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])

            # Verify the result is within British Columbia bounds
            if 48.0 <= lat <= 60.5 and -140.0 <= lon <= -114.0:
                return (lat, lon)

        return None

    except Exception as e:
        print(f"    Geocoding error for '{address}': {e}")
        return None


def geocode_permit(permit_id, address, city='Vancouver', delay=1.0):
    """
    Geocode a single permit and update the database.

    Args:
        permit_id: Database ID of the permit
        address: Address to geocode
        city: City name for context (default: Vancouver)
        delay: Delay after geocoding (rate limiting)

    Returns:
        tuple (lat, lng) if successful, None if failed
    """
    if not address:
        return None

    coords = geocode_address(address, city)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if coords:
            lat, lon = coords
            cur.execute("""
                UPDATE permits
                SET latitude = %s, longitude = %s, geocode_status = 'success'
                WHERE id = %s
            """, (lat, lon, permit_id))
            conn.commit()
            print(f"    Geocoded: ({lat:.6f}, {lon:.6f})")
        else:
            cur.execute("""
                UPDATE permits
                SET geocode_status = 'failed'
                WHERE id = %s
            """, (permit_id,))
            conn.commit()
            print(f"    Geocoding failed")
    finally:
        conn.close()

    # Rate limiting
    time.sleep(delay)

    return coords


def geocode_permits_batch(permits_data, delay=1.0):
    """
    Geocode multiple permits and update the database.

    Args:
        permits_data: List of tuples (permit_id, address, city)
        delay: Delay between requests (rate limiting)

    Returns:
        dict with 'success' and 'failed' counts
    """
    success = 0
    failed = 0

    for permit_id, address, city in permits_data:
        city = city or 'Vancouver'
        result = geocode_permit(permit_id, address, city, delay)
        if result:
            success += 1
        else:
            failed += 1

    return {'success': success, 'failed': failed}
