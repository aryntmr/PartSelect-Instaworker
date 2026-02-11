"""
ETL Script: Load enriched CSV data into PostgreSQL database
"""

import os
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

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

# File paths
CSV_PATH = Path(__file__).parent.parent / 'scraping' / 'data' / 'processed' / 'parts_latest.csv'


def get_db_connection():
    """Create and return database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✅ Connected to PostgreSQL database: {DB_CONFIG['database']}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print(f"\nConnection details:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        sys.exit(1)


def load_csv_data():
    """Load and prepare CSV data."""
    print(f"\n📂 Loading CSV from: {CSV_PATH}")

    if not CSV_PATH.exists():
        print(f"❌ CSV file not found: {CSV_PATH}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"✅ Loaded {len(df)} parts from CSV")
    return df


def insert_parts(conn, df):
    """Insert parts data into database."""
    print("\n📦 Inserting parts into database...")

    cursor = conn.cursor()

    # Prepare insert query
    insert_query = """
    INSERT INTO parts (
        part_name, manufacturer_part_number, part_number, brand, appliance_type,
        current_price, original_price,
        rating, review_count,
        description, symptoms, replacement_parts,
        installation_difficulty, installation_time,
        delivery_time, availability,
        image_url, video_url, product_url,
        compatible_models_count
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s, %s,
        %s
    )
    RETURNING part_id;
    """

    part_ids = []
    compatible_models_data = []  # Store for later processing

    for idx, row in df.iterrows():
        # Prepare values
        values = (
            row.get('part_name', ''),
            row.get('manufacturer_part_number', ''),
            row.get('part_number', ''),
            row.get('brand', ''),
            row.get('appliance_type', ''),

            float(row.get('current_price', 0)),
            float(row.get('original_price', 0)),

            float(row.get('rating', 0)) if pd.notna(row.get('rating')) else None,
            int(row.get('review_count', 0)),

            row.get('description', ''),
            row.get('symptoms', ''),
            row.get('replacement_parts', ''),

            row.get('installation_difficulty', ''),
            row.get('installation_time', ''),

            row.get('delivery_time', ''),
            row.get('availability', ''),

            row.get('image_url', ''),
            row.get('video_url', ''),
            row.get('product_url', ''),

            int(row.get('compatible_models_count', 0))
        )

        try:
            cursor.execute(insert_query, values)
            part_id = cursor.fetchone()[0]
            part_ids.append(part_id)

            # Store compatible models JSON for this part
            models_json = row.get('compatible_models_json', '')
            if models_json and models_json.strip():
                try:
                    models = json.loads(models_json)
                    compatible_models_data.append({
                        'part_id': part_id,
                        'models': models
                    })
                except json.JSONDecodeError:
                    print(f"  ⚠️  Invalid JSON for part {row.get('part_name')}")

        except Exception as e:
            print(f"  ❌ Error inserting part {row.get('part_name')}: {e}")
            conn.rollback()
            continue

    conn.commit()
    print(f"✅ Inserted {len(part_ids)} parts")

    cursor.close()
    return part_ids, compatible_models_data


def insert_models_and_mappings(conn, compatible_models_data):
    """Insert models and create part-model mappings."""
    print("\n🏷️  Inserting models and creating mappings...")

    cursor = conn.cursor()

    # Track unique models
    model_cache = {}  # model_number -> model_id
    total_models = 0
    total_mappings = 0

    # First pass: Insert all unique models
    print("  Step 1: Extracting unique models...")
    unique_models = set()
    for item in compatible_models_data:
        for model in item['models']:
            model_number = model.get('model_number', '').strip()
            if model_number:
                unique_models.add((model_number, model.get('model_url', '')))

    print(f"  Found {len(unique_models)} unique models")

    # Insert models
    print("  Step 2: Inserting models...")
    insert_model_query = """
    INSERT INTO models (model_number, model_url)
    VALUES (%s, %s)
    ON CONFLICT (model_number) DO UPDATE SET model_url = EXCLUDED.model_url
    RETURNING model_id, model_number;
    """

    for model_number, model_url in unique_models:
        try:
            cursor.execute(insert_model_query, (model_number, model_url))
            model_id, model_num = cursor.fetchone()
            model_cache[model_num] = model_id
            total_models += 1
        except Exception as e:
            print(f"    ⚠️  Error inserting model {model_number}: {e}")
            continue

    conn.commit()
    print(f"  ✅ Inserted {total_models} models")

    # Second pass: Create part-model mappings
    print("  Step 3: Creating part-model mappings...")
    insert_mapping_query = """
    INSERT INTO part_model_mapping (part_id, model_id)
    VALUES (%s, %s)
    ON CONFLICT (part_id, model_id) DO NOTHING;
    """

    mapping_values = []
    for item in compatible_models_data:
        part_id = item['part_id']
        for model in item['models']:
            model_number = model.get('model_number', '').strip()
            if model_number and model_number in model_cache:
                model_id = model_cache[model_number]
                mapping_values.append((part_id, model_id))

    # Batch insert mappings
    execute_batch(cursor, insert_mapping_query, mapping_values, page_size=1000)
    total_mappings = len(mapping_values)

    conn.commit()
    print(f"  ✅ Created {total_mappings} part-model mappings")

    cursor.close()
    return total_models, total_mappings


def verify_data(conn):
    """Verify data was loaded correctly."""
    print("\n🔍 Verifying data...")

    cursor = conn.cursor()

    # Count parts
    cursor.execute("SELECT COUNT(*) FROM parts;")
    parts_count = cursor.fetchone()[0]
    print(f"  ✅ Parts in database: {parts_count}")

    # Count models
    cursor.execute("SELECT COUNT(*) FROM models;")
    models_count = cursor.fetchone()[0]
    print(f"  ✅ Models in database: {models_count}")

    # Count mappings
    cursor.execute("SELECT COUNT(*) FROM part_model_mapping;")
    mappings_count = cursor.fetchone()[0]
    print(f"  ✅ Part-model mappings: {mappings_count}")

    # Sample queries
    print("\n📊 Sample data:")

    # Top rated parts
    cursor.execute("""
        SELECT part_name, rating, review_count, current_price
        FROM parts
        WHERE rating IS NOT NULL
        ORDER BY rating DESC, review_count DESC
        LIMIT 3;
    """)
    print("\n  Top-rated parts:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: ⭐ {row[1]}/5.0 ({row[2]} reviews) - ${row[3]}")

    # Discounted parts
    cursor.execute("""
        SELECT part_name, original_price, current_price, discount_percentage
        FROM parts
        WHERE has_discount = TRUE
        ORDER BY discount_percentage DESC
        LIMIT 3;
    """)
    print("\n  Discounted parts:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: ${row[1]} → ${row[2]} ({row[3]:.0f}% OFF)")

    # Part with most compatible models
    cursor.execute("""
        SELECT p.part_name, COUNT(pmm.model_id) as model_count
        FROM parts p
        LEFT JOIN part_model_mapping pmm ON p.part_id = pmm.part_id
        GROUP BY p.part_id, p.part_name
        ORDER BY model_count DESC
        LIMIT 3;
    """)
    print("\n  Parts with most compatible models:")
    for row in cursor.fetchall():
        print(f"    - {row[0]}: {row[1]} models")

    cursor.close()


def main():
    """Main ETL pipeline."""
    print("=" * 60)
    print("📊 PartSelect Database ETL Pipeline")
    print("=" * 60)

    # Step 1: Load CSV
    df = load_csv_data()

    # Step 2: Connect to database
    conn = get_db_connection()

    try:
        # Step 3: Insert parts
        part_ids, compatible_models_data = insert_parts(conn, df)

        # Step 4: Insert models and mappings
        total_models, total_mappings = insert_models_and_mappings(conn, compatible_models_data)

        # Step 5: Verify
        verify_data(conn)

        print("\n" + "=" * 60)
        print("✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"  📦 Parts loaded: {len(part_ids)}")
        print(f"  🏷️  Models loaded: {total_models}")
        print(f"  🔗 Mappings created: {total_mappings}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during ETL: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()
        print("\n🔒 Database connection closed")


if __name__ == "__main__":
    main()
