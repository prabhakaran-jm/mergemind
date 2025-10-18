"""
BigQuery client for MergeMind API.
Provides a thin wrapper around google-cloud-bigquery with retry logic and error handling.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import time
from functools import wraps
from .config import get_settings

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator for retrying operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


class BigQueryClient:
    """BigQuery client with retry logic and error handling."""
    
    def __init__(self):
        """Initialize BigQuery client with configuration from settings."""
        settings = get_settings()
        self.project_id = settings.gcp_project_id
        self.dataset_raw = settings.bq_dataset_raw
        self.dataset_modeled = settings.bq_dataset_modeled
        self._client = None
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
    
    @property
    def client(self):
        """Lazy initialization of BigQuery client."""
        if self._client is None:
            self._client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client initialized for project: {self.project_id}")
            logger.info(f"Raw dataset: {self.dataset_raw}, Modeled dataset: {self.dataset_modeled}")
        return self._client
    
    @retry_with_backoff(max_retries=3, backoff_factor=1.0)
    def query(self, sql: str, **params) -> List[Dict[str, Any]]:
        """
        Execute a SQL query with optional parameters.
        
        Args:
            sql: SQL query string
            **params: Query parameters
            
        Returns:
            List of dictionaries representing query results
            
        Raises:
            Exception: If query execution fails
        """
        try:
            # Replace parameter placeholders in SQL
            formatted_sql = sql
            for key, value in params.items():
                placeholder = f"@{key}"
                if isinstance(value, str):
                    formatted_sql = formatted_sql.replace(placeholder, f"'{value}'")
                else:
                    formatted_sql = formatted_sql.replace(placeholder, str(value))
            
            logger.debug(f"Executing query: {formatted_sql}")
            
            # Execute query
            query_job = self.client.query(formatted_sql)
            results = query_job.result()
            
            # Convert to list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row))
            
            logger.info(f"Query returned {len(rows)} rows")
            return rows
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=1.0)
    def table_exists(self, dataset: str, table: str) -> bool:
        """
        Check if a table exists in the specified dataset.
        
        Args:
            dataset: Dataset name
            table: Table name
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            table_ref = self.client.dataset(dataset).table(table)
            self.client.get_table(table_ref)
            return True
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            raise
    
    def get_table_info(self, dataset: str, table: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a table.
        
        Args:
            dataset: Dataset name
            table: Table name
            
        Returns:
            Dictionary with table information or None if table doesn't exist
        """
        try:
            table_ref = self.client.dataset(dataset).table(table)
            table_obj = self.client.get_table(table_ref)
            
            return {
                "table_id": table_obj.table_id,
                "dataset_id": table_obj.dataset_id,
                "project": table_obj.project,
                "num_rows": table_obj.num_rows,
                "num_bytes": table_obj.num_bytes,
                "created": table_obj.created.isoformat() if table_obj.created else None,
                "modified": table_obj.modified.isoformat() if table_obj.modified else None,
                "schema": [{"name": field.name, "type": field.field_type} for field in table_obj.schema]
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the BigQuery connection with a simple query.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            result = self.query("SELECT 1 as test_value")
            return len(result) == 1 and result[0]["test_value"] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global instance - lazy initialization
_bigquery_client_instance = None

def get_bigquery_client():
    """Get or create BigQuery client instance."""
    global _bigquery_client_instance
    if _bigquery_client_instance is None:
        _bigquery_client_instance = BigQueryClient()
    return _bigquery_client_instance

class LazyBigQueryClient:
    """Lazy wrapper for BigQuery client."""
    def __getattr__(self, name):
        return getattr(get_bigquery_client(), name)

# For backward compatibility - this will only initialize when first accessed
bigquery_client = LazyBigQueryClient()
