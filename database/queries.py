"""
Common database queries for PartSelect Chatbot
Use these functions in your chatbot to retrieve data
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'partselect_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}


def get_db_connection():
    """Create and return database connection with dict cursor."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# ==========================================
# QUERY 1: Find Parts by Model Number
# ==========================================
def find_parts_by_model(model_number: str) -> List[Dict]:
    """
    Find all parts compatible with a specific appliance model.

    Args:
        model_number: The appliance model number (e.g., 'WDT780SAEM1')

    Returns:
        List of parts with details

    Example:
        >>> parts = find_parts_by_model('WDT780SAEM1')
        >>> print(f"Found {len(parts)} compatible parts")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        p.part_id,
        p.part_name,
        p.manufacturer_part_number,
        p.brand,
        p.current_price,
        p.original_price,
        p.has_discount,
        p.discount_percentage,
        p.rating,
        p.review_count,
        p.description,
        p.symptoms,
        p.installation_difficulty,
        p.installation_time,
        p.video_url,
        p.product_url
    FROM parts p
    JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
    JOIN models m ON pmm.model_id = m.model_id
    WHERE m.model_number ILIKE %s
    ORDER BY p.rating DESC NULLS LAST, p.review_count DESC;
    """

    cursor.execute(query, (model_number,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 2: Find Parts by Symptom
# ==========================================
def find_parts_by_symptom(symptom: str, limit: int = 10) -> List[Dict]:
    """
    Find parts that fix a specific symptom.

    Args:
        symptom: The problem description (e.g., 'ice maker not working')
        limit: Maximum number of results

    Returns:
        List of parts that address this symptom

    Example:
        >>> parts = find_parts_by_symptom('ice maker')
        >>> for part in parts:
        >>>     print(f"{part['part_name']}: ${part['current_price']}")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        part_id,
        part_name,
        manufacturer_part_number,
        current_price,
        original_price,
        has_discount,
        rating,
        review_count,
        symptoms,
        installation_difficulty,
        installation_time,
        video_url,
        product_url
    FROM parts
    WHERE to_tsvector('english', symptoms || ' ' || description)
          @@ to_tsquery('english', %s)
       OR symptoms ILIKE %s
       OR description ILIKE %s
    ORDER BY rating DESC NULLS LAST, review_count DESC
    LIMIT %s;
    """

    # Prepare search terms
    search_query = ' & '.join(symptom.split())  # Full-text search
    like_pattern = f'%{symptom}%'  # LIKE search

    cursor.execute(query, (search_query, like_pattern, like_pattern, limit))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 3: Find Parts by Name or Part Number
# ==========================================
def find_parts_by_name_or_number(search_term: str, limit: int = 10) -> List[Dict]:
    """
    Search for parts by name or part number.

    Args:
        search_term: Part name or number to search for
        limit: Maximum number of results

    Returns:
        List of matching parts

    Example:
        >>> parts = find_parts_by_name_or_number('door shelf')
        >>> print(parts[0]['part_name'])
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        part_id,
        part_name,
        manufacturer_part_number,
        part_number,
        brand,
        current_price,
        original_price,
        has_discount,
        rating,
        review_count,
        description,
        product_url
    FROM parts
    WHERE part_name ILIKE %s
       OR manufacturer_part_number ILIKE %s
       OR part_number ILIKE %s
       OR to_tsvector('english', part_name) @@ to_tsquery('english', %s)
    ORDER BY rating DESC NULLS LAST
    LIMIT %s;
    """

    like_pattern = f'%{search_term}%'
    search_query = ' & '.join(search_term.split())

    cursor.execute(query, (like_pattern, like_pattern, like_pattern, search_query, limit))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 4: Get Discounted Parts
# ==========================================
def get_discounted_parts(min_discount: float = 0, limit: int = 20) -> List[Dict]:
    """
    Find parts currently on sale.

    Args:
        min_discount: Minimum discount percentage (default: 0)
        limit: Maximum number of results

    Returns:
        List of discounted parts

    Example:
        >>> deals = get_discounted_parts(min_discount=20)
        >>> for deal in deals:
        >>>     print(f"{deal['part_name']}: {deal['discount_percentage']}% OFF")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        part_id,
        part_name,
        manufacturer_part_number,
        brand,
        original_price,
        current_price,
        discount_percentage,
        rating,
        review_count,
        product_url
    FROM parts
    WHERE has_discount = TRUE
      AND discount_percentage >= %s
    ORDER BY discount_percentage DESC, rating DESC NULLS LAST
    LIMIT %s;
    """

    cursor.execute(query, (min_discount, limit))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 5: Get Top-Rated Parts
# ==========================================
def get_top_rated_parts(min_reviews: int = 5, limit: int = 20) -> List[Dict]:
    """
    Find highest-rated parts with minimum review count.

    Args:
        min_reviews: Minimum number of reviews required
        limit: Maximum number of results

    Returns:
        List of top-rated parts

    Example:
        >>> top_parts = get_top_rated_parts(min_reviews=10)
        >>> print(f"Top part: {top_parts[0]['part_name']}")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        part_id,
        part_name,
        manufacturer_part_number,
        brand,
        current_price,
        rating,
        review_count,
        description,
        installation_difficulty,
        product_url
    FROM parts
    WHERE rating IS NOT NULL
      AND review_count >= %s
    ORDER BY rating DESC, review_count DESC
    LIMIT %s;
    """

    cursor.execute(query, (min_reviews, limit))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 6: Get Part Details by ID
# ==========================================
def get_part_details(part_id: str) -> Optional[Dict]:
    """
    Get complete details for a specific part.

    Args:
        part_id: UUID of the part

    Returns:
        Complete part details or None if not found

    Example:
        >>> part = get_part_details('123e4567-e89b-12d3-a456-426614174000')
        >>> print(part['description'])
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        p.*,
        COALESCE(
            json_agg(
                json_build_object(
                    'model_number', m.model_number,
                    'model_url', m.model_url
                )
            ) FILTER (WHERE m.model_id IS NOT NULL),
            '[]'::json
        ) as compatible_models
    FROM parts p
    LEFT JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
    LEFT JOIN models m ON pmm.model_id = m.model_id
    WHERE p.part_id = %s
    GROUP BY p.part_id;
    """

    cursor.execute(query, (part_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return dict(result) if result else None


# ==========================================
# QUERY 7: Find Parts with Video Instructions
# ==========================================
def get_parts_with_videos(difficulty: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Find parts that have installation video guides.

    Args:
        difficulty: Filter by difficulty ('Easy', 'Moderate', 'Difficult')
        limit: Maximum number of results

    Returns:
        List of parts with installation videos

    Example:
        >>> easy_parts = get_parts_with_videos(difficulty='Easy')
        >>> print(f"Found {len(easy_parts)} easy-to-install parts with videos")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if difficulty:
        query = """
        SELECT
            part_id,
            part_name,
            manufacturer_part_number,
            current_price,
            installation_difficulty,
            installation_time,
            video_url,
            rating,
            product_url
        FROM parts
        WHERE video_url IS NOT NULL
          AND video_url != ''
          AND installation_difficulty ILIKE %s
        ORDER BY rating DESC NULLS LAST
        LIMIT %s;
        """
        cursor.execute(query, (f'%{difficulty}%', limit))
    else:
        query = """
        SELECT
            part_id,
            part_name,
            manufacturer_part_number,
            current_price,
            installation_difficulty,
            installation_time,
            video_url,
            rating,
            product_url
        FROM parts
        WHERE video_url IS NOT NULL
          AND video_url != ''
        ORDER BY
            CASE installation_difficulty
                WHEN 'Really Easy' THEN 1
                WHEN 'Easy' THEN 2
                WHEN 'Moderate' THEN 3
                ELSE 4
            END,
            rating DESC NULLS LAST
        LIMIT %s;
        """
        cursor.execute(query, (limit,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 8: Find Replacement Parts
# ==========================================
def find_replacement_parts(part_number: str) -> List[Dict]:
    """
    Find alternative/replacement parts for a given part number.

    Args:
        part_number: The original part number

    Returns:
        List of replacement parts

    Example:
        >>> replacements = find_replacement_parts('240534701')
        >>> print(f"Found {len(replacements)} replacement options")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        part_id,
        part_name,
        manufacturer_part_number,
        replacement_parts,
        current_price,
        rating,
        review_count,
        product_url
    FROM parts
    WHERE replacement_parts LIKE %s
       OR manufacturer_part_number = %s
    ORDER BY rating DESC NULLS LAST;
    """

    cursor.execute(query, (f'%{part_number}%', part_number))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in results]


# ==========================================
# QUERY 9: Get Database Statistics
# ==========================================
def get_database_stats() -> Dict:
    """
    Get summary statistics about the database.

    Returns:
        Dictionary with database statistics

    Example:
        >>> stats = get_database_stats()
        >>> print(f"Total parts: {stats['total_parts']}")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        (SELECT COUNT(*) FROM parts) as total_parts,
        (SELECT COUNT(*) FROM models) as total_models,
        (SELECT COUNT(*) FROM part_model_mapping) as total_mappings,
        (SELECT COUNT(*) FROM parts WHERE has_discount = TRUE) as discounted_parts,
        (SELECT COUNT(*) FROM parts WHERE video_url IS NOT NULL AND video_url != '') as parts_with_videos,
        (SELECT AVG(rating) FROM parts WHERE rating IS NOT NULL) as avg_rating,
        (SELECT AVG(current_price) FROM parts) as avg_price,
        (SELECT MIN(current_price) FROM parts WHERE current_price > 0) as min_price,
        (SELECT MAX(current_price) FROM parts) as max_price;
    """

    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return dict(result) if result else {}


# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    print("🔍 Testing Database Queries\n")

    # Test 1: Find parts by model
    print("1️⃣ Finding parts for model WDT780SAEM1...")
    model_parts = find_parts_by_model('WDT780SAEM1')
    print(f"   Found {len(model_parts)} compatible parts\n")

    # Test 2: Find parts by symptom
    print("2️⃣ Finding parts for symptom 'ice maker'...")
    symptom_parts = find_parts_by_symptom('ice maker')
    print(f"   Found {len(symptom_parts)} parts\n")

    # Test 3: Get discounted parts
    print("3️⃣ Finding discounted parts...")
    discounts = get_discounted_parts(min_discount=20)
    print(f"   Found {len(discounts)} parts with 20%+ discount\n")

    # Test 4: Get top-rated parts
    print("4️⃣ Finding top-rated parts...")
    top_parts = get_top_rated_parts(min_reviews=5)
    print(f"   Found {len(top_parts)} highly-rated parts\n")

    # Test 5: Get database stats
    print("5️⃣ Getting database statistics...")
    stats = get_database_stats()
    print(f"   Total parts: {stats.get('total_parts', 0)}")
    print(f"   Total models: {stats.get('total_models', 0)}")
    print(f"   Average rating: {stats.get('avg_rating', 0):.2f}/5.0")
    print(f"   Average price: ${stats.get('avg_price', 0):.2f}\n")

    print("✅ All queries executed successfully!")
