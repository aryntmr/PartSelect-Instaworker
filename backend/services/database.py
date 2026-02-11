"""Database service for backend - handles all database operations."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Optional
import sys

# Load environment variables
load_dotenv()

# Try to load from parent database directory if exists
parent_env = os.path.join(os.path.dirname(__file__), '..', '..', 'database', '.env')
if os.path.exists(parent_env):
    load_dotenv(parent_env)


class DatabaseService:
    """Database connection and query service."""
    
    def __init__(self):
        """Initialize database configuration."""
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'partselect_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    def get_connection(self):
        """Create and return database connection."""
        return psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def search_parts(self, search_term: str, limit: int = 4) -> List[Dict]:
        """
        Search for parts by name or part number.
        
        Args:
            search_term: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching parts
        """
        conn = self.get_connection()
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
            image_url,
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
        search_query = ' & '.join(search_term.split()) if search_term.strip() else search_term
        
        cursor.execute(query, (like_pattern, like_pattern, like_pattern, search_query, limit))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_part_by_id(self, part_id: str) -> Optional[Dict]:
        """
        Get complete details for a specific part.
        
        Args:
            part_id: UUID of the part
            
        Returns:
            Part details or None if not found
        """
        conn = self.get_connection()
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
    
    def get_compatible_models(self, part_id: str, limit: int = 10) -> List[str]:
        """
        Get list of compatible model numbers for a part.
        
        Args:
            part_id: UUID of the part
            limit: Maximum models to return
            
        Returns:
            List of model numbers
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT m.model_number 
        FROM models m
        JOIN part_model_mapping pmm ON m.model_id = pmm.model_id
        WHERE pmm.part_id = %s
        LIMIT %s;
        """
        
        cursor.execute(query, (part_id, limit))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [row['model_number'] for row in results]


# Singleton instance
db_service = DatabaseService()
