-- Companies table
CREATE TABLE Companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) UNIQUE NOT NULL,
    company_summary TEXT NOT NULL, -- display under company dashboard
    website_url VARCHAR(255),
    industry VARCHAR(50),
    cso_linkedin_url VARCHAR(255), -- LinkedIn URL of the CSO
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to retrieve timestamp when update is made to Companies
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_timestamp
BEFORE UPDATE ON Companies
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Metrics table that stores all relevent scorecard data
CREATE TABLE SustainabilityMetrics (
    metric_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    owns_cng_fleet BOOLEAN NOT NULL DEFAULT FALSE, -- Yes/No
    cng_fleet_size_range INT NOT NULL DEFAULT 0, -- 0 = None, 1 = 1-10, 2 = 11-50, 3 = 51+,
    cng_fleet_size_actual INT NOT NULL DEFAULT 0,
    total_fleet_size INT NOT NULL DEFAULT 0,
    emission_report BOOLEAN NOT NULL DEFAULT FALSE, -- Yes/No
    emission_goals INT NOT NULL DEFAULT 0, -- 0 = No, 1 = Goal Mentioned, 2 = Goal with timeline
    alt_fuels BOOLEAN NOT NULL DEFAULT FALSE, -- Yes/No
    clean_energy_partners BOOLEAN NOT NULL DEFAULT FALSE, -- Yes/No
    regulatory_pressure BOOLEAN NOT NULL DEFAULT FALSE, -- Yes/No
    cng_adopt_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES Companies(company_id) ON DELETE CASCADE,
    UNIQUE (company_id),
    CONSTRAINT valid_cng_fleet_size_range CHECK (cng_fleet_size_range IN (0, 1, 2, 3)),
    CONSTRAINT valid_emission_goal CHECK (emission_goals in (0, 1, 2))
);

-- Sources for a given metric
CREATE TABLE MetricSources (
    metric_source_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    contribution_text TEXT, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    UNIQUE (metric_id, metric_name),
    CONSTRAINT valid_metric_name CHECK (metric_name IN (
        'owns_cng_fleet', -- "CNG Fleet Presence"
        'cng_fleet_size_range', -- "CNG Fleet Presence"
        'cng_fleet_size_actual', -- "CNG Fleet Size"
        'total_fleet_size', -- "CNG Fleet Presence"
        'emission_report', -- "Emissions Reporting"
        'emission_goals', -- "Target Emission Goals"
        'alt_fuels', -- "Alternative Fuels"
        'clean_energy_partners', -- "Clean Energy"
        'regulatory_pressure' -- "Regulatory Pressure"
    ))
);

CREATE TABLE FleetSummary (
    fleet_summary_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL,
    metric_source_id INT,
    metric_name VARCHAR(50) NOT NULL DEFAULT 'owns_cng_fleet',
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    FOREIGN KEY (metric_source_id) REFERENCES MetricSources(metric_source_id) ON DELETE SET NULL,
    CONSTRAINT valid_metric_name CHECK (metric_name IN ('owns_cng_fleet'))
);

CREATE TABLE EmissionsSummary (
    emissions_summary_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL,
    metric_source_id INT,
    metric_name VARCHAR(50) NOT NULL DEFAULT 'emission_report',
    emissions_summary TEXT NOT NULL,
    emissions_goals_summary TEXT NOT NULL,
    
    current_emissions INT DEFAULT 0,
    target_year INT DEFAULT 2040,
    target_emissions INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    FOREIGN KEY (metric_source_id) REFERENCES MetricSources(metric_source_id) ON DELETE SET NULL,
    CONSTRAINT valid_metric_name CHECK (metric_name IN ('emission_report'))
);

CREATE TABLE AltFuelsSummary (
    alt_fuels_summary_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL, 
    metric_source_id INT,
    metric_name VARCHAR(50) NOT NULL DEFAULT 'alt_fuels',
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    FOREIGN KEY (metric_source_id) REFERENCES MetricSources(metric_source_id) ON DELETE SET NULL,
    CONSTRAINT alt_fuels_summary_metric_name CHECK (metric_name = 'alt_fuels')
);

CREATE TABLE CleanEnergyPartnersSummary (
    clean_energy_summary_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL,
    metric_source_id INT,
    metric_name VARCHAR(50) NOT NULL DEFAULT 'clean_energy_partners',
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    FOREIGN KEY (metric_source_id) REFERENCES MetricSources(metric_source_id) ON DELETE SET NULL,
    CONSTRAINT clean_energy_summary_metric_name CHECK (metric_name = 'clean_energy_partners')
);

CREATE TABLE RegulatoryPressureSummary (
    regulatory_pressure_summary_id SERIAL PRIMARY KEY,
    metric_id INT NOT NULL,
    metric_source_id INT,
    metric_name VARCHAR(50) NOT NULL DEFAULT 'regulatory_pressure',
    summary_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES SustainabilityMetrics(metric_id) ON DELETE CASCADE,
    FOREIGN KEY (metric_source_id) REFERENCES MetricSources(metric_source_id) ON DELETE SET NULL,
    CONSTRAINT regulatory_pressure_summary_metric_name CHECK (metric_name = 'regulatory_pressure')
);

-- Might need to add boolen for webscraper finishing