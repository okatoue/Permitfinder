"""
Geocode Permits Script
- Pre-computes latitude/longitude for all permits
- Stores coordinates in the database for fast map loading
- Cleans addresses before geocoding (strips unit numbers, etc.)
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
    - Removes postal codes
    - Removes existing city/province suffixes (since we add them later)
    - Normalizes format
    """
    if not address:
        return None

    addr = str(address).strip()

    # Remove Canadian postal codes (e.g., V6B 4N9)
    addr = re.sub(r'\s*[A-Z]\d[A-Z]\s*\d[A-Z]\d\s*$', '', addr, flags=re.IGNORECASE)

    # Remove existing city/province suffixes (we add these later)
    # Patterns like ", Vancouver, BC" or ", Vancouver BC"
    addr = re.sub(r',?\s*Vancouver,?\s*BC\s*$', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r',?\s*Vancouver,?\s*British Columbia\s*$', '', addr, flags=re.IGNORECASE)

    # Remove common unit/suite patterns
    # "Unit 12", "Suite 100", "#3", "Apt 5", etc.
    patterns = [
        r'\s*#\s*\d+\s*',           # #3, # 123
        r'\s*Unit\s*\d+\s*',        # Unit 12
        r'\s*Suite\s*\d+\s*',       # Suite 100
        r'\s*Apt\.?\s*\d+\s*',      # Apt 5, Apt. 5
        r'\s*-\s*\d+\s*$',          # -123 at end
        r'\s+\d+\s*$',              # trailing number like "Road 12"
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
            # BC roughly: lat 48.3-60.0, lon -139.0 to -114.0
            if 48.0 <= lat <= 60.5 and -140.0 <= lon <= -114.0:
                return (lat, lon)
            else:
                print(f"    Rejected (outside BC): {address} -> ({lat}, {lon})")
                return None

        return None

    except Exception as e:
        print(f"    Error geocoding '{address}': {e}")
        return None


def is_valid_street_address(address):
    """
    Check if an address looks like a valid street address.
    Valid addresses typically start with a number followed by a street name.
    """
    if not address:
        return False

    addr = str(address).strip()

    # Valid address should start with a street number
    if re.match(r'^\d+\s+', addr):
        return True

    return False


def geocode_all_permits(batch_size=50, delay=1.0):
    """
    Geocode all permits that don't have coordinates yet.

    Args:
        batch_size: Number of permits to process before committing
        delay: Delay between requests (Nominatim rate limit is 1 req/sec)
    """
    conn = get_connection()
    cur = conn.cursor()

    # Get permits that need geocoding (include specific_location as fallback)
    cur.execute("""
        SELECT id, permit_number, primary_location, specific_location, source_city
        FROM permits
        WHERE (geocode_status = 'pending' OR geocode_status IS NULL)
        AND (primary_location IS NOT NULL OR specific_location IS NOT NULL)
        ORDER BY id
    """)

    permits = cur.fetchall()
    total = len(permits)
    print(f"Found {total} permits to geocode")

    success_count = 0
    failed_count = 0

    for i, (permit_id, permit_number, primary_loc, specific_loc, city) in enumerate(permits):
        city = city or 'Vancouver'

        # Use primary_location if it's a valid street address, otherwise fall back to specific_location
        if is_valid_street_address(primary_loc):
            address = primary_loc
        elif is_valid_street_address(specific_loc):
            address = specific_loc
            print(f"[{i+1}/{total}] {permit_number}: {primary_loc} -> using specific_location: {address}")
        else:
            # Neither is a valid address
            print(f"[{i+1}/{total}] {permit_number}: No valid address (primary: {primary_loc}, specific: {specific_loc})")
            cur.execute("""
                UPDATE permits
                SET geocode_status = 'failed'
                WHERE id = %s
            """, (permit_id,))
            failed_count += 1
            continue

        if address == primary_loc:
            print(f"[{i+1}/{total}] {permit_number}: {address}")

        coords = geocode_address(address, city)

        if coords:
            lat, lon = coords
            cur.execute("""
                UPDATE permits
                SET latitude = %s, longitude = %s, geocode_status = 'success'
                WHERE id = %s
            """, (lat, lon, permit_id))
            print(f"    -> ({lat:.6f}, {lon:.6f})")
            success_count += 1
        else:
            cur.execute("""
                UPDATE permits
                SET geocode_status = 'failed'
                WHERE id = %s
            """, (permit_id,))
            print(f"    -> FAILED")
            failed_count += 1

        # Commit periodically
        if (i + 1) % batch_size == 0:
            conn.commit()
            print(f"  Committed batch ({i+1}/{total})")

        # Rate limiting
        time.sleep(delay)

    # Final commit
    conn.commit()
    conn.close()

    print(f"\nGeocoding complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {total}")


def reset_failed_geocodes():
    """Reset all failed geocodes to pending for retry."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE permits
        SET geocode_status = 'pending', latitude = NULL, longitude = NULL
        WHERE geocode_status = 'failed'
    """)

    count = cur.rowcount
    conn.commit()
    conn.close()

    print(f"Reset {count} failed geocodes to pending")


def get_geocode_stats():
    """Get statistics about geocoding status."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            geocode_status,
            COUNT(*) as count
        FROM permits
        GROUP BY geocode_status
        ORDER BY count DESC
    """)

    stats = cur.fetchall()
    conn.close()

    print("Geocoding Statistics:")
    for status, count in stats:
        print(f"  {status or 'NULL'}: {count}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'stats':
            get_geocode_stats()
        elif cmd == 'reset':
            reset_failed_geocodes()
        elif cmd == 'run':
            geocode_all_permits()
        else:
            print("Usage:")
            print("  py geocode_permits.py run    - Geocode all pending permits")
            print("  py geocode_permits.py stats  - Show geocoding statistics")
            print("  py geocode_permits.py reset  - Reset failed geocodes to retry")
    else:
        print("Usage:")
        print("  py geocode_permits.py run    - Geocode all pending permits")
        print("  py geocode_permits.py stats  - Show geocoding statistics")
        print("  py geocode_permits.py reset  - Reset failed geocodes to retry")
