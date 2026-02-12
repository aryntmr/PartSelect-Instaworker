# SQL Search Tool - Description & Field Reference

## Tool Description

**Tool Name:** `sql_search_tool`

**Purpose:** Execute SQL queries against the PostgreSQL database to retrieve structured information about appliance parts, compatible models, and part-model compatibility relationships. This tool provides direct access to the parts catalog, pricing information, ratings, installation details, availability, and compatibility mappings for refrigerator and dishwasher parts.

**When to Use This Tool:**
- User asks about specific part numbers or part names (e.g., "Tell me about PS11752778", "Show me water inlet valves")
- User requests parts by brand, appliance type, or price range (e.g., "Whirlpool refrigerator parts under $50")
- User checks part compatibility with specific model numbers (e.g., "Is this part compatible with WDT780SAEM1?")
- User searches for parts by symptoms/problems (e.g., "Parts for ice maker not working")
- User asks about pricing, discounts, ratings, or availability (e.g., "What's the price?", "Is it in stock?", "Show me parts with good ratings")
- User needs installation information (e.g., "How hard is it to install?", "How long does installation take?")
- User wants to find alternative/replacement parts
- User queries compatible models for a specific part (e.g., "Which models is this part compatible with?")
- User searches for parts with specific attributes (e.g., "Easy to install parts", "Parts with video tutorials")

**When NOT to Use This Tool:**
- User asks "how to" repair questions or troubleshooting steps (use Vector DB Search Tool instead)
- User asks about repair guides, symptoms diagnosis, or error codes (use Vector DB Search Tool instead)
- User asks about policies, warranties, returns, or shipping information (use Vector DB Search Tool instead)
- User asks general appliance maintenance questions (use Vector DB Search Tool instead)

**Input Format:**
- The tool accepts a **raw SQL query string** as input
- The query should be a valid PostgreSQL SELECT statement
- The query can involve JOINs across tables (parts, models, part_model_mapping)
- The query should use proper SQL syntax with appropriate WHERE, ORDER BY, LIMIT clauses

**Output Format:**
- Returns a list of dictionaries representing database rows
- Each dictionary contains column names as keys and values from the database
- Empty list `[]` if no results match the query
- Error message string if SQL query is invalid or execution fails

**Database Schema Overview:**
The database contains 3 tables:
1. **parts** (92 unique parts) - Main product catalog
2. **models** (1,845 appliance models) - Compatible model numbers
3. **part_model_mapping** (2,735 mappings) - Junction table connecting parts to models (many-to-many relationship)

**Important Query Patterns:**

1. **Get part by part number or manufacturer part number:**
   ```sql
   SELECT * FROM parts WHERE part_number = 'PS11752778' OR manufacturer_part_number = 'PS11752778';
   ```

2. **Search parts by name (partial match):**
   ```sql
   SELECT * FROM parts WHERE part_name ILIKE '%ice maker%' LIMIT 10;
   ```

3. **Search parts by symptoms:**
   ```sql
   SELECT * FROM parts WHERE symptoms ILIKE '%ice maker not working%' LIMIT 10;
   ```

4. **Filter by appliance type and brand:**
   ```sql
   SELECT * FROM parts WHERE appliance_type = 'refrigerator' AND brand = 'Whirlpool' LIMIT 10;
   ```

5. **Find parts with discounts:**
   ```sql
   SELECT * FROM parts WHERE has_discount = TRUE ORDER BY discount_percentage DESC LIMIT 10;
   ```

6. **Find top-rated parts:**
   ```sql
   SELECT * FROM parts WHERE rating IS NOT NULL ORDER BY rating DESC, review_count DESC LIMIT 10;
   ```

7. **Check part compatibility with a specific model:**
   ```sql
   SELECT p.*, m.model_number
   FROM parts p
   JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
   JOIN models m ON pmm.model_id = m.model_id
   WHERE m.model_number = 'WDT780SAEM1' AND p.part_number = 'PS11752778';
   ```

8. **Get all compatible models for a part:**
   ```sql
   SELECT m.model_number, m.brand, m.appliance_type
   FROM models m
   JOIN part_model_mapping pmm ON m.model_id = pmm.model_id
   JOIN parts p ON pmm.part_id = p.part_id
   WHERE p.part_number = 'PS11752778';
   ```

9. **Find all parts compatible with a specific model:**
   ```sql
   SELECT p.*
   FROM parts p
   JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
   JOIN models m ON pmm.model_id = m.model_id
   WHERE m.model_number = 'WDT780SAEM1'
   ORDER BY p.rating DESC;
   ```

10. **Search parts by price range:**
    ```sql
    SELECT * FROM parts
    WHERE current_price BETWEEN 20.00 AND 100.00
    AND appliance_type = 'refrigerator'
    ORDER BY current_price ASC;
    ```

**Best Practices:**
- Always use `LIMIT` clause to prevent returning too many results (recommended: 10-50 rows)
- Use `ILIKE` for case-insensitive text searches
- Use `ORDER BY` to sort results by relevance (rating, price, discount_percentage, etc.)
- When searching by model compatibility, always JOIN through `part_model_mapping` table
- Use `WHERE rating IS NOT NULL` when filtering by ratings to exclude parts without reviews
- For symptom searches, use `ILIKE '%keyword%'` to match partial text in the `symptoms` field
- Check `availability` field to ensure parts are in stock if user requests available parts
- Use computed fields like `has_discount` and `discount_percentage` for discount-related queries

**Error Handling:**
- If query syntax is invalid, return error message with details
- If no results found, return empty list `[]` (this is NOT an error - it means no matching parts exist)
- If multiple parts match, return up to LIMIT specified (default: 10 if not specified)
- If a field doesn't exist in the schema, return error message

**Performance Considerations:**
- The database has indexes on: appliance_type, brand, current_price, has_discount, rating, manufacturer_part_number, symptoms (full-text), description (full-text), model_number
- Use indexed fields in WHERE clauses for faster queries
- Avoid SELECT * if you only need specific columns (though for LLM context, SELECT * is often acceptable)
- Full-text search on symptoms and description uses PostgreSQL's `to_tsvector` - use `ILIKE` for simpler partial matching

---

## Database Field Descriptions

### **Table: parts** (Main Product Catalog)

#### **Identification Fields**

- **part_id** (UUID, Primary Key): Unique internal database identifier for each part record; automatically generated; used for JOINs with part_model_mapping table

- **part_name** (VARCHAR 255, NOT NULL): Human-readable name/title of the part as displayed on PartSelect website (e.g., "Door Shelf Bin", "Ice Maker Assembly", "Water Inlet Valve")

- **manufacturer_part_number** (VARCHAR 100, UNIQUE, NOT NULL): Official part number assigned by the manufacturer (e.g., "WPW10321304"); unique identifier used by manufacturers and on physical part labels; use this for exact part identification

- **part_number** (VARCHAR 100): PartSelect's internal part number/SKU (e.g., "PS11752778"); typically starts with "PS"; used on PartSelect website URLs and product pages

- **brand** (VARCHAR 100): Manufacturer or brand name that produces this part (e.g., "Whirlpool", "GE", "Samsung", "LG", "Frigidaire", "Bosch"); useful for filtering parts by specific brands

- **appliance_type** (VARCHAR 50): Category of appliance this part is designed for; values are either "refrigerator" or "dishwasher" (scope is limited to these two types only)

#### **Pricing Fields**

- **current_price** (DECIMAL 10,2, NOT NULL): Current selling price of the part in USD; this is the price customers pay; may be lower than original_price if there's an active discount

- **original_price** (DECIMAL 10,2, NOT NULL): Manufacturer's suggested retail price (MSRP) or regular price before any discounts in USD; used to calculate discount percentage

- **has_discount** (BOOLEAN, GENERATED/COMPUTED): Automatically computed boolean flag indicating whether part is currently on sale; TRUE if original_price > current_price, FALSE otherwise; use this to filter discounted/sale parts

- **discount_percentage** (DECIMAL 5,2, GENERATED/COMPUTED): Automatically calculated percentage discount from original price; formula: ((original_price - current_price) / original_price * 100); 0 if no discount; useful for sorting by best deals

#### **Reviews & Ratings Fields**

- **rating** (DECIMAL 3,2): Average customer rating score from 0 to 5 stars; based on customer reviews; NULL if no reviews exist; higher ratings indicate better customer satisfaction; use for sorting by quality

- **review_count** (INTEGER, DEFAULT 0): Total number of customer reviews submitted for this part; higher count indicates more reliable/popular part; use with rating to assess part quality and popularity

#### **Product Details Fields**

- **description** (TEXT): Detailed text description of what the part is, what it does, and what problems it solves; may include technical specifications, dimensions, materials, and usage information; useful for answering "what is this part?" questions

- **symptoms** (TEXT): Pipe-separated list of common appliance problems/symptoms that this part can fix (e.g., "Ice maker not working|Refrigerator leaking|Water dispenser not working"); extracted from customer repair stories; critical for symptom-based part searches

- **replacement_parts** (TEXT): Pipe-separated list of alternative/equivalent part numbers that can be used as replacements; includes both manufacturer part numbers and PartSelect part numbers; useful when primary part is out of stock

#### **Installation Fields**

- **installation_difficulty** (VARCHAR 50): Difficulty level rating for installing this part; typical values: "Easy", "Moderate", "Difficult", "Hard"; helps users assess if they can DIY or need professional help

- **installation_time** (VARCHAR 50): Estimated time required to install/replace this part (e.g., "15-30 minutes", "30-60 minutes", "1-2 hours"); helps users plan repair timeline

#### **Availability Fields**

- **delivery_time** (VARCHAR 100): Estimated shipping/delivery timeframe after order placement (e.g., "2-3 business days", "1-2 weeks", "Same day shipping available"); helps users know when they'll receive the part

- **availability** (VARCHAR 50): Current stock status of the part; typical values: "In Stock", "Out of Stock", "Backordered", "Limited Stock"; critical for determining if part can be ordered immediately

#### **Media Fields**

- **image_url** (TEXT): Full URL to the product image/photo; typically hosted on PartSelect CDN; use for displaying part visually to users; may be empty if no image available

- **video_url** (TEXT): Full URL to installation/repair video tutorial (often YouTube); provides step-by-step visual guidance; may be empty if no video exists; highly valuable for DIY users

- **product_url** (TEXT, NOT NULL): Full URL to the part's product page on PartSelect.com website; users can click this link to view full details, purchase, or check real-time availability

#### **Metadata Fields**

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

**Note:** This table enables the many-to-many relationship between parts and models (one part can fit many models, and one model can use many parts). Always JOIN through this table when querying part-model compatibility.

---

## Query Construction Guidelines for LLM Agent

When constructing SQL queries based on user questions, follow these guidelines:

1. **Part Identification Queries:**
   - If user provides a part number (starts with "PS"), search `part_number` field
   - If user provides manufacturer part number, search `manufacturer_part_number` field
   - If user provides a general name, search `part_name` with ILIKE for partial match

2. **Symptom-Based Queries:**
   - Always search the `symptoms` field with ILIKE when user describes a problem
   - Use multiple keywords if user describes multiple symptoms
   - Combine with `appliance_type` filter if user mentions refrigerator or dishwasher

3. **Compatibility Queries:**
   - Always JOIN `part_model_mapping` and `models` tables when checking compatibility
   - For "Is part X compatible with model Y?": JOIN all 3 tables and filter by both
   - For "What models work with part X?": JOIN to get list of models for that part
   - For "What parts work with model Y?": JOIN to get list of parts for that model

4. **Price/Discount Queries:**
   - Use `has_discount = TRUE` to filter discounted parts
   - Sort by `discount_percentage DESC` to show best deals first
   - Use `current_price BETWEEN X AND Y` for price range queries

5. **Quality/Rating Queries:**
   - Always add `WHERE rating IS NOT NULL` when filtering by ratings
   - Sort by `rating DESC, review_count DESC` to show top-rated parts
   - Use `review_count > 50` to show parts with substantial review history

6. **Availability Queries:**
   - Filter by `availability = 'In Stock'` when user needs parts immediately
   - Check `delivery_time` field when user asks about shipping

7. **Installation Queries:**
   - Filter by `installation_difficulty = 'Easy'` when user wants easy DIY repairs
   - Check `video_url IS NOT NULL` when user wants video tutorials

8. **Always Include:**
   - `LIMIT` clause to prevent returning too many results (recommend 10-20)
   - `ORDER BY` clause to sort results by relevance
   - Appropriate filters for `appliance_type` when context is clear

9. **Result Limits:**
   - For specific part lookups (by part number): LIMIT 1
   - For general searches (by name, symptom): LIMIT 10-20
   - For compatibility lists (models for a part): LIMIT 50-100
   - For price comparison lists: LIMIT 10-20

---

## Example User Questions → SQL Query Mapping

| User Question | SQL Query |
|--------------|-----------|
| "Tell me about part PS11752778" | `SELECT * FROM parts WHERE part_number = 'PS11752778';` |
| "Show me ice maker parts for refrigerators" | `SELECT * FROM parts WHERE part_name ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
| "Is part PS11752778 compatible with WDT780SAEM1?" | `SELECT p.part_name, m.model_number FROM parts p JOIN part_model_mapping pmm ON p.part_id = pmm.part_id JOIN models m ON pmm.model_id = m.model_id WHERE p.part_number = 'PS11752778' AND m.model_number = 'WDT780SAEM1';` |
| "What parts fix ice maker not working in refrigerators?" | `SELECT * FROM parts WHERE symptoms ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
| "Show me Whirlpool parts under $50 with good ratings" | `SELECT * FROM parts WHERE brand = 'Whirlpool' AND current_price < 50 AND rating >= 4.0 ORDER BY rating DESC LIMIT 10;` |
| "Which models is part PS11752778 compatible with?" | `SELECT m.model_number, m.brand FROM models m JOIN part_model_mapping pmm ON m.model_id = pmm.model_id JOIN parts p ON pmm.part_id = p.part_id WHERE p.part_number = 'PS11752778' LIMIT 50;` |
| "Show me parts with discounts for dishwashers" | `SELECT * FROM parts WHERE has_discount = TRUE AND appliance_type = 'dishwasher' ORDER BY discount_percentage DESC LIMIT 10;` |
| "What's the highest rated water valve?" | `SELECT * FROM parts WHERE part_name ILIKE '%water%valve%' AND rating IS NOT NULL ORDER BY rating DESC, review_count DESC LIMIT 5;` |
| "Easy to install refrigerator parts" | `SELECT * FROM parts WHERE installation_difficulty = 'Easy' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
| "Parts with installation videos" | `SELECT * FROM parts WHERE video_url IS NOT NULL ORDER BY rating DESC LIMIT 10;` |

---

## Summary

The SQL Search Tool is the primary tool for accessing structured product data from the PartSelect parts catalog. It excels at:
- Part lookups and searches
- Compatibility checking
- Price/discount queries
- Rating/review filtering
- Availability checking
- Installation information retrieval

Use this tool whenever the user's query requires accessing concrete product data, pricing, compatibility, or availability information. Construct precise SQL queries that leverage the indexed fields and relationships between tables to provide fast, accurate results.

For repair instructions, troubleshooting guides, policy information, or general "how-to" content, use the Vector DB Search Tool instead.
