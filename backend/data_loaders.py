"""Data loaders for various file formats."""

import json
import csv
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSON file.
    
    Expected format:
    [
        {
            "id": "unique-id",
            "title": "Title",
            "content": "Content...",
            "metadata": {...}
        },
        ...
    ]
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return []


def load_csv_data(file_path: str, content_columns: List[str], 
                  id_column: str = "id", title_column: str = "title") -> List[Dict[str, Any]]:
    """Load data from a CSV file.
    
    Args:
        file_path: Path to CSV file
        content_columns: List of column names to combine for content
        id_column: Column name for ID
        title_column: Column name for title
    
    Returns:
        List of formatted data dictionaries
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Combine content columns
                content_parts = []
                for col in content_columns:
                    if col in row and row[col]:
                        content_parts.append(f"{col}: {row[col]}")
                
                # Create metadata from all other columns
                metadata = {k: v for k, v in row.items() 
                           if k not in [id_column, title_column] + content_columns}
                
                item = {
                    "id": row.get(id_column, ""),
                    "title": row.get(title_column, ""),
                    "content": "\n".join(content_parts),
                    "metadata": metadata
                }
                data.append(item)
        
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading CSV file {file_path}: {e}")
        return []


def load_from_postgres(connection, query: str) -> List[Dict[str, Any]]:
    """Load data directly from PostgreSQL.
    
    Args:
        connection: psycopg2 connection
        query: SQL query that returns id, title, content, and metadata columns
    
    Returns:
        List of formatted data dictionaries
    """
    from psycopg2.extras import RealDictCursor
    
    data = []
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                item = {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "content": row.get("content"),
                    "metadata": row.get("metadata", {})
                }
                # If metadata is a string, try to parse it as JSON
                if isinstance(item["metadata"], str):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except:
                        item["metadata"] = {"raw": item["metadata"]}
                
                data.append(item)
        
        logger.info(f"Loaded {len(data)} items from PostgreSQL")
        return data
    except Exception as e:
        logger.error(f"Error loading from PostgreSQL: {e}")
        return []


# Example usage for different data sources
if __name__ == "__main__":
    # Example 1: Load from JSON
    json_data = load_json_data("venues.json")
    
    # Example 2: Load from CSV
    csv_data = load_csv_data(
        "venues.csv",
        content_columns=["description", "amenities", "location_details"],
        id_column="venue_id",
        title_column="venue_name"
    )
    
    # Example 3: Load from PostgreSQL
    # import psycopg2
    # conn = psycopg2.connect(...)
    # pg_data = load_from_postgres(
    #     conn,
    #     """
    #     SELECT 
    #         id,
    #         name as title,
    #         description || ' ' || COALESCE(details, '') as content,
    #         json_build_object(
    #             'category', category,
    #             'location', location,
    #             'price_range', price_range
    #         ) as metadata
    #     FROM venues
    #     WHERE active = true
    #     """
    # )