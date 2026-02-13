"""
SQL Search Tool for LangChain Agent
Executes SQL queries against PostgreSQL database for structured part data.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Any, Optional
from langchain.tools import tool
from services.database import DatabaseService
import psycopg2


# Tool description loaded from sql_tool.md
TOOL_DESCRIPTION = """
Execute SQL queries against the PostgreSQL database to retrieve structured information about appliance parts, compatible models, and part-model compatibility relationships. This tool provides direct access to the parts catalog, pricing information, ratings, installation details, availability, and compatibility mappings for refrigerator and dishwasher parts.

**Best Practices:**
- Always use `LIMIT` clause to prevent returning too many results (recommended: 10-50 rows)
- Use `ILIKE` for case-insensitive text searches
- Use `ORDER BY` to sort results by relevance (rating, price, discount_percentage, etc.)
- When searching by model compatibility, always JOIN through `part_model_mapping` table
- Use `WHERE rating IS NOT NULL` when filtering by ratings to exclude parts without reviews
- For symptom searches, use `ILIKE '%keyword%'` to match partial text in the `symptoms` field
- Check `availability` field to ensure parts are in stock if user requests available parts
- Use computed fields like `has_discount` and `discount_percentage` for discount-related queries

**Database Schema:**

Table: parts (Main Product Catalog)
- part_id (UUID, PK): Unique database identifier for JOINs
- part_name (VARCHAR 255): Human-readable part name (e.g., "Door Shelf Bin", "Ice Maker Assembly")
- manufacturer_part_number (VARCHAR 100, UNIQUE): Manufacturer's official part number (e.g., "WPW10321304")
- part_number (VARCHAR 100): PartSelect internal SKU (e.g., "PS11752778"). **NOTE: Currently empty/unused in database**
- brand (VARCHAR 100): Manufacturer name (Whirlpool, GE, Samsung, LG, etc.)
- appliance_type (VARCHAR 50): "refrigerator" or "dishwasher"
- current_price (DECIMAL 10,2): Current selling price in USD
- original_price (DECIMAL 10,2): MSRP before discounts
- has_discount (BOOLEAN, COMPUTED): TRUE if on sale
- discount_percentage (DECIMAL 5,2, COMPUTED): Percentage off original price
- rating (DECIMAL 3,2): Customer rating 0-5 stars (NULL if no reviews)
- review_count (INTEGER): Number of customer reviews
- description (TEXT): Detailed part description and specifications
- symptoms (TEXT): Pipe-separated list of problems this part fixes
- replacement_parts (TEXT): Pipe-separated alternative part numbers
- installation_difficulty (VARCHAR 50): "Easy", "Moderate", "Difficult", "Hard"
- installation_time (VARCHAR 50): Estimated install time (e.g., "30-60 minutes")
- delivery_time (VARCHAR 100): Estimated shipping timeframe
- availability (VARCHAR 50): Stock status ("In Stock", "Out of Stock", etc.)
- image_url (TEXT): Product image URL
- video_url (TEXT): Installation video URL (often YouTube)
- product_url (TEXT): PartSelect product page URL
- compatible_models_count (INTEGER): Number of compatible models
- created_at (TIMESTAMP): When record was created
- updated_at (TIMESTAMP): Last modification timestamp

Table: models (Appliance Models)
- model_id (UUID, PK): Unique database identifier for JOINs
- model_number (VARCHAR 100, UNIQUE): Appliance model number (e.g., "WDT780SAEM1")
- model_url (TEXT): PartSelect model page URL
- brand (VARCHAR 100): Manufacturer name
- appliance_type (VARCHAR 50): "refrigerator" or "dishwasher"
- description (TEXT): Model description and specifications
- parts_count (INTEGER): Number of compatible parts
- created_at (TIMESTAMP): When record was created
- updated_at (TIMESTAMP): Last modification timestamp

Table: part_model_mapping (Junction Table for Compatibility)
- mapping_id (UUID, PK): Unique mapping identifier
- part_id (UUID, FK → parts.part_id): References part record
- model_id (UUID, FK → models.model_id): References model record
- created_at (TIMESTAMP): When mapping was created

**Example Queries:**

| User Question | SQL Query |
|--------------|-----------|
| "Tell me about part PS11752778" | `SELECT * FROM parts WHERE part_number = 'PS11752778';` |
| "Show me ice maker parts for refrigerators" | `SELECT * FROM parts WHERE part_name ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
| "Is part PS11752778 compatible with WDT780SAEM1?" | `SELECT p.part_name, m.model_number FROM parts p JOIN part_model_mapping pmm ON p.part_id = pmm.part_id JOIN models m ON pmm.model_id = m.model_id WHERE p.part_number = 'PS11752778' AND m.model_number = 'WDT780SAEM1';` |
| "What parts fix ice maker not working in refrigerators?" | `SELECT * FROM parts WHERE symptoms ILIKE '%ice maker%' AND appliance_type = 'refrigerator' ORDER BY rating DESC LIMIT 10;` |
"""


@tool(description=TOOL_DESCRIPTION)
def sql_search_tool(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute SQL SELECT query against PostgreSQL database.

    Args:
        sql_query: Raw SQL SELECT query string

    Returns:
        List of dictionaries (database rows) or empty list if no results

    Raises:
        Returns error dict if query fails
    """
    # Input validation
    if not sql_query or not isinstance(sql_query, str):
        return [{"error": "Invalid input: sql_query must be a non-empty string"}]

    # Security: Only allow SELECT queries
    query_upper = sql_query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return [{"error": "Only SELECT queries are allowed. No INSERT, UPDATE, DELETE, DROP, or other modifying statements."}]

    # Block dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return [{"error": f"Dangerous SQL keyword '{keyword}' detected. Only SELECT queries are allowed."}]

    try:
        # Initialize database service
        db = DatabaseService()

        # Get connection
        conn = db.get_connection()
        cursor = conn.cursor()

        # Execute query
        cursor.execute(sql_query)

        # Fetch results
        results = cursor.fetchall()

        # Close connection
        cursor.close()
        conn.close()

        # Convert to list of dicts
        if results:
            return [dict(row) for row in results]
        else:
            return []

    except psycopg2.Error as e:
        # Database/SQL error
        error_msg = str(e).split('\n')[0]  # Get first line of error
        return [{"error": f"SQL execution error: {error_msg}", "query": sql_query}]

    except Exception as e:
        # General error
        return [{"error": f"Tool execution error: {str(e)}", "query": sql_query}]


# Test function (optional, for development)
def test_sql_search_tool():
    """Test the SQL search tool with sample queries."""
    print("Testing SQL Search Tool...\n")

    # Test 1: Simple part search
    print("Test 1: Search for ice maker parts")
    result1 = sql_search_tool("SELECT part_name, brand, current_price FROM parts WHERE part_name ILIKE '%ice maker%' LIMIT 5")
    print(f"Results: {len(result1)} parts found")
    if result1:
        print(f"Sample: {result1[0]}")
    print()

    # Test 2: Get specific part
    print("Test 2: Get specific part by part_number")
    result2 = sql_search_tool("SELECT * FROM parts WHERE part_number = 'PS11752778' OR manufacturer_part_number = 'PS11752778'")
    print(f"Results: {len(result2)} parts found")
    print()

    # Test 3: Discounted parts
    print("Test 3: Find discounted refrigerator parts")
    result3 = sql_search_tool("SELECT part_name, current_price, original_price, discount_percentage FROM parts WHERE has_discount = TRUE AND appliance_type = 'refrigerator' ORDER BY discount_percentage DESC LIMIT 5")
    print(f"Results: {len(result3)} parts found")
    if result3:
        print(f"Sample: {result3[0]}")
    print()

    # Test 4: Invalid query (should return error)
    print("Test 4: Invalid query (should return error)")
    result4 = sql_search_tool("DROP TABLE parts")
    print(f"Result: {result4}")
    print()

    # Test 5: Compatibility check
    print("Test 5: Check model compatibility")
    result5 = sql_search_tool("SELECT COUNT(*) as compatible_parts FROM part_model_mapping WHERE model_id IN (SELECT model_id FROM models WHERE model_number = 'WDT780SAEM1')")
    print(f"Result: {result5}")
    print()


if __name__ == "__main__":
    # Run tests if executed directly
    test_sql_search_tool()
