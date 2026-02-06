"""
Richmond Weekly Reports Scraper
- Navigates to Richmond's Weekly Reports for Permits page
- Finds the 2026 Weekly Reports section
- Downloads the most recent Building Reports and Demolition Reports PDFs
- Parses PDF content and saves permits to database
"""

import os
import re
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
import pdfplumber
from database import save_permits_to_db, get_permit_stats, get_connection
from geocoder import geocode_permit


def get_download_folder():
    """Get or create the downloads folder"""
    download_folder = os.path.join(os.path.dirname(__file__), "richmond_reports")
    os.makedirs(download_folder, exist_ok=True)
    return download_folder


def download_pdf(url, filename, download_folder):
    """Download a PDF file from URL"""
    filepath = os.path.join(download_folder, filename)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"  Downloaded: {filename}")
        return filepath
    except Exception as e:
        print(f"  Error downloading {filename}: {e}")
        return None


def extract_2026_reports(page):
    """Extract the most recent 2026 Building and Demolition report URLs"""

    js_code = """
    () => {
        // Find all PDF links that contain "2026" in the URL
        const allLinks = Array.from(document.querySelectorAll('a[href*=".pdf"]'));
        const links2026 = allLinks.filter(link => link.href.includes('2026'));

        // Get the first (most recent) building and demolition reports for 2026
        const buildingLink = links2026.find(l => l.href.toLowerCase().includes('building'));
        const demolitionLink = links2026.find(l => l.href.toLowerCase().includes('demolition'));

        return {
            building: buildingLink ? {
                url: buildingLink.href,
                text: buildingLink.textContent.trim()
            } : null,
            demolition: demolitionLink ? {
                url: demolitionLink.href,
                text: demolitionLink.textContent.trim()
            } : null
        };
    }
    """

    try:
        return page.evaluate(js_code)
    except Exception as e:
        print(f"Error extracting report links: {e}")
        return {"building": None, "demolition": None}


def extract_filename_from_url(url):
    """Extract a clean filename from the PDF URL"""
    filename = url.split('/')[-1]
    return filename


def clean_text(text):
    """Clean extracted text from PDF"""
    if text is None:
        return None
    text = str(text).strip()
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text if text else None


def clean_address(text):
    """
    Clean address by removing description after '-'
    e.g., '11700 Blundell Road - Detached Garage' -> '11700 Blundell Road'
    """
    if text is None:
        return None
    text = str(text).strip()
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove everything after ' - ' (space-dash-space)
    if ' - ' in text:
        text = text.split(' - ')[0].strip()
    return text if text else None


def parse_folder_number(folder_num):
    """
    Parse folder number to create a standardized permit number.
    Input: "24 038935 000 01 B2" or "25 036554 000 00 D7"
    Output: "BP-24-038935" or "DP-25-036554"
    """
    if not folder_num:
        return None

    parts = folder_num.strip().split()
    if len(parts) >= 2:
        year = parts[0]
        number = parts[1]
        # Determine prefix based on last part (B2 = Building, D7 = Demolition)
        suffix = parts[-1] if len(parts) > 2 else ""
        if 'D' in suffix.upper():
            prefix = "DP"  # Demolition Permit
        else:
            prefix = "BP"  # Building Permit
        return f"{prefix}-{year}-{number}"

    return folder_num


def parse_date(date_str):
    """
    Parse date from PDF format (YYYY/MM/DD) to ISO format (YYYY-MM-DD)
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Try YYYY/MM/DD format
    try:
        dt = datetime.strptime(date_str, '%Y/%m/%d')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Try other formats
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue

    return None


def parse_construction_value(value_str):
    """Parse construction value string to float"""
    if not value_str:
        return None

    value_str = str(value_str).strip()
    # Remove $ and commas
    value_str = value_str.replace('$', '').replace(',', '')

    try:
        return float(value_str)
    except ValueError:
        return None


def extract_phone_from_contact(contact_str):
    """Extract name and phone from contact string like 'Name (Phone)'"""
    if not contact_str:
        return None, None

    contact_str = str(contact_str).strip()

    # Pattern: "Name (XXX)XXX-XXXX" or "Name (XXX) XXX-XXXX"
    phone_pattern = r'\((\d{3})\)\s*(\d{3}[-\s]?\d{4})'
    match = re.search(phone_pattern, contact_str)

    if match:
        phone = f"({match.group(1)}){match.group(2)}"
        name = contact_str[:match.start()].strip()
        return name, phone

    return contact_str, None


def is_folder_number(text):
    """Check if text looks like a folder number (e.g., '24 038935 000 01 B2')"""
    if not text:
        return False
    text = str(text).strip()
    # Pattern: 2 digits, space, 6 digits, space, 3 digits, space, 2 digits, space, alphanumeric
    pattern = r'^\d{2}\s+\d{6}\s+\d{3}\s+\d{2}\s+\w+'
    return bool(re.match(pattern, text.replace('\n', ' ')))


def parse_building_pdf(filepath):
    """
    Parse Building Permit Issuance Report PDF and extract permit data.

    Returns list of permit dictionaries.
    """
    permits = []

    print(f"\nParsing Building Report: {filepath}")

    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""

                # Check for SUB TYPE headers in the text
                sub_type_matches = re.findall(r'SUB TYPE:\s*([^\n]+)', text)

                # Extract tables from page
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    # Process each row in the table
                    for row in table:
                        if not row or len(row) < 6:
                            continue

                        # Get the first cell and check if it's a folder number
                        first_cell = clean_text(row[0]) if row[0] else ""

                        # Skip header rows and summary rows
                        if not first_cell or 'FOLDER' in first_cell.upper():
                            continue

                        # Skip rows that are just numbers (summary counts)
                        if first_cell.replace(' ', '').isdigit():
                            continue

                        # Check if this looks like a folder number
                        if not is_folder_number(first_cell):
                            continue

                        # This is a data row - extract permit info
                        # Column order: FOLDER NUMBER, WORK PROPOSED, STATUS, ISSUE DATE, CONSTR VALUE, FOLDER NAME, APPLICANT, CONTRACTOR
                        permit = {
                            'permit_number': parse_folder_number(first_cell),
                            'permit_type': 'Building Permit',
                            'source_city': 'Richmond',
                        }

                        # Extract other fields by position
                        if len(row) > 1 and row[1]:
                            permit['type_of_work'] = clean_text(row[1])

                        if len(row) > 2 and row[2]:
                            permit['status'] = clean_text(row[2])
                            permit['list_status'] = permit['status']

                        if len(row) > 3 and row[3]:
                            permit['issue_date'] = parse_date(row[3])
                            permit['list_issue_date'] = permit['issue_date']

                        if len(row) > 4 and row[4]:
                            value = parse_construction_value(row[4])
                            if value is not None:
                                permit['construction_value'] = value

                        if len(row) > 5 and row[5]:
                            permit['primary_location'] = clean_address(row[5])
                            permit['list_location'] = permit['primary_location']

                        if len(row) > 6 and row[6]:
                            applicant_name, applicant_phone = extract_phone_from_contact(row[6])
                            if applicant_name:
                                permit['applicant'] = applicant_name
                                permit['applicant_phone'] = applicant_phone

                        if len(row) > 7 and row[7]:
                            contractor_name, contractor_phone = extract_phone_from_contact(row[7])
                            if contractor_name:
                                permit['contractors'] = contractor_name
                                permit['contractor_phone'] = contractor_phone

                        # Add sub-type if found
                        if sub_type_matches:
                            permit['sub_type'] = sub_type_matches[-1].strip()

                        # Only add if we have a valid permit number
                        if permit.get('permit_number'):
                            permits.append(permit)
                            print(f"  Found: {permit['permit_number']} - {permit.get('primary_location', 'N/A')}")

    except Exception as e:
        print(f"Error parsing Building PDF: {e}")
        import traceback
        traceback.print_exc()

    print(f"  Total building permits extracted: {len(permits)}")
    return permits


def parse_demolition_pdf(filepath):
    """
    Parse Demolition Permit Issuance Report PDF and extract permit data.

    Returns list of permit dictionaries.
    """
    permits = []

    print(f"\nParsing Demolition Report: {filepath}")

    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""

                # Check for SUB TYPE headers
                sub_type_matches = re.findall(r'SUB TYPE:\s*([^\n]+)', text)

                # Extract tables from page
                tables = page.extract_tables()

                for table in tables:
                    if not table:
                        continue

                    # Process each row in the table
                    for row in table:
                        if not row or len(row) < 5:
                            continue

                        # Get the first cell and check if it's a folder number
                        first_cell = clean_text(row[0]) if row[0] else ""

                        # Skip header rows and summary rows
                        if not first_cell or 'FOLDER' in first_cell.upper():
                            continue

                        # Skip rows that are just numbers (summary counts)
                        if first_cell.replace(' ', '').isdigit():
                            continue

                        # Check if this looks like a folder number
                        if not is_folder_number(first_cell):
                            continue

                        # This is a data row - extract permit info
                        # Demolition columns: FOLDER NUMBER, WORK PROPOSED, STATUS, ISSUE DATE, FOLDER NAME, APPLICANT, CONTRACTOR
                        permit = {
                            'permit_number': parse_folder_number(first_cell),
                            'permit_type': 'Demolition Permit',
                            'source_city': 'Richmond',
                        }

                        # Extract other fields by position
                        if len(row) > 1 and row[1]:
                            permit['type_of_work'] = clean_text(row[1])

                        if len(row) > 2 and row[2]:
                            permit['status'] = clean_text(row[2])
                            permit['list_status'] = permit['status']

                        if len(row) > 3 and row[3]:
                            permit['issue_date'] = parse_date(row[3])
                            permit['list_issue_date'] = permit['issue_date']

                        if len(row) > 4 and row[4]:
                            permit['primary_location'] = clean_address(row[4])
                            permit['list_location'] = permit['primary_location']

                        if len(row) > 5 and row[5]:
                            applicant_name, applicant_phone = extract_phone_from_contact(row[5])
                            if applicant_name:
                                permit['applicant'] = applicant_name
                                permit['applicant_phone'] = applicant_phone

                        if len(row) > 6 and row[6]:
                            contractor_name, contractor_phone = extract_phone_from_contact(row[6])
                            if contractor_name:
                                permit['contractors'] = contractor_name
                                permit['contractor_phone'] = contractor_phone

                        # Add sub-type if found
                        if sub_type_matches:
                            permit['sub_type'] = sub_type_matches[-1].strip()

                        # Only add if we have a valid permit number
                        if permit.get('permit_number'):
                            permits.append(permit)
                            print(f"  Found: {permit['permit_number']} - {permit.get('primary_location', 'N/A')}")

    except Exception as e:
        print(f"Error parsing Demolition PDF: {e}")
        import traceback
        traceback.print_exc()

    print(f"  Total demolition permits extracted: {len(permits)}")
    return permits


def save_permits(permits_by_type):
    """Save permits to PostgreSQL database and geocode them"""
    if not permits_by_type:
        print("\nNo permits to save.")
        return

    print("\nSaving permits to database...")
    results = save_permits_to_db(permits_by_type)

    total_saved = sum(results.values())
    print(f"\nTotal permits saved to database: {total_saved}")

    # Geocode newly saved permits
    print("\nGeocoding new permits...")
    geocode_new_permits()

    return results


def convert_permit_to_portal_format(permit_number):
    """
    Convert permit number from database format to portal format.
    "BP-24-040504" -> "24040504"
    "DP-25-036554" -> "25036554"
    """
    if not permit_number:
        return None
    # Remove prefix (BP- or DP-) and dashes
    parts = permit_number.split('-')
    if len(parts) >= 3:
        return parts[1] + parts[2]
    return permit_number.replace('-', '')


def get_permits_needing_portal_lookup():
    """Get Richmond permits that haven't been looked up in the portal yet"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, permit_number, primary_location
        FROM permits
        WHERE source_city = 'Richmond'
        AND (portal_lookup_done IS NULL OR portal_lookup_done = FALSE)
        ORDER BY id
    """)

    permits = cur.fetchall()
    conn.close()
    return permits


def update_permit_with_portal_data(permit_id, portal_data):
    """Update permit record with data from portal lookup"""
    conn = get_connection()
    cur = conn.cursor()

    # Update the type_specific_data JSONB field with portal data
    cur.execute("""
        UPDATE permits
        SET type_specific_data = COALESCE(type_specific_data, '{}'::jsonb) || %s::jsonb,
            portal_lookup_done = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (json.dumps(portal_data), permit_id))

    conn.commit()
    conn.close()
    print(f"  Updated permit {permit_id} with portal data")


def extract_modal_comment(page, timeout=1500):
    """
    Extract comment text from an open modal dialog.
    Returns the comment text or None if no modal found.
    """
    try:
        # Wait for modal to appear (short timeout)
        modal = page.locator('.ui-dialog, .modal, [role="dialog"]').first
        modal.wait_for(state="visible", timeout=timeout)

        # Get the modal body text (exclude the title and button)
        modal_body = page.locator('.ui-dialog-content, .modal-body, [role="dialog"] > div').first
        comment_text = modal_body.inner_text()

        # Close the modal by clicking OK button
        ok_button = page.locator('.ui-dialog button:has-text("OK"), .modal button:has-text("OK"), button:has-text("Close")').first
        ok_button.click(timeout=2000)
        page.wait_for_timeout(200)  # Brief wait for modal to close

        return comment_text.strip()
    except:
        # Try to close any open modal silently
        try:
            page.locator('button:has-text("OK")').first.click(timeout=500)
            page.wait_for_timeout(200)
        except:
            pass
        return None


def extract_inspections_data(page):
    """
    Extract data from the View Inspections page using JavaScript.
    Returns a list of inspection records with full comments from modals.
    """
    inspections = []

    try:
        # Table has 5 columns: Inspections, Status, Scheduled Date, Actions, Comments
        # Header is in <thead>, data rows in <tbody>.
        js_code = """
        () => {
            const results = [];
            const table = document.querySelector('.ui-page-active table') || document.querySelector('table');
            if (!table) return results;

            const tbody = table.querySelector('tbody');
            const rows = (tbody || table).querySelectorAll('tr');
            rows.forEach((row, index) => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 2) return;

                const inspection = cells[0] ? cells[0].innerText.trim() : '';
                const status = cells[1] ? cells[1].innerText.trim() : '';
                const commentCell = cells[4] || null;
                const commentText = commentCell ? commentCell.innerText.trim() : '';
                const hasCommentLink = commentCell ? commentCell.querySelector('a') !== null : false;

                if (inspection && inspection !== 'Inspections') {
                    results.push({
                        inspection: inspection,
                        status: status,
                        comment: commentText,
                        hasLink: hasCommentLink,
                        tbodyIndex: index
                    });
                }
            });
            return results;
        }
        """

        raw_data = page.evaluate(js_code)

        # Process each row - click comment links to get full text if needed
        for item in raw_data:
            comment_text = item['comment']

            # If there's a link, click it to get full comment from modal
            if item['hasLink'] and comment_text:
                try:
                    nth = item["tbodyIndex"] + 1
                    # Try active page first, fall back to any table (matches JS logic)
                    row_selector = f'.ui-page-active table tbody tr:nth-child({nth}) td:nth-child(5) a'
                    comment_link = page.locator(row_selector).first
                    if comment_link.count() == 0:
                        row_selector = f'table tbody tr:nth-child({nth}) td:nth-child(5) a'
                        comment_link = page.locator(row_selector).first
                    if comment_link.count() > 0:
                        comment_link.click(timeout=2000)
                        page.wait_for_timeout(300)
                        modal_text = extract_modal_comment(page)
                        if modal_text:
                            comment_text = modal_text
                except:
                    pass  # Keep original comment text

            inspections.append({
                'inspection': item['inspection'],
                'status': item['status'],
                'comment': comment_text
            })

    except Exception as e:
        print(f"  Error extracting inspections: {e}")

    return inspections


def extract_plan_review_data(page):
    """
    Extract data from the Plan Review page using JavaScript.
    Comments are clickable links that open modals with full text.
    Returns a list of plan review records with comments.
    """
    plan_reviews = []

    try:
        # The table has columns: Name, Reviewer, Reviewer Phone, Status, Comment, (possibly FullComment)
        # The header is in <thead> and data rows in <tbody>.
        # Comment column contains clickable links that open modals with full comment text.
        js_code = """
        () => {
            const results = [];
            const table = document.querySelector('.ui-page-active table') || document.querySelector('table');
            if (!table) return results;

            const tbody = table.querySelector('tbody');
            const rows = (tbody || table).querySelectorAll('tr');
            rows.forEach((row, index) => {
                const cells = row.querySelectorAll('td');
                if (cells.length < 4) return;

                const name = cells[0] ? cells[0].innerText.trim() : '';
                const status = cells[3] ? cells[3].innerText.trim() : '';
                const commentCell = cells[4] || null;
                const commentText = commentCell ? commentCell.innerText.trim() : '';
                const hasCommentLink = commentCell ? commentCell.querySelector('a') !== null : false;

                if (name && name !== 'Name') {
                    results.push({
                        name: name,
                        status: status,
                        comment: commentText,
                        hasLink: hasCommentLink,
                        tbodyIndex: index
                    });
                }
            });
            return results;
        }
        """

        raw_data = page.evaluate(js_code)

        # Process each row - click comment links to get full text from modal
        for item in raw_data:
            comment_text = item['comment']

            if item['hasLink'] and comment_text:
                try:
                    nth = item["tbodyIndex"] + 1
                    # Try active page first, fall back to any table (matches JS logic)
                    row_selector = f'.ui-page-active table tbody tr:nth-child({nth}) td:nth-child(5) a'
                    comment_link = page.locator(row_selector).first
                    if comment_link.count() == 0:
                        row_selector = f'table tbody tr:nth-child({nth}) td:nth-child(5) a'
                        comment_link = page.locator(row_selector).first
                    if comment_link.count() > 0:
                        comment_link.click(timeout=2000)
                        page.wait_for_timeout(300)
                        modal_text = extract_modal_comment(page)
                        if modal_text:
                            comment_text = modal_text
                except:
                    pass  # Keep original comment text

            plan_reviews.append({
                'name': item['name'],
                'status': item['status'],
                'comment': comment_text
            })

    except Exception as e:
        print(f"  Error extracting plan reviews: {e}")

    return plan_reviews


def click_portal_nav_link(page, href_patterns, text_patterns):
    """
    Try to click a navigation link on the portal using multiple strategies.
    Returns True if a link was clicked, False otherwise.
    """
    # Strategy 1: Playwright locator with href patterns
    for pattern in href_patterns:
        try:
            link = page.locator(f'a[href*="{pattern}"]:visible').first
            if link.count() > 0:
                link.click(timeout=5000)
                print(f"    Clicked link matching href *{pattern}*")
                return True
        except Exception:
            pass

    # Strategy 2: Playwright text-based locator
    for pattern in text_patterns:
        try:
            link = page.locator(f'a:has-text("{pattern}"):visible').first
            if link.count() > 0:
                link.click(timeout=5000)
                print(f"    Clicked link matching text '{pattern}'")
                return True
        except Exception:
            pass

    # Strategy 3: jQuery evaluate as last resort (in case links are in jQuery Mobile)
    for pattern in href_patterns:
        try:
            clicked = page.evaluate(f"""
                () => {{
                    const link = document.querySelector('a[href*="{pattern}"]');
                    if (link) {{ link.click(); return true; }}
                    return false;
                }}
            """)
            if clicked:
                print(f"    Clicked link via JS matching href *{pattern}*")
                return True
        except Exception:
            pass

    return False


def extract_portal_data(page):
    """
    Extract permit data from the portal.
    Navigates to both View Inspections and Plan Review pages.
    Returns a dictionary with inspections and plan_reviews data.
    """
    data = {
        'inspections': [],
        'plan_reviews': []
    }

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(3000)  # Extra wait for jQuery Mobile page transitions

        current_url = page.url
        print(f"    Current URL: {current_url}")

        # Debug: show available navigation links relevant to inspections/plan review
        nav_info = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a'));
                return links
                    .filter(a => a.textContent.trim().length > 0)
                    .map(a => ({
                        text: a.textContent.trim().substring(0, 60),
                        href: a.getAttribute('href') || '',
                        visible: a.offsetParent !== null
                    }))
                    .filter(l =>
                        l.href.toLowerCase().includes('inspection') ||
                        l.href.toLowerCase().includes('plan') ||
                        l.text.toLowerCase().includes('inspection') ||
                        l.text.toLowerCase().includes('plan review')
                    );
            }
        """)
        if nav_info:
            for link in nav_info:
                vis = "visible" if link['visible'] else "hidden"
                print(f"    Nav link: '{link['text']}' -> {link['href']} ({vis})")
        else:
            print("    No inspection/plan review links found on page")

        # 1. Extract View Inspections data
        print("    Extracting View Inspections data...")
        try:
            if 'Inspection' not in current_url and 'inspection' not in current_url:
                clicked = click_portal_nav_link(
                    page,
                    href_patterns=["ShowInspections", "Inspection", "inspection"],
                    text_patterns=["View Inspections", "Inspections"]
                )
                if clicked:
                    page.wait_for_timeout(3000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                else:
                    print("    Could not find inspections link, extracting from current page")

            data['inspections'] = extract_inspections_data(page)
            print(f"    Found {len(data['inspections'])} inspections")
        except Exception as e:
            print(f"    Could not access View Inspections: {e}")

        # 2. Navigate to Plan Review
        print("    Extracting Plan Review data...")
        try:
            # If clicking comments navigated away, go back to the portal page
            post_url = page.url
            if ('inspection' not in post_url.lower() and
                'planreview' not in post_url.lower() and
                'inspections.richmond.ca' not in post_url.lower()):
                print("    Page navigated away, going back...")
                page.go_back(wait_until="networkidle", timeout=10000)
                page.wait_for_timeout(1000)

            clicked = click_portal_nav_link(
                page,
                href_patterns=["PlanReview", "planreview"],
                text_patterns=["Plan Review"]
            )
            if clicked:
                page.wait_for_timeout(3000)
                page.wait_for_load_state("networkidle", timeout=10000)
            else:
                print("    Could not find plan review link, extracting from current page")

            data['plan_reviews'] = extract_plan_review_data(page)
            print(f"    Found {len(data['plan_reviews'])} plan reviews")
        except Exception as e:
            print(f"    Could not access Plan Review: {e}")

    except Exception as e:
        print(f"  Error extracting portal data: {e}")
        data['_extraction_error'] = str(e)

    return data


def run_portal_lookups(browser=None, page=None):
    """
    Look up permits in the Richmond inspection portal.
    Requires human interaction to solve CAPTCHAs.
    """
    # Use the explicit login/lookup page URL to ensure we always get the form
    PORTAL_URL = "https://inspections.richmond.ca/Account/LogOn"

    permits = get_permits_needing_portal_lookup()

    if not permits:
        print("\nNo permits need portal lookup.")
        return

    print(f"\n{'='*50}")
    print(f"Portal Lookup: {len(permits)} permits to look up")
    print("You will need to solve the CAPTCHA for each permit.")
    print(f"{'='*50}\n")

    # Use existing browser or create new one
    own_browser = False
    if browser is None:
        from playwright.sync_api import sync_playwright
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        own_browser = True

    if page is None:
        page = browser.new_page()

    try:
        for i, (permit_id, permit_number, address) in enumerate(permits):
            portal_number = convert_permit_to_portal_format(permit_number)

            print(f"\n--- Permit {i+1}/{len(permits)}: {permit_number} ({address}) ---")
            print(f"Portal number: {portal_number}")

            # Navigate to portal (fresh page each time guarantees clean state)
            page.goto(PORTAL_URL, wait_until="networkidle", timeout=30000)

            # Wait for permit input field
            permit_input = page.locator('input[type="number"]').first
            permit_input.wait_for(state="visible", timeout=15000)
            permit_input.fill(portal_number)

            print(f"Entered permit number: {portal_number}")
            print("\n>>> PLEASE SOLVE THE CAPTCHA <<<")
            print("Press ENTER in this console after solving the CAPTCHA...")
            input()  # Wait for human to solve CAPTCHA

            # Click the lookup button (it's actually a link styled as a button)
            lookup_button = page.locator('a:has-text("Lookup Permit Info")').first
            lookup_button.click()

            print("Clicked Lookup button, waiting for results...")

            # Wait for page to load
            page.wait_for_load_state("networkidle")

            # Extract data from results page
            portal_data = extract_portal_data(page)

            if portal_data:
                insp_count = len(portal_data.get('inspections', []))
                plan_count = len(portal_data.get('plan_reviews', []))
                print(f"  Extracted {insp_count} inspections, {plan_count} plan reviews")
                update_permit_with_portal_data(permit_id, portal_data)
            else:
                print("  No data extracted from portal")

            # Create fresh page for next permit (closes current page, opens new one)
            # This guarantees a clean state instead of trying to navigate back
            page.close()
            page = browser.new_page()

    except KeyboardInterrupt:
        print("\n\nPortal lookup interrupted by user.")
    except Exception as e:
        print(f"\nError during portal lookup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if own_browser:
            browser.close()
            playwright.stop()

    print(f"\n{'='*50}")
    print("Portal lookups complete!")


def geocode_new_permits():
    """Geocode all permits that don't have coordinates yet"""
    conn = get_connection()
    cur = conn.cursor()

    # Get permits that need geocoding (from Richmond)
    cur.execute("""
        SELECT id, permit_number, primary_location, source_city
        FROM permits
        WHERE (geocode_status = 'pending' OR geocode_status IS NULL)
        AND source_city = 'Richmond'
        AND primary_location IS NOT NULL
        AND primary_location != ''
    """)

    permits = cur.fetchall()
    conn.close()

    if not permits:
        print("  No new permits to geocode")
        return

    print(f"  Geocoding {len(permits)} permits...")

    for permit_id, permit_number, address, city in permits:
        print(f"  {permit_number}: {address}")
        geocode_permit(permit_id, address, city or 'Richmond', delay=1.0)


def ensure_portal_lookup_column():
    """Add portal_lookup_done column if it doesn't exist"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            ALTER TABLE permits
            ADD COLUMN IF NOT EXISTS portal_lookup_done BOOLEAN DEFAULT FALSE
        """)
        conn.commit()
    except Exception as e:
        # Column might already exist or other error
        conn.rollback()
    finally:
        conn.close()


def run_scraper(skip_pdfs=False, skip_portal=False):
    """
    Main scraper function.

    Args:
        skip_pdfs: Skip PDF scraping (useful if you only want portal lookups)
        skip_portal: Skip portal lookups (useful if you only want PDF data)
    """

    # Ensure database has the portal_lookup_done column
    ensure_portal_lookup_column()

    all_permits = {}

    if not skip_pdfs:
        url = "https://www.richmond.ca/business-development/building-approvals/reports/weeklyreports.htm"
        download_folder = get_download_folder()

        print(f"Download folder: {download_folder}")
        print(f"Opening Richmond Weekly Reports page...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            page.goto(url)
            page.wait_for_load_state("networkidle")
            print("Page loaded.")

            # Extract the most recent 2026 report links
            reports = extract_2026_reports(page)

            browser.close()
            print("Browser closed.")

        # Download and parse PDFs
        # Process Building Report
        if reports["building"]:
            print(f"\nMost recent Building Report: {reports['building']['url']}")
            filename = extract_filename_from_url(reports["building"]["url"])
            filepath = download_pdf(reports["building"]["url"], filename, download_folder)

            if filepath:
                building_permits = parse_building_pdf(filepath)
                if building_permits:
                    all_permits['Building Permit'] = building_permits
        else:
            print("\nNo 2026 Building Report found.")

        # Process Demolition Report
        if reports["demolition"]:
            print(f"\nMost recent Demolition Report: {reports['demolition']['url']}")
            filename = extract_filename_from_url(reports["demolition"]["url"])
            filepath = download_pdf(reports["demolition"]["url"], filename, download_folder)

            if filepath:
                demolition_permits = parse_demolition_pdf(filepath)
                if demolition_permits:
                    all_permits['Demolition Permit'] = demolition_permits
        else:
            print("\nNo 2026 Demolition Report found.")

        # Save to database
        if all_permits:
            save_permits(all_permits)

            # Print database stats
            try:
                stats = get_permit_stats()
                print(f"\nDatabase now contains {stats['total_permits']} total permits")
            except Exception as e:
                print(f"Could not fetch stats: {e}")
        else:
            print("\nNo permits were extracted.")

        print(f"\n{'='*50}")
        print("PDF scraping complete!")

    # Run portal lookups if not skipped
    if not skip_portal:
        run_portal_lookups()

    print(f"\n{'='*50}")
    print("All scraping complete!")

    return all_permits


if __name__ == "__main__":
    import sys

    skip_pdfs = '--skip-pdfs' in sys.argv or '--portal-only' in sys.argv
    skip_portal = '--skip-portal' in sys.argv or '--pdfs-only' in sys.argv

    if '--help' in sys.argv:
        print("Richmond Scraper")
        print("Usage: python richmond_scraper.py [options]")
        print("")
        print("Options:")
        print("  --skip-pdfs, --portal-only   Skip PDF scraping, only do portal lookups")
        print("  --skip-portal, --pdfs-only   Skip portal lookups, only scrape PDFs")
        print("  --help                       Show this help message")
    else:
        run_scraper(skip_pdfs=skip_pdfs, skip_portal=skip_portal)
