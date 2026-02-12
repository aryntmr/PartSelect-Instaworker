# SQL Search Tool - Description & Field Reference

## Tool Description

**Tool Name:** `sql_search_tool`

**Purpose:** Execute SQL queries against the PostgreSQL database to retrieve structured information about appliance parts, compatible models, and part-model compatibility relationships. This tool provides direct access to the parts catalog, pricing information, ratings, installation details, availability, and compatibility mappings for refrigerator and dishwasher parts.

**Best Practices:**
- Always use `LIMIT` clause to prevent returning too many results (recommended: 10-50 rows)
- Use `ILIKE` for case-insensitive text searches
- Use `ORDER BY` to sort results by relevance (rating, price, discount_percentage, etc.)
- When searching by model compatibility, always JOIN through `part_model_mapping` table
- Use `WHERE rating IS NOT NULL` when filtering by ratings to exclude parts without reviews
- For symptom searches, use `ILIKE '%keyword%'` to match partial text in the `symptoms` field
- Check `availability` field to ensure parts are in stock if user requests available parts
- Use computed fields like `has_discount` and `discount_percentage` for discount-related queries

## Database Field Descriptions

### **Table: parts** (Main Product Catalog)

- **part_id** (UUID, Primary Key): Unique internal database identifier for each part record; automatically generated; used for JOINs with part_model_mapping table

- **part_name** (VARCHAR 255, NOT NULL): Human-readable name/title of the part as displayed on PartSelect website (e.g., "Door Shelf Bin", "Ice Maker Assembly", "Water Inlet Valve")

- **manufacturer_part_number** (VARCHAR 100, UNIQUE, NOT NULL): Official part number assigned by the manufacturer (e.g., "WPW10321304"); unique identifier used by manufacturers and on physical part labels; use this for exact part identification

- **part_number** (VARCHAR 100): PartSelect's internal part number/SKU (e.g., "PS11752778"); typically starts with "PS"; used on PartSelect website URLs and product pages

- **brand** (VARCHAR 100): Manufacturer or brand name that produces this part (e.g., "Whirlpool", "GE", "Samsung", "LG", "Frigidaire", "Bosch"); useful for filtering parts by specific brands

- **appliance_type** (VARCHAR 50): Category of appliance this part is designed for; values are either "refrigerator" or "dishwasher" (scope is limited to these two types only)

- **current_price** (DECIMAL 10,2, NOT NULL): Current selling price of the part in USD; this is the price customers pay; may be lower than original_price if there's an active discount

- **original_price** (DECIMAL 10,2, NOT NULL): Manufacturer's suggested retail price (MSRP) or regular price before any discounts in USD; used to calculate discount percentage

- **has_discount** (BOOLEAN, GENERATED/COMPUTED): Automatically computed boolean flag indicating whether part is currently on sale; TRUE if original_price > current_price, FALSE otherwise; use this to filter discounted/sale parts

- **discount_percentage** (DECIMAL 5,2, GENERATED/COMPUTED): Automatically calculated percentage discount from original price; formula: ((original_price - current_price) / original_price * 100); 0 if no discount; useful for sorting by best deals

- **rating** (DECIMAL 3,2): Average customer rating score from 0 to 5 stars; based on customer reviews; NULL if no reviews exist; higher ratings indicate better customer satisfaction; use for sorting by quality

- **review_count** (INTEGER, DEFAULT 0): Total number of customer reviews submitted for this part; higher count indicates more reliable/popular part; use with rating to assess part quality and popularity

- **description** (TEXT): Detailed text description of what the part is, what it does, and what problems it solves; may include technical specifications, dimensions, materials, and usage information; useful for answering "what is this part?" questions

- **symptoms** (TEXT): Pipe-separated list of common appliance problems/symptoms that this part can fix (e.g., "Ice maker not working|Refrigerator leaking|Water dispenser not working"); extracted from customer repair stories; critical for symptom-based part searches

- **replacement_parts** (TEXT): Pipe-separated list of alternative/equivalent part numbers that can be used as replacements; includes both manufacturer part numbers and PartSelect part numbers; useful when primary part is out of stock

- **installation_difficulty** (VARCHAR 50): Difficulty level rating for installing this part; typical values: "Easy", "Moderate", "Difficult", "Hard"; helps users assess if they can DIY or need professional help

- **installation_time** (VARCHAR 50): Estimated time required to install/replace this part (e.g., "15-30 minutes", "30-60 minutes", "1-2 hours"); helps users plan repair timeline

- **delivery_time** (VARCHAR 100): Estimated shipping/delivery timeframe after order placement (e.g., "2-3 business days", "1-2 weeks", "Same day shipping available"); helps users know when they'll receive the part

- **availability** (VARCHAR 50): Current stock status of the part; typical values: "In Stock", "Out of Stock", "Backordered", "Limited Stock"; critical for determining if part can be ordered immediately

- **image_url** (TEXT): Full URL to the product image/photo; typically hosted on PartSelect CDN; use for displaying part visually to users; may be empty if no image available

- **video_url** (TEXT): Full URL to installation/repair video tutorial (often YouTube); provides step-by-step visual guidance; may be empty if no video exists; highly valuable for DIY users

- **product_url** (TEXT, NOT NULL): Full URL to the part's product page on PartSelect.com website; users can click this link to view full details, purchase, or check real-time availability

- **compatible_models_count** (INTEGER, DEFAULT 0): Cached count of how many appliance models this part is compatible with; higher number means part fits more models (more universal); actual compatibility list is in part_model_mapping table

- **created_at** (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Timestamp when this part record was first inserted into database; useful for tracking when data was scraped/added

- **updated_at** (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Timestamp of last modification to this part record; automatically updated by trigger on any UPDATE operation; useful for tracking data freshness

---

### **Table: models** (Appliance Models)

- **model_id** (UUID, Primary Key): Unique internal database identifier for each appliance model record; automatically generated; used for JOINs with part_model_mapping table

- **model_number** (VARCHAR 100, UNIQUE, NOT NULL): Specific alphanumeric model number of the appliance (e.g., "WDT780SAEM1", "RF28R7351SR"); unique identifier for each appliance model; users find this on their appliance nameplate

- **model_url** (TEXT): Full URL to the model's page on PartSelect.com showing all compatible parts for this model; may be empty if URL not available

- **brand** (VARCHAR 100): Manufacturer or brand of this appliance model (e.g., "Whirlpool", "Samsung", "GE"); extracted from model pages; may be NULL if not available

- **appliance_type** (VARCHAR 50): Type of appliance; values are "refrigerator" or "dishwasher" (scope limited to these two); indicates which category of parts are compatible

- **description** (TEXT): Optional detailed description of this appliance model; may include model name, features, year released, or technical specifications; often NULL/empty for many models

- **parts_count** (INTEGER, DEFAULT 0): Cached count of how many parts are compatible with this model; automatically maintained by database triggers; useful for showing model's part availability

- **created_at** (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Timestamp when this model record was first inserted into database; useful for tracking when data was scraped/added

- **updated_at** (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Timestamp of last modification to this model record; automatically updated by trigger on any UPDATE operation; useful for tracking data freshness

---

### **Table: part_model_mapping** (Junction Table for Compatibility)

- **mapping_id** (UUID, Primary Key): Unique internal database identifier for each part-model compatibility mapping record; automatically generated

- **part_id** (UUID, Foreign Key → parts.part_id, ON DELETE CASCADE): References a part record; establishes which part is compatible with a model; when part is deleted, all its mappings are automatically deleted

- **model_id** (UUID, Foreign Key → models.model_id, ON DELETE CASCADE): References a model record; establishes which model is compatible with a part; when model is deleted, all its mappings are automatically deleted

- **created_at** (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Timestamp when this compatibility mapping was created; useful for tracking when compatibility data was added

## Example User Questions → SQL Query Mapping

| User Question | SQL Query |
|--------------|-----------|
| "Tell me about part PS11752778" | `SELECT * FROM parts WHERE part_number = 'PS11752778';` |
| "Show me ice maker parts for refrigerators" | `SELECT * FROM parts WHERE part_name ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
| "Is part PS11752778 compatible with WDT780SAEM1?" | `SELECT p.part_name, m.model_number FROM parts p JOIN part_model_mapping pmm ON p.part_id = pmm.part_id JOIN models m ON pmm.model_id = m.model_id WHERE p.part_number = 'PS11752778' AND m.model_number = 'WDT780SAEM1';` |
| "What parts fix ice maker not working in refrigerators?" | `SELECT * FROM parts WHERE symptoms ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |