"""
Vancouver Permit Search Scraper
- Extracts permit info from list page (including status)
- Visits each permit detail page to extract all fields
- Saves permits to PostgreSQL database
"""

import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from database import save_permits_to_db, get_permit_stats, get_connection
from geocoder import geocode_permit


def get_today_formatted():
    """Format today's date as 'Mon dd, yyyy' (e.g., 'Feb 01, 2026')"""
    return datetime.now().strftime("%b %d, %Y")


def extract_list_data(page):
    """Extract permit data from the search results list page"""

    js_code = """
    () => {
        const permits = [];
        const rows = document.querySelectorAll('.possegrid tr');

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                // Check if this is a data row (has a link in first cell)
                const link = cells[0]?.querySelector('a');
                if (link) {
                    const permit = {
                        url: link.href,
                        permit_type: cells[1]?.innerText?.trim() || '',
                        permit_number: cells[2]?.innerText?.trim() || '',
                        list_location: cells[3]?.innerText?.trim() || '',
                        list_status: cells[4]?.innerText?.trim() || '',
                        list_created_date: cells[5]?.innerText?.trim() || '',
                        list_issue_date: cells[6]?.innerText?.trim() || '',
                        list_completed_date: cells[7]?.innerText?.trim() || ''
                    };
                    permits.push(permit);
                }
            }
        });

        return permits;
    }
    """

    try:
        return page.evaluate(js_code) or []
    except Exception as e:
        print(f"Error extracting list data: {e}")
        return []


def extract_permit_details(page):
    """Extract all details from a permit detail page"""

    js_code = """
    () => {
        const data = {};
        const mainContent = document.body.innerText;

        // Extract permit number
        const numberMatch = mainContent.match(/([A-Z]{2,3}-\\d{4}-\\d+)/);
        if (numberMatch) data.permit_number = numberMatch[1];

        // Extract permit type
        const permitTypes = [
            'Building Permit Application', 'Building Permit',
            'Sprinkler Permit', 'Electrical Permit', 'Plumbing Permit',
            'Gas Permit', 'Mechanical Permit', 'Development Permit Application',
            'Development Permit', 'Fire Permit', 'Sign & Awning Permit',
            'Tree Permit', 'Occupancy Permit', 'Rezoning Application',
            'Street Use Permit', 'Fire Services Permit', 'Operating Permit',
            'Subdivision Application', 'Temporary Street Occupancy Permit'
        ];
        for (const pType of permitTypes) {
            if (mainContent.includes(pType)) {
                data.permit_type = pType;
                break;
            }
        }

        // Get status from badge
        const statusEl = document.querySelector('.permitStatusDisplay');
        if (statusEl) data.status = statusEl.innerText.trim();

        // Extract dates
        const appDateMatch = mainContent.match(/Application Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (appDateMatch) data.application_date = appDateMatch[1].trim();

        const issueDateMatch = mainContent.match(/Issue Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (issueDateMatch) data.issue_date = issueDateMatch[1].trim();

        const completedDateMatch = mainContent.match(/Completed Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (completedDateMatch) data.completed_date = completedDateMatch[1].trim();

        // Extract Details section fields
        const primaryLocMatch = mainContent.match(/Primary Location:\\s*([^\\n]+)/);
        if (primaryLocMatch) data.primary_location = primaryLocMatch[1].trim();

        const specificLocMatch = mainContent.match(/Specific Location:\\s*([^\\n]+)/);
        if (specificLocMatch) data.specific_location = specificLocMatch[1].trim();

        const workDescMatch = mainContent.match(/Work Description:\\s*([\\s\\S]*?)(?=Type of Work:|Parcels|Related Information|Installation Details|Letters of Assurance|Application Information|Street Use Types|Locations|$)/);
        if (workDescMatch) {
            data.work_description = workDescMatch[1].trim().replace(/\\n+/g, ' ').replace(/\\s+/g, ' ').substring(0, 1000);
        }

        const typeWorkMatch = mainContent.match(/Type of Work:\\s*([^\\n]+)/);
        if (typeWorkMatch) data.type_of_work = typeWorkMatch[1].trim();

        // Extract Type field (used by multiple permit types)
        const typeMatch = mainContent.match(/Details\\s+(?:Scope[^:]*:\\s*[^\\n]*\\s+)?Type:\\s*([^\\n]+)/);
        if (typeMatch) data.type = typeMatch[1].trim();

        // Extract Parcels
        const parcelMatch = mainContent.match(/(\\d{3}-\\d{3}-\\d{3})\\s+([^\\n]+?)\\s+(\\d{3}-\\d{3}-\\d{2}-\\d{4})/);
        if (parcelMatch) {
            data.parcel_id = parcelMatch[1];
            data.parcel_address = parcelMatch[2].trim();
            data.folio_number = parcelMatch[3];
        }

        // Extract Related Information - Contractors
        const contractors = [];
        const contractorTypes = [
            'Sprinkler Contractor', 'Electrical Contractor', 'Gas Contractor',
            'Plumbing Contractor', 'Mechanical Contractor', 'Contractor',
            'Customer', 'Applicant', 'Owner'
        ];
        for (const cType of contractorTypes) {
            const regex = new RegExp(cType + '\\\\s+([^\\\\n]+)', 'g');
            const matches = mainContent.matchAll(regex);
            for (const match of matches) {
                const name = match[1].trim();
                if (name && !name.includes('Click to') && name.length > 2) {
                    contractors.push(name);
                }
            }
        }
        if (contractors.length > 0) {
            data.contractors = [...new Set(contractors)].join('; ');
        }

        // ========== ELECTRICAL PERMIT FIELDS ==========
        const scopeElecMatch = mainContent.match(/Scope of Electrical Work:\\s*([^\\n]+)/);
        if (scopeElecMatch) data.scope_of_electrical_work = scopeElecMatch[1].trim();

        const fsrNameMatch = mainContent.match(/FSR Name:\\s*([^\\n]+)/);
        if (fsrNameMatch) data.fsr_name = fsrNameMatch[1].trim();

        const fsrClassMatch = mainContent.match(/FSR Class Code:\\s*([^\\n]+)/);
        if (fsrClassMatch) data.fsr_class_code = fsrClassMatch[1].trim();

        const serviceIncreaseMatch = mainContent.match(/Service Increase:\\s*([^\\n]+)/);
        if (serviceIncreaseMatch) data.service_increase = serviceIncreaseMatch[1].trim();

        const reconnectServiceMatch = mainContent.match(/Reconnect\\/Relocate Service:\\s*([^\\n]+)/);
        if (reconnectServiceMatch) data.reconnect_relocate_service = reconnectServiceMatch[1].trim();

        const newServiceMatch = mainContent.match(/New Service:\\s*([^\\n]+)/);
        if (newServiceMatch) data.new_service = newServiceMatch[1].trim();

        const voltsMatch = mainContent.match(/Volts:\\s*([^\\n]+)/);
        if (voltsMatch && voltsMatch[1].trim() !== '(None)') data.volts = voltsMatch[1].trim();

        const ampsMatch = mainContent.match(/AMPS:\\s*([^\\n]+)/);
        if (ampsMatch && ampsMatch[1].trim() !== '(None)') data.amps = ampsMatch[1].trim();

        const phaseMatch = mainContent.match(/Phase:\\s*([^\\n]+)/);
        if (phaseMatch && phaseMatch[1].trim() !== '(None)') data.phase = phaseMatch[1].trim();

        const serviceConductorSizeMatch = mainContent.match(/Size of Service Conductor:\\s*([^\\n]+)/);
        if (serviceConductorSizeMatch) data.size_of_service_conductor = serviceConductorSizeMatch[1].trim();

        const serviceConductorMaterialMatch = mainContent.match(/Material of Service conductor:\\s*([^\\n]+)/);
        if (serviceConductorMaterialMatch) data.material_of_service_conductor = serviceConductorMaterialMatch[1].trim();

        const groundingConductorMatch = mainContent.match(/Size of Grounding Conductor:\\s*([^\\n]+)/);
        if (groundingConductorMatch) data.size_of_grounding_conductor = groundingConductorMatch[1].trim();

        const transformerKvaMatch = mainContent.match(/Transformer KVA:\\s*([^\\n]+)/);
        if (transformerKvaMatch) data.transformer_kva = transformerKvaMatch[1].trim();

        const faultCurrentMatch = mainContent.match(/Available Fault Current:\\s*([^\\n]+)/);
        if (faultCurrentMatch) data.available_fault_current = faultCurrentMatch[1].trim();

        const serviceBoxMatch = mainContent.match(/Service Box Interrupting Capacity:\\s*([^\\n]+)/);
        if (serviceBoxMatch) data.service_box_interrupting_capacity = serviceBoxMatch[1].trim();

        const installValueMatch = mainContent.match(/Total Installation Value[^:]*:\\s*([\\d,\\.]+)/);
        if (installValueMatch) data.total_installation_value = installValueMatch[1].trim();

        const tempPowerMatch = mainContent.match(/Temporary Power:\\s*([^\\n]+)/);
        if (tempPowerMatch) data.temporary_power = tempPowerMatch[1].trim();

        // ========== GAS PERMIT FIELDS ==========
        const bldgDevPermitMatch = mainContent.match(/Building \\/ Development Permit Number:\\s*([^\\n]+)/);
        if (bldgDevPermitMatch) data.building_development_permit_number = bldgDevPermitMatch[1].trim();

        const totalPipingMatch = mainContent.match(/Total Piping Length:\\s*([^\\n]+)/);
        if (totalPipingMatch) data.total_piping_length = totalPipingMatch[1].trim();

        const replacementAppliancesMatch = mainContent.match(/Total Replacement Appliances:\\s*([^\\n]+)/);
        if (replacementAppliancesMatch) data.total_replacement_appliances = replacementAppliancesMatch[1].trim();

        const newAppliancesMatch = mainContent.match(/Total New Appliances:\\s*([^\\n]+)/);
        if (newAppliancesMatch) data.total_new_appliances = newAppliancesMatch[1].trim();

        const noMetersMatch = mainContent.match(/No\\. of Meters:\\s*([^\\n]+)/);
        if (noMetersMatch) data.no_of_meters = noMetersMatch[1].trim();

        const btuLoadMatch = mainContent.match(/Current BTU \\/ HR Load Before Additions:\\s*([^\\n]+)/);
        if (btuLoadMatch) data.current_btu_hr_load = btuLoadMatch[1].trim();

        const ventGasMatch = mainContent.match(/Vent, Gas valve or Furnace Plenum:\\s*([^\\n]+)/);
        if (ventGasMatch) data.vent_gas_valve_furnace_plenum = ventGasMatch[1].trim();

        const newGasServiceMatch = mainContent.match(/New Gas Service\\?:\\s*([^\\n]+)/);
        if (newGasServiceMatch) data.new_gas_service = newGasServiceMatch[1].trim();

        const gasUtilityMatch = mainContent.match(/Who is the Gas Utility provider\\?:\\s*([^\\n]+)/);
        if (gasUtilityMatch) data.gas_utility_provider = gasUtilityMatch[1].trim();

        // ========== MECHANICAL PERMIT FIELDS ==========
        const scopeMechMatch = mainContent.match(/Scope:\\s*([^\\n]+)/);
        if (scopeMechMatch) data.scope = scopeMechMatch[1].trim();

        const heatLossMatch = mainContent.match(/Combined total heat loss load \\(kW\\):\\s*([^\\n]+)/);
        if (heatLossMatch) data.combined_heat_loss_load_kw = heatLossMatch[1].trim();

        const heatOutputMatch = mainContent.match(/Combined output of heating appliances at -7 deg\\.? day:\\s*([^\\n]+)/);
        if (heatOutputMatch) data.combined_output_heating_appliances = heatOutputMatch[1].trim();

        const heatPumpsMatch = mainContent.match(/Heat pumps:\\s*([^\\n]+)/);
        if (heatPumpsMatch) data.heat_pumps = heatPumpsMatch[1].trim();

        // ========== PLUMBING PERMIT FIELDS ==========
        const pipingLengthMatch = mainContent.match(/Piping Length \\(Metres\\):\\s*([^\\n]+)/);
        if (pipingLengthMatch) data.piping_length_metres = pipingLengthMatch[1].trim();

        const totalFixturesMatch = mainContent.match(/Total number of fixtures:\\s*([^\\n]+)/);
        if (totalFixturesMatch) data.total_number_of_fixtures = totalFixturesMatch[1].trim();

        // ========== SPRINKLER PERMIT FIELDS ==========
        const sprinklerFields = [
            'Backflow Preventer(s)',
            'Dual Check Valve(s) flow through system',
            'Fire Hydrant(s)',
            'Fire Main Length',
            'Fire Pump(s)',
            'Hose Cabinet(s)',
            'Hose Outlet(s)',
            'Sprinkler Head(s)',
            'Standpipe Riser(s)',
            'Wet & Dry Outlet(s)',
            'Wet & Dry Standpipes'
        ];

        for (const field of sprinklerFields) {
            const regex = new RegExp(field.replace(/[()]/g, '\\\\$&') + ':\\\\s*(\\\\d+)');
            const match = mainContent.match(regex);
            if (match) {
                const key = field.toLowerCase()
                    .replace(/[()]/g, '')
                    .replace(/\\s+/g, '_')
                    .replace(/&/g, 'and');
                data[key] = match[1];
            }
        }

        // ========== OCCUPANCY PERMIT FIELDS ==========
        const occupancyTypeMatch = mainContent.match(/Occupancy Type:\\s*([^\\n]+)/);
        if (occupancyTypeMatch) data.occupancy_type = occupancyTypeMatch[1].trim();

        const useOfBuildingMatch = mainContent.match(/Use of Building\\/Premises:\\s*([^\\n]+)/);
        if (useOfBuildingMatch) data.use_of_building_premises = useOfBuildingMatch[1].trim();

        const proposedOccDateMatch = mainContent.match(/Proposed Occupancy Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (proposedOccDateMatch) data.proposed_occupancy_date = proposedOccDateMatch[1].trim();

        // ========== SIGN & AWNING PERMIT FIELDS ==========
        const scopePermitMatch = mainContent.match(/Scope of the Permit:\\s*([^\\n]+)/);
        if (scopePermitMatch) data.scope_of_permit = scopePermitMatch[1].trim();

        const signTypeMatch = mainContent.match(/Sign Type:\\s*([^\\n]+)/);
        if (signTypeMatch) data.sign_type = signTypeMatch[1].trim();

        const typeOfSignMatch = mainContent.match(/Type of Sign:\\s*([^\\n]+)/);
        if (typeOfSignMatch) data.type_of_sign = typeOfSignMatch[1].trim();

        const reqElecConnMatch = mainContent.match(/Requires Electrical Connection:\\s*([^\\n]+)/);
        if (reqElecConnMatch) data.requires_electrical_connection = reqElecConnMatch[1].trim();

        const weightMatch = mainContent.match(/Weight \\(kg\\):\\s*([^\\n]+)/);
        if (weightMatch) data.weight_kg = weightMatch[1].trim();

        const lettersAssuranceMatch = mainContent.match(/Letters of Assurance:\\s*([^\\n]+)/);
        if (lettersAssuranceMatch) data.letters_of_assurance = lettersAssuranceMatch[1].trim();

        const tempUseStartMatch = mainContent.match(/Temporary Use Start Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (tempUseStartMatch) data.temporary_use_start_date = tempUseStartMatch[1].trim();

        const tempUseEndMatch = mainContent.match(/Temporary Use End Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (tempUseEndMatch) data.temporary_use_end_date = tempUseEndMatch[1].trim();

        // ========== FIRE SERVICES PERMIT FIELDS ==========
        // scope_of_permit already captured above

        // ========== TREE PERMIT FIELDS ==========
        const reqTreesMatch = mainContent.match(/Requested No\\. of Trees to be removed:\\s*([^\\n]+)/);
        if (reqTreesMatch) data.requested_trees_to_remove = reqTreesMatch[1].trim();

        const appTreesMatch = mainContent.match(/Approved Number of Trees to be removed:\\s*([^\\n]+)/);
        if (appTreesMatch) data.approved_trees_to_remove = appTreesMatch[1].trim();

        // ========== STREET USE PERMIT FIELDS ==========
        const relatedPermitMatch = mainContent.match(/Related Permit Number:\\s*([^\\n]+)/);
        if (relatedPermitMatch) data.related_permit_number = relatedPermitMatch[1].trim();

        // Extract Street Use Types
        const streetUseTypesMatch = mainContent.match(/Street Use Types\\s+([\\s\\S]*?)(?=Locations|Related Information|$)/);
        if (streetUseTypesMatch) {
            const typesText = streetUseTypesMatch[1].trim();
            const types = typesText.split(/\\n/).map(t => t.trim()).filter(t => t && !t.includes('Parcel'));
            if (types.length > 0) data.street_use_types = types.join('; ');
        }

        // ========== SUBDIVISION APPLICATION FIELDS ==========
        const subdivisionTypeMatch = mainContent.match(/Subdivision Type:\\s*([^\\n]+)/);
        if (subdivisionTypeMatch) data.subdivision_type = subdivisionTypeMatch[1].trim();

        // ========== TEMPORARY STREET OCCUPANCY PERMIT FIELDS ==========
        const permitPurposeMatch = mainContent.match(/Permit Purpose:\\s*([^\\n]+)/);
        if (permitPurposeMatch) data.permit_purpose = permitPurposeMatch[1].trim();

        const fullPartTimeMatch = mainContent.match(/Full\\/Part Time:\\s*([^\\n]+)/);
        if (fullPartTimeMatch) data.full_part_time = fullPartTimeMatch[1].trim();

        const shortLongTermMatch = mainContent.match(/Short\\/Long Term:\\s*([^\\n]+)/);
        if (shortLongTermMatch) data.short_long_term = shortLongTermMatch[1].trim();

        const addSignageMatch = mainContent.match(/Additional Signage Required:\\s*([^\\n]+)/);
        if (addSignageMatch) data.additional_signage_required = addSignageMatch[1].trim();

        const startDateMatch = mainContent.match(/Start Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (startDateMatch) data.start_date = startDateMatch[1].trim();

        const endDateMatch = mainContent.match(/End Date:\\s*([A-Z][a-z]{2},?\\s+\\d{1,2},\\s+\\d{4})/);
        if (endDateMatch) data.end_date = endDateMatch[1].trim();

        const utilityCompanyMatch = mainContent.match(/Utility Company:\\s*([^\\n]+)/);
        if (utilityCompanyMatch) data.utility_company = utilityCompanyMatch[1].trim();

        // ========== DEVELOPMENT PERMIT FIELDS ==========
        const zoningCodeMatch = mainContent.match(/Zoning Code\\s+([^\\n]+)/);
        if (zoningCodeMatch) data.zoning_code = zoningCodeMatch[1].trim();

        // ========== REZONING APPLICATION FIELDS ==========
        const permitLocationMatch = mainContent.match(/Permit Location:\\s*([^\\n]+)/);
        if (permitLocationMatch) data.permit_location = permitLocationMatch[1].trim();

        const jobLocationMatch = mainContent.match(/Job Location:\\s*([^\\n]+)/);
        if (jobLocationMatch) data.job_location = jobLocationMatch[1].trim();

        return data;
    }
    """

    try:
        page.wait_for_load_state("networkidle")
        return page.evaluate(js_code) or {}
    except Exception as e:
        print(f"Error extracting permit details: {e}")
        return {}


def save_permits_by_type(permits_by_type):
    """Save permits to PostgreSQL database and geocode them"""

    print("\nSaving permits to database...")
    results = save_permits_to_db(permits_by_type)

    total_saved = sum(results.values())
    print(f"\nTotal permits saved to database: {total_saved}")

    # Geocode newly saved permits
    print("\nGeocoding new permits...")
    geocode_new_permits()

    return results


def geocode_new_permits():
    """Geocode all permits that don't have coordinates yet"""
    conn = get_connection()
    cur = conn.cursor()

    # Get permits that need geocoding (from Vancouver)
    cur.execute("""
        SELECT id, permit_number, primary_location, source_city
        FROM permits
        WHERE (geocode_status = 'pending' OR geocode_status IS NULL)
        AND (source_city = 'Vancouver' OR source_city IS NULL)
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
        print(f"  {permit_number}: {address[:50]}..." if len(address or '') > 50 else f"  {permit_number}: {address}")
        geocode_permit(permit_id, address, city or 'Vancouver', delay=1.0)


def run_scraper():
    """Main scraper function"""

    url = "https://plposweb.vancouver.ca/Public/Default.aspx?PossePresentation=PermitSearchByDate&IconName=form_yellow_search.png"

    with sync_playwright() as p:
        # Launch browser (set headless=True for background execution)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Opening permit search page...")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Get today's date in the required format
        today_date = get_today_formatted()
        print(f"Today's date: {today_date}")

        # Enter today's date in Created Date From field
        created_date_field = page.locator("input[id*='CreatedDateFrom']")
        created_date_field.fill("")
        created_date_field.fill(today_date)
        print(f"Entered date: {today_date}")

        # Click Search button
        search_button = page.locator("[id*='PerformSearch']")
        search_button.click()
        print("Search button clicked")

        # Wait for results
        page.wait_for_load_state("networkidle")
        print("Search completed!")

        # Extract data from the list page first
        list_data = extract_list_data(page)
        print(f"Found {len(list_data)} permits in list")

        if not list_data:
            print("No permits found.")
            browser.close()
            return {}

        # Process each permit and collect by type
        permits_by_type = {}

        for i, list_permit in enumerate(list_data):
            permit_type = list_permit.get('permit_type', 'Unknown')
            permit_number = list_permit.get('permit_number', 'Unknown')
            permit_url = list_permit.get('url', '')

            print(f"\nProcessing {i+1}/{len(list_data)}: {permit_type} {permit_number}")

            if not permit_url:
                print("  No URL found, skipping")
                continue

            try:
                # Visit permit detail page
                page.goto(permit_url)
                page.wait_for_load_state("networkidle")

                # Extract details
                detail_data = extract_permit_details(page)

                # Merge list data with detail data (list data takes precedence for status)
                permit_data = {**detail_data}
                permit_data['url'] = permit_url
                permit_data['list_status'] = list_permit.get('list_status', '')
                permit_data['list_location'] = list_permit.get('list_location', '')
                permit_data['list_created_date'] = list_permit.get('list_created_date', '')
                permit_data['list_issue_date'] = list_permit.get('list_issue_date', '')
                permit_data['list_completed_date'] = list_permit.get('list_completed_date', '')

                # Use the type from the list (more reliable)
                permit_data['permit_type'] = permit_type

                # Add to type group
                if permit_type not in permits_by_type:
                    permits_by_type[permit_type] = []
                permits_by_type[permit_type].append(permit_data)

                print(f"  Extracted: {permit_data.get('primary_location', 'N/A')}")

            except Exception as e:
                print(f"  Error: {e}")
                continue

        browser.close()
        print("\nBrowser closed.")

    # Save to PostgreSQL database
    if permits_by_type:
        save_permits_by_type(permits_by_type)

        # Print database stats
        try:
            stats = get_permit_stats()
            print(f"\nDatabase now contains {stats['total_permits']} total permits")
        except Exception as e:
            print(f"Could not fetch stats: {e}")
    else:
        print("\nNo permits were extracted.")

    return permits_by_type


if __name__ == "__main__":
    run_scraper()
