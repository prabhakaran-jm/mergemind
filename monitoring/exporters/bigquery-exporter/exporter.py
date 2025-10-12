#!/usr/bin/env python3
"""
BigQuery metrics exporter for Prometheus.
"""

import os
import time
import logging
from flask import Flask, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
bigquery_queries_total = Counter(
    'bigquery_queries_total',
    'Total BigQuery queries',
    ['status']
)

bigquery_query_duration_seconds = Histogram(
    'bigquery_query_duration_seconds',
    'BigQuery query duration',
    ['query_type']
)

bigquery_bytes_processed_total = Counter(
    'bigquery_bytes_processed_total',
    'Total bytes processed by BigQuery',
    ['query_type']
)

bigquery_slot_seconds_total = Counter(
    'bigquery_slot_seconds_total',
    'Total slot seconds used by BigQuery',
    ['query_type']
)

bigquery_job_failures_total = Counter(
    'bigquery_job_failures_total',
    'Total BigQuery job failures',
    ['error_type']
)

bigquery_table_size_bytes = Gauge(
    'bigquery_table_size_bytes',
    'BigQuery table size in bytes',
    ['dataset', 'table']
)

bigquery_table_row_count = Gauge(
    'bigquery_table_row_count',
    'BigQuery table row count',
    ['dataset', 'table']
)

bigquery_quota_usage = Gauge(
    'bigquery_quota_usage',
    'BigQuery quota usage percentage',
    ['quota_type']
)

# Flask app
app = Flask(__name__)

class BigQueryExporter:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.dataset_raw = os.getenv('BQ_DATASET_RAW', 'mergemind_raw')
        self.dataset_modeled = os.getenv('BQ_DATASET_MODELED', 'mergemind')
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        self.client = bigquery.Client(project=self.project_id)
        logger.info(f"BigQuery exporter initialized for project: {self.project_id}")
    
    def collect_metrics(self):
        """Collect BigQuery metrics."""
        try:
            # Get job statistics
            self._collect_job_metrics()
            
            # Get table metrics
            self._collect_table_metrics()
            
            # Get quota usage
            self._collect_quota_metrics()
            
            logger.info("BigQuery metrics collected successfully")
            
        except Exception as e:
            logger.error(f"Failed to collect BigQuery metrics: {e}")
            bigquery_job_failures_total.labels(error_type='collection_error').inc()
    
    def _collect_job_metrics(self):
        """Collect job-related metrics."""
        try:
            # Query recent jobs
            sql = """
            SELECT
              job_type,
              state,
              total_bytes_processed,
              total_slot_ms,
              creation_time,
              error_result.reason as error_reason
            FROM `{project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
            WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
            """.format(project_id=self.project_id)
            
            query_job = self.client.query(sql)
            results = query_job.result()
            
            for row in results:
                job_type = row.job_type or 'unknown'
                state = row.state or 'unknown'
                
                # Count queries
                bigquery_queries_total.labels(status=state).inc()
                
                # Bytes processed
                if row.total_bytes_processed:
                    bigquery_bytes_processed_total.labels(query_type=job_type).inc(row.total_bytes_processed)
                
                # Slot seconds
                if row.total_slot_ms:
                    slot_seconds = row.total_slot_ms / 1000
                    bigquery_slot_seconds_total.labels(query_type=job_type).inc(slot_seconds)
                
                # Job failures
                if state == 'FAILED' and row.error_reason:
                    bigquery_job_failures_total.labels(error_type=row.error_reason).inc()
                    
        except Exception as e:
            logger.error(f"Failed to collect job metrics: {e}")
            bigquery_job_failures_total.labels(error_type='job_query_error').inc()
    
    def _collect_table_metrics(self):
        """Collect table-related metrics."""
        try:
            datasets = [self.dataset_raw, self.dataset_modeled]
            
            for dataset_id in datasets:
                try:
                    dataset = self.client.dataset(dataset_id)
                    tables = list(self.client.list_tables(dataset))
                    
                    for table in tables:
                        try:
                            table_obj = self.client.get_table(table.reference)
                            
                            # Table size
                            if table_obj.num_bytes:
                                bigquery_table_size_bytes.labels(
                                    dataset=dataset_id,
                                    table=table.table_id
                                ).set(table_obj.num_bytes)
                            
                            # Row count
                            if table_obj.num_rows:
                                bigquery_table_row_count.labels(
                                    dataset=dataset_id,
                                    table=table.table_id
                                ).set(table_obj.num_rows)
                                
                        except NotFound:
                            logger.warning(f"Table not found: {dataset_id}.{table.table_id}")
                        except Exception as e:
                            logger.error(f"Failed to get table info for {dataset_id}.{table.table_id}: {e}")
                            
                except NotFound:
                    logger.warning(f"Dataset not found: {dataset_id}")
                except Exception as e:
                    logger.error(f"Failed to list tables in dataset {dataset_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to collect table metrics: {e}")
            bigquery_job_failures_total.labels(error_type='table_query_error').inc()
    
    def _collect_quota_metrics(self):
        """Collect quota usage metrics."""
        try:
            # Note: Quota metrics require special permissions and may not be available
            # This is a placeholder for future implementation
            
            # For now, we'll set a placeholder value
            bigquery_quota_usage.labels(quota_type='queries').set(0.0)
            bigquery_quota_usage.labels(quota_type='bytes').set(0.0)
            bigquery_quota_usage.labels(quota_type='slots').set(0.0)
            
        except Exception as e:
            logger.error(f"Failed to collect quota metrics: {e}")

# Global exporter instance
exporter = BigQueryExporter()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    exporter.collect_metrics()
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        # Test BigQuery connection
        exporter.client.query("SELECT 1").result()
        return Response("OK", status=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response("ERROR", status=500)

@app.route('/')
def index():
    """Index page."""
    return """
    <h1>BigQuery Exporter</h1>
    <p><a href="/metrics">Metrics</a></p>
    <p><a href="/health">Health</a></p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
