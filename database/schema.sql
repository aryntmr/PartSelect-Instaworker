-- PartSelect Chatbot Database Schema
-- PostgreSQL 14+

-- Enable UUID extension for unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- TABLE 1: Parts
-- ==========================================
CREATE TABLE IF NOT EXISTS parts (
    -- Primary Key
    part_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Part Identification
    part_name VARCHAR(255) NOT NULL,
    manufacturer_part_number VARCHAR(100) UNIQUE NOT NULL,
    part_number VARCHAR(100),  -- PartSelect internal number
    brand VARCHAR(100),
    appliance_type VARCHAR(50),  -- 'refrigerator', 'dishwasher', etc.

    -- Pricing
    current_price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2) NOT NULL,
    has_discount BOOLEAN GENERATED ALWAYS AS (original_price > current_price) STORED,
    discount_percentage DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE
            WHEN original_price > current_price
            THEN ((original_price - current_price) / original_price * 100)
            ELSE 0
        END
    ) STORED,

    -- Reviews & Ratings
    rating DECIMAL(3, 2) CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER DEFAULT 0,

    -- Product Details
    description TEXT,
    symptoms TEXT,  -- Pipe-separated symptoms
    replacement_parts TEXT,  -- Pipe-separated part numbers

    -- Installation
    installation_difficulty VARCHAR(50),  -- 'Easy', 'Moderate', 'Difficult'
    installation_time VARCHAR(50),  -- '15-30 mins', '1-2 hours', etc.

    -- Availability
    delivery_time VARCHAR(100),
    availability VARCHAR(50),  -- 'In Stock', 'Out of Stock', etc.

    -- Media
    image_url TEXT,
    video_url TEXT,
    product_url TEXT NOT NULL,

    -- Metadata
    compatible_models_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLE 2: Models (Appliance Models)
-- ==========================================
CREATE TABLE IF NOT EXISTS models (
    -- Primary Key
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model Identification
    model_number VARCHAR(100) UNIQUE NOT NULL,
    model_url TEXT,

    -- Model Details (can be enriched later)
    brand VARCHAR(100),
    appliance_type VARCHAR(50),
    description TEXT,

    -- Metadata
    parts_count INTEGER DEFAULT 0,  -- Count of compatible parts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLE 3: Part-Model Mapping (Junction Table)
-- ==========================================
CREATE TABLE IF NOT EXISTS part_model_mapping (
    -- Composite Primary Key
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_id UUID NOT NULL REFERENCES parts(part_id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES models(model_id) ON DELETE CASCADE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique combinations
    UNIQUE(part_id, model_id)
);

-- ==========================================
-- INDEXES for Performance
-- ==========================================

-- Parts table indexes
CREATE INDEX idx_parts_appliance_type ON parts(appliance_type);
CREATE INDEX idx_parts_brand ON parts(brand);
CREATE INDEX idx_parts_price ON parts(current_price);
CREATE INDEX idx_parts_discount ON parts(has_discount) WHERE has_discount = TRUE;
CREATE INDEX idx_parts_rating ON parts(rating DESC);
CREATE INDEX idx_parts_manufacturer_part_number ON parts(manufacturer_part_number);
CREATE INDEX idx_parts_symptoms ON parts USING gin(to_tsvector('english', symptoms));
CREATE INDEX idx_parts_description ON parts USING gin(to_tsvector('english', description));

-- Models table indexes
CREATE INDEX idx_models_model_number ON models(model_number);
CREATE INDEX idx_models_brand ON models(brand);

-- Part-Model mapping indexes
CREATE INDEX idx_mapping_part_id ON part_model_mapping(part_id);
CREATE INDEX idx_mapping_model_id ON part_model_mapping(model_id);

-- ==========================================
-- FUNCTIONS & TRIGGERS
-- ==========================================

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for parts table
CREATE TRIGGER update_parts_updated_at
    BEFORE UPDATE ON parts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for models table
CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update parts_count in models table
CREATE OR REPLACE FUNCTION update_model_parts_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE models
        SET parts_count = parts_count + 1
        WHERE model_id = NEW.model_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE models
        SET parts_count = parts_count - 1
        WHERE model_id = OLD.model_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain parts_count
CREATE TRIGGER update_model_parts_count_trigger
    AFTER INSERT OR DELETE ON part_model_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_model_parts_count();

-- ==========================================
-- VIEWS for Common Queries
-- ==========================================

-- View: Parts with discount
CREATE OR REPLACE VIEW discounted_parts AS
SELECT
    part_id,
    part_name,
    manufacturer_part_number,
    brand,
    original_price,
    current_price,
    discount_percentage,
    rating,
    product_url
FROM parts
WHERE has_discount = TRUE
ORDER BY discount_percentage DESC;

-- View: Top-rated parts
CREATE OR REPLACE VIEW top_rated_parts AS
SELECT
    part_id,
    part_name,
    manufacturer_part_number,
    brand,
    rating,
    review_count,
    current_price,
    product_url
FROM parts
WHERE rating IS NOT NULL
ORDER BY rating DESC, review_count DESC
LIMIT 50;

-- View: Parts with compatible models count
CREATE OR REPLACE VIEW parts_with_models AS
SELECT
    p.part_id,
    p.part_name,
    p.manufacturer_part_number,
    p.brand,
    p.appliance_type,
    p.current_price,
    p.rating,
    p.compatible_models_count,
    COUNT(pmm.model_id) as actual_model_count
FROM parts p
LEFT JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
GROUP BY p.part_id
ORDER BY actual_model_count DESC;

-- ==========================================
-- COMMENTS for Documentation
-- ==========================================

COMMENT ON TABLE parts IS 'Main parts catalog with pricing, ratings, and details';
COMMENT ON TABLE models IS 'Appliance models that are compatible with parts';
COMMENT ON TABLE part_model_mapping IS 'Many-to-many relationship between parts and models';

COMMENT ON COLUMN parts.has_discount IS 'Computed: TRUE if original_price > current_price';
COMMENT ON COLUMN parts.discount_percentage IS 'Computed: Percentage discount';
COMMENT ON COLUMN parts.symptoms IS 'Pipe-separated list of repair symptoms from customer stories';
COMMENT ON COLUMN parts.replacement_parts IS 'Pipe-separated list of alternative part numbers';
