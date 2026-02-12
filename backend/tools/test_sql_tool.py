"""
Test script for SQL Search Tool
Run this to verify the tool works correctly with the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sql_search_tool import sql_search_tool


def print_separator():
    """Print a visual separator."""
    print("=" * 80)


def test_basic_queries():
    """Test basic SQL queries."""
    print_separator()
    print("TESTING SQL SEARCH TOOL")
    print_separator()
    print()

    # Test 1: Count all parts
    print("Test 1: Count all parts in database")
    print("Query: SELECT COUNT(*) as total_parts FROM parts")
    result = sql_search_tool.invoke({"sql_query": "SELECT COUNT(*) as total_parts FROM parts"})
    print(f"Result: {result}")
    print()

    # Test 2: Search by part name
    print("Test 2: Search for 'door' parts")
    print("Query: SELECT part_name, brand, current_price FROM parts WHERE part_name ILIKE '%door%' LIMIT 5")
    result = sql_search_tool.invoke({"sql_query": "SELECT part_name, brand, current_price FROM parts WHERE part_name ILIKE '%door%' LIMIT 5"})
    print(f"Found {len(result)} parts")
    for i, part in enumerate(result, 1):
        print(f"  {i}. {part.get('part_name')} - ${part.get('current_price')} ({part.get('brand')})")
    print()

    # Test 3: Get specific part by part_number
    print("Test 3: Get specific part by part_number")
    print("Query: SELECT part_name, part_number, current_price, rating FROM parts LIMIT 1")
    result = sql_search_tool.invoke({"sql_query": "SELECT part_name, part_number, current_price, rating FROM parts LIMIT 1"})
    if result:
        print(f"Result: {result[0]}")
    print()

    # Test 4: Find discounted parts
    print("Test 4: Find discounted parts")
    print("Query: SELECT part_name, original_price, current_price, discount_percentage FROM parts WHERE has_discount = TRUE ORDER BY discount_percentage DESC LIMIT 5")
    result = sql_search_tool.invoke({"sql_query": "SELECT part_name, original_price, current_price, discount_percentage FROM parts WHERE has_discount = TRUE ORDER BY discount_percentage DESC LIMIT 5"})
    print(f"Found {len(result)} discounted parts")
    for i, part in enumerate(result, 1):
        print(f"  {i}. {part.get('part_name')} - ${part.get('current_price')} (was ${part.get('original_price')}, {part.get('discount_percentage')}% off)")
    print()

    # Test 5: Search by appliance type
    print("Test 5: Count parts by appliance type")
    print("Query: SELECT appliance_type, COUNT(*) as count FROM parts GROUP BY appliance_type")
    result = sql_search_tool.invoke({"sql_query": "SELECT appliance_type, COUNT(*) as count FROM parts GROUP BY appliance_type"})
    print("Results:")
    for row in result:
        print(f"  {row.get('appliance_type')}: {row.get('count')} parts")
    print()

    # Test 6: Top rated parts
    print("Test 6: Get top 5 rated parts")
    print("Query: SELECT part_name, rating, review_count FROM parts WHERE rating IS NOT NULL ORDER BY rating DESC, review_count DESC LIMIT 5")
    result = sql_search_tool.invoke({"sql_query": "SELECT part_name, rating, review_count FROM parts WHERE rating IS NOT NULL ORDER BY rating DESC, review_count DESC LIMIT 5"})
    print(f"Found {len(result)} top-rated parts")
    for i, part in enumerate(result, 1):
        print(f"  {i}. {part.get('part_name')} - {part.get('rating')}/5 ({part.get('review_count')} reviews)")
    print()

    # Test 7: Search by symptoms
    print("Test 7: Search parts by symptom")
    print("Query: SELECT part_name, symptoms FROM parts WHERE symptoms ILIKE '%leaking%' LIMIT 5")
    result = sql_search_tool.invoke({"sql_query": "SELECT part_name, symptoms FROM parts WHERE symptoms ILIKE '%leaking%' LIMIT 5"})
    print(f"Found {len(result)} parts for 'leaking' symptom")
    for i, part in enumerate(result, 1):
        symptoms = part.get('symptoms', '')[:100] if part.get('symptoms') else ''  # Truncate long symptoms
        print(f"  {i}. {part.get('part_name')} - {symptoms}...")
    print()

    # Test 8: Count models
    print("Test 8: Count total models")
    print("Query: SELECT COUNT(*) as total_models FROM models")
    result = sql_search_tool.invoke({"sql_query": "SELECT COUNT(*) as total_models FROM models"})
    print(f"Result: {result}")
    print()

    # Test 9: Get compatible models for a part
    print("Test 9: Get compatible models count")
    print("Query: SELECT COUNT(*) as total_mappings FROM part_model_mapping")
    result = sql_search_tool.invoke({"sql_query": "SELECT COUNT(*) as total_mappings FROM part_model_mapping"})
    print(f"Result: {result}")
    print()


def test_error_handling():
    """Test error handling."""
    print_separator()
    print("TESTING ERROR HANDLING")
    print_separator()
    print()

    # Test 1: Invalid SQL syntax
    print("Test 1: Invalid SQL syntax")
    result = sql_search_tool.invoke({"sql_query": "SELECT * FORM parts"})  # typo: FORM instead of FROM
    print(f"Result: {result}")
    print()

    # Test 2: Dangerous query (DROP)
    print("Test 2: Dangerous query (DROP TABLE)")
    result = sql_search_tool.invoke({"sql_query": "DROP TABLE parts"})
    print(f"Result: {result}")
    print()

    # Test 3: Non-SELECT query (INSERT)
    print("Test 3: Non-SELECT query (INSERT)")
    result = sql_search_tool.invoke({"sql_query": "INSERT INTO parts VALUES ('test')"})
    print(f"Result: {result}")
    print()

    # Test 4: Empty query
    print("Test 4: Empty query")
    result = sql_search_tool.invoke({"sql_query": ""})
    print(f"Result: {result}")
    print()

    # Test 5: Non-existent table
    print("Test 5: Non-existent table")
    result = sql_search_tool.invoke({"sql_query": "SELECT * FROM nonexistent_table"})
    print(f"Result: {result}")
    print()


def test_complex_queries():
    """Test complex queries with JOINs."""
    print_separator()
    print("TESTING COMPLEX QUERIES")
    print_separator()
    print()

    # Test 1: JOIN to get part with models
    print("Test 1: Get part with compatible models (JOIN)")
    query = """
    SELECT
        p.part_name,
        p.brand,
        COUNT(pmm.model_id) as compatible_model_count
    FROM parts p
    LEFT JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
    GROUP BY p.part_id, p.part_name, p.brand
    HAVING COUNT(pmm.model_id) > 0
    ORDER BY compatible_model_count DESC
    LIMIT 5
    """
    result = sql_search_tool.invoke({"sql_query": query})
    print(f"Found {len(result)} parts with compatibility info")
    for i, part in enumerate(result, 1):
        print(f"  {i}. {part.get('part_name')} ({part.get('brand')}) - {part.get('compatible_model_count')} models")
    print()

    # Test 2: Price range query
    print("Test 2: Parts in price range $20-$50")
    query = """
    SELECT part_name, current_price, appliance_type
    FROM parts
    WHERE current_price BETWEEN 20 AND 50
    ORDER BY current_price ASC
    LIMIT 10
    """
    result = sql_search_tool.invoke({"sql_query": query})
    print(f"Found {len(result)} parts in $20-$50 range")
    for i, part in enumerate(result, 1):
        print(f"  {i}. {part.get('part_name')} - ${part.get('current_price')} ({part.get('appliance_type')})")
    print()


if __name__ == "__main__":
    print("\n🚀 Starting SQL Search Tool Tests\n")

    # Test basic queries
    test_basic_queries()

    # Test error handling
    test_error_handling()

    # Test complex queries
    test_complex_queries()

    print_separator()
    print("✅ ALL TESTS COMPLETED")
    print_separator()
