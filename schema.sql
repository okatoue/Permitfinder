-- Permit Finder Database Schema
-- PostgreSQL database for storing Vancouver permit data

-- Drop existing tables if they exist (for fresh setup)
DROP TABLE IF EXISTS permits CASCADE;
DROP TYPE IF EXISTS permit_status CASCADE;

-- Create enum for permit status
CREATE TYPE permit_status AS ENUM (
    'Application Received',
    'In Review',
    'Pending',
    'Approved',
    'Issued',
    'Completed',
    'Cancelled',
    'Expired',
    'On Hold',
    'Unknown'
);

-- Main permits table
-- Uses JSONB for type-specific fields to allow flexibility across permit types
CREATE TABLE permits (
    id SERIAL PRIMARY KEY,

    -- Core identification
    permit_number VARCHAR(50) NOT NULL UNIQUE,
    permit_type VARCHAR(100) NOT NULL,

    -- Status tracking
    status VARCHAR(100),
    list_status VARCHAR(100),

    -- Important dates
    application_date DATE,
    issue_date DATE,
    completed_date DATE,
    list_created_date DATE,
    list_issue_date DATE,
    list_completed_date DATE,

    -- Location information
    primary_location TEXT,
    specific_location TEXT,
    list_location TEXT,

    -- Property details
    parcel_id VARCHAR(50),
    parcel_address TEXT,
    folio_number VARCHAR(50),

    -- Work details
    work_description TEXT,
    type_of_work VARCHAR(255),

    -- Contractors (stored as text, semicolon-separated)
    contractors TEXT,

    -- Source URL
    url TEXT,

    -- Type-specific fields stored as JSONB for flexibility
    -- This allows different permit types to have different fields
    -- without requiring schema changes
    type_specific_data JSONB DEFAULT '{}',

    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Source tracking
    source_city VARCHAR(100) DEFAULT 'Vancouver',

    -- Geocoded coordinates (pre-computed for fast map loading)
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    geocode_status VARCHAR(20) DEFAULT 'pending'  -- pending, success, failed
);

-- Indexes for common queries
CREATE INDEX idx_permits_permit_type ON permits(permit_type);
CREATE INDEX idx_permits_status ON permits(status);
CREATE INDEX idx_permits_application_date ON permits(application_date);
CREATE INDEX idx_permits_issue_date ON permits(issue_date);
CREATE INDEX idx_permits_primary_location ON permits(primary_location);
CREATE INDEX idx_permits_scraped_at ON permits(scraped_at);

-- GIN index for JSONB queries on type-specific data
CREATE INDEX idx_permits_type_specific_data ON permits USING GIN (type_specific_data);

-- Full-text search index on work description
CREATE INDEX idx_permits_work_description_fts ON permits USING GIN (to_tsvector('english', COALESCE(work_description, '')));

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_permits_updated_at
    BEFORE UPDATE ON permits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for electrical permits
CREATE OR REPLACE VIEW electrical_permits AS
SELECT
    id, permit_number, status, application_date, issue_date, completed_date,
    primary_location, specific_location, work_description, contractors, url,
    type_specific_data->>'scope_of_electrical_work' AS scope_of_electrical_work,
    type_specific_data->>'fsr_name' AS fsr_name,
    type_specific_data->>'fsr_class_code' AS fsr_class_code,
    type_specific_data->>'volts' AS volts,
    type_specific_data->>'amps' AS amps,
    type_specific_data->>'phase' AS phase,
    type_specific_data->>'temporary_power' AS temporary_power,
    type_specific_data->>'total_installation_value' AS total_installation_value,
    scraped_at
FROM permits
WHERE permit_type = 'Electrical Permit';

-- View for building permits
CREATE OR REPLACE VIEW building_permits AS
SELECT
    id, permit_number, status, application_date, issue_date, completed_date,
    primary_location, specific_location, work_description, type_of_work,
    contractors, url, scraped_at
FROM permits
WHERE permit_type IN ('Building Permit', 'Building Permit Application');

-- View for gas permits
CREATE OR REPLACE VIEW gas_permits AS
SELECT
    id, permit_number, status, application_date, issue_date, completed_date,
    primary_location, specific_location, work_description, contractors, url,
    type_specific_data->>'total_piping_length' AS total_piping_length,
    type_specific_data->>'total_replacement_appliances' AS total_replacement_appliances,
    type_specific_data->>'total_new_appliances' AS total_new_appliances,
    type_specific_data->>'no_of_meters' AS no_of_meters,
    type_specific_data->>'gas_utility_provider' AS gas_utility_provider,
    scraped_at
FROM permits
WHERE permit_type = 'Gas Permit';

-- View for plumbing permits
CREATE OR REPLACE VIEW plumbing_permits AS
SELECT
    id, permit_number, status, application_date, issue_date, completed_date,
    primary_location, specific_location, work_description, contractors, url,
    type_specific_data->>'piping_length_metres' AS piping_length_metres,
    type_specific_data->>'total_number_of_fixtures' AS total_number_of_fixtures,
    scraped_at
FROM permits
WHERE permit_type = 'Plumbing Permit';

-- View for mechanical permits
CREATE OR REPLACE VIEW mechanical_permits AS
SELECT
    id, permit_number, status, application_date, issue_date, completed_date,
    primary_location, specific_location, work_description, contractors, url,
    type_specific_data->>'scope' AS scope,
    type_specific_data->>'combined_heat_loss_load_kw' AS combined_heat_loss_load_kw,
    type_specific_data->>'heat_pumps' AS heat_pumps,
    scraped_at
FROM permits
WHERE permit_type = 'Mechanical Permit';

-- View for daily permit summary
CREATE OR REPLACE VIEW daily_permit_summary AS
SELECT
    DATE(scraped_at) AS scrape_date,
    permit_type,
    COUNT(*) AS permit_count,
    COUNT(DISTINCT primary_location) AS unique_locations
FROM permits
GROUP BY DATE(scraped_at), permit_type
ORDER BY scrape_date DESC, permit_count DESC;

-- Helpful comment
COMMENT ON TABLE permits IS 'Main table storing all Vancouver permit data. Type-specific fields are stored in the type_specific_data JSONB column.';
COMMENT ON COLUMN permits.type_specific_data IS 'JSONB column storing permit-type-specific fields (electrical specs, gas details, etc.)';
