#!/usr/bin/env python3
"""
Query optimization utilities for MergeMind.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MERGE = "MERGE"

class OptimizationLevel(Enum):
    """Optimization levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    AGGRESSIVE = "aggressive"

@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_id: str
    query_type: QueryType
    execution_time: float
    bytes_processed: int
    rows_returned: int
    slot_ms: int
    optimization_level: OptimizationLevel
    timestamp: datetime
    query_text: str
    parameters: Dict[str, Any]

@dataclass
class OptimizationRule:
    """Query optimization rule."""
    rule_id: str
    name: str
    description: str
    pattern: str
    replacement: str
    conditions: List[str]
    enabled: bool = True
    priority: int = 0

class QueryOptimizer:
    """Query optimizer for BigQuery and other databases."""
    
    def __init__(self):
        """Initialize query optimizer."""
        self.optimization_rules = self._load_optimization_rules()
        self.query_metrics = []
        self.performance_thresholds = {
            'slow_query_threshold': 5.0,  # seconds
            'high_bytes_threshold': 1000000000,  # 1GB
            'high_slots_threshold': 1000000  # 1M slot-ms
        }
        
        logger.info("Query optimizer initialized")
    
    def _load_optimization_rules(self) -> List[OptimizationRule]:
        """Load optimization rules."""
        rules = [
            # Basic optimizations
            OptimizationRule(
                rule_id="select_star_elimination",
                name="SELECT * Elimination",
                description="Replace SELECT * with specific columns",
                pattern=r"SELECT\s+\*\s+FROM",
                replacement="SELECT specific_columns FROM",
                conditions=["performance_critical"],
                priority=1
            ),
            
            OptimizationRule(
                rule_id="unnecessary_distinct",
                name="Unnecessary DISTINCT Removal",
                description="Remove DISTINCT when not needed",
                pattern=r"SELECT\s+DISTINCT\s+([^,]+)\s+FROM\s+(\w+)\s+WHERE\s+\1\s+IS\s+NOT\s+NULL",
                replacement="SELECT \\1 FROM \\2 WHERE \\1 IS NOT NULL",
                conditions=["unique_constraint"],
                priority=2
            ),
            
            OptimizationRule(
                rule_id="index_hint",
                name="Index Hint Addition",
                description="Add index hints for better performance",
                pattern=r"FROM\s+(\w+)\s+WHERE",
                replacement="FROM \\1 WITH(INDEX(idx_common)) WHERE",
                conditions=["frequent_query"],
                priority=3
            ),
            
            OptimizationRule(
                rule_id="join_optimization",
                name="JOIN Optimization",
                description="Optimize JOIN order and conditions",
                pattern=r"FROM\s+(\w+)\s+JOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)",
                replacement="FROM \\1 INNER JOIN \\2 ON \\3 = \\4",
                conditions=["join_query"],
                priority=4
            ),
            
            OptimizationRule(
                rule_id="subquery_to_join",
                name="Subquery to JOIN Conversion",
                description="Convert subqueries to JOINs when possible",
                pattern=r"WHERE\s+\w+\s+IN\s+\(\s*SELECT\s+\w+\s+FROM\s+(\w+)\s*\)",
                replacement="INNER JOIN \\1 ON condition",
                conditions=["subquery_optimizable"],
                priority=5
            ),
            
            OptimizationRule(
                rule_id="date_function_optimization",
                name="Date Function Optimization",
                description="Optimize date functions",
                pattern=r"DATE\(([^)]+)\)",
                replacement="\\1",
                conditions=["date_column_indexed"],
                priority=6
            ),
            
            OptimizationRule(
                rule_id="string_function_optimization",
                name="String Function Optimization",
                description="Optimize string functions",
                pattern=r"UPPER\(([^)]+)\)",
                replacement="\\1",
                conditions=["case_insensitive_collation"],
                priority=7
            ),
            
            OptimizationRule(
                rule_id="aggregation_optimization",
                name="Aggregation Optimization",
                description="Optimize aggregation functions",
                pattern=r"COUNT\(\*\)",
                replacement="COUNT(1)",
                conditions=["count_optimization"],
                priority=8
            ),
            
            OptimizationRule(
                rule_id="limit_optimization",
                name="LIMIT Optimization",
                description="Add LIMIT to queries without it",
                pattern=r"ORDER\s+BY\s+([^;]+);?\s*$",
                replacement="ORDER BY \\1 LIMIT 1000",
                conditions=["no_limit", "large_result_set"],
                priority=9
            ),
            
            OptimizationRule(
                rule_id="partition_pruning",
                name="Partition Pruning",
                description="Add partition filters",
                pattern=r"FROM\s+(\w+)\s+WHERE",
                replacement="FROM \\1 WHERE partition_column >= 'start_date' AND partition_column <= 'end_date' AND",
                conditions=["partitioned_table"],
                priority=10
            )
        ]
        
        return rules
    
    def optimize_query(self, query: str, optimization_level: OptimizationLevel = OptimizationLevel.BASIC) -> str:
        """Optimize SQL query."""
        try:
            optimized_query = query
            
            # Apply optimization rules based on level
            if optimization_level == OptimizationLevel.BASIC:
                rules_to_apply = [rule for rule in self.optimization_rules if rule.priority <= 3]
            elif optimization_level == OptimizationLevel.INTERMEDIATE:
                rules_to_apply = [rule for rule in self.optimization_rules if rule.priority <= 6]
            elif optimization_level == OptimizationLevel.ADVANCED:
                rules_to_apply = [rule for rule in self.optimization_rules if rule.priority <= 8]
            else:  # AGGRESSIVE
                rules_to_apply = self.optimization_rules
            
            # Apply rules
            for rule in rules_to_apply:
                if rule.enabled:
                    try:
                        if re.search(rule.pattern, optimized_query, re.IGNORECASE):
                            optimized_query = re.sub(rule.pattern, rule.replacement, optimized_query, flags=re.IGNORECASE)
                            logger.debug(f"Applied optimization rule: {rule.name}")
                    except Exception as e:
                        logger.warning(f"Failed to apply rule {rule.name}: {e}")
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return query
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query for optimization opportunities."""
        analysis = {
            'query_length': len(query),
            'has_select_star': bool(re.search(r'SELECT\s+\*', query, re.IGNORECASE)),
            'has_distinct': bool(re.search(r'SELECT\s+DISTINCT', query, re.IGNORECASE)),
            'has_subquery': bool(re.search(r'\([^)]*SELECT[^)]*\)', query, re.IGNORECASE)),
            'has_join': bool(re.search(r'JOIN', query, re.IGNORECASE)),
            'has_order_by': bool(re.search(r'ORDER\s+BY', query, re.IGNORECASE)),
            'has_group_by': bool(re.search(r'GROUP\s+BY', query, re.IGNORECASE)),
            'has_limit': bool(re.search(r'LIMIT', query, re.IGNORECASE)),
            'has_where': bool(re.search(r'WHERE', query, re.IGNORECASE)),
            'table_count': len(re.findall(r'FROM\s+(\w+)', query, re.IGNORECASE)),
            'join_count': len(re.findall(r'JOIN', query, re.IGNORECASE)),
            'optimization_suggestions': []
        }
        
        # Generate optimization suggestions
        if analysis['has_select_star']:
            analysis['optimization_suggestions'].append("Replace SELECT * with specific columns")
        
        if analysis['has_distinct'] and not analysis['has_group_by']:
            analysis['optimization_suggestions'].append("Consider if DISTINCT is necessary")
        
        if analysis['has_subquery']:
            analysis['optimization_suggestions'].append("Consider converting subqueries to JOINs")
        
        if analysis['has_order_by'] and not analysis['has_limit']:
            analysis['optimization_suggestions'].append("Add LIMIT to prevent large result sets")
        
        if analysis['table_count'] > 3:
            analysis['optimization_suggestions'].append("Consider query complexity with multiple tables")
        
        return analysis
    
    def record_query_metrics(self, metrics: QueryMetrics):
        """Record query performance metrics."""
        self.query_metrics.append(metrics)
        
        # Keep only recent metrics (last 1000 queries)
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
        
        # Check for performance issues
        self._check_performance_issues(metrics)
    
    def _check_performance_issues(self, metrics: QueryMetrics):
        """Check for performance issues."""
        issues = []
        
        if metrics.execution_time > self.performance_thresholds['slow_query_threshold']:
            issues.append(f"Slow query: {metrics.execution_time:.2f}s")
        
        if metrics.bytes_processed > self.performance_thresholds['high_bytes_threshold']:
            issues.append(f"High bytes processed: {metrics.bytes_processed:,}")
        
        if metrics.slot_ms > self.performance_thresholds['high_slots_threshold']:
            issues.append(f"High slot usage: {metrics.slot_ms:,}")
        
        if issues:
            logger.warning(f"Performance issues detected for query {metrics.query_id}: {', '.join(issues)}")
    
    def get_performance_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get query performance statistics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.query_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                'total_queries': 0,
                'avg_execution_time': 0,
                'total_bytes_processed': 0,
                'total_slot_ms': 0,
                'slow_queries': 0,
                'optimization_opportunities': 0
            }
        
        execution_times = [m.execution_time for m in recent_metrics]
        bytes_processed = [m.bytes_processed for m in recent_metrics]
        slot_ms = [m.slot_ms for m in recent_metrics]
        
        slow_queries = len([m for m in recent_metrics if m.execution_time > self.performance_thresholds['slow_query_threshold']])
        
        return {
            'total_queries': len(recent_metrics),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'total_bytes_processed': sum(bytes_processed),
            'avg_bytes_processed': sum(bytes_processed) / len(bytes_processed),
            'total_slot_ms': sum(slot_ms),
            'avg_slot_ms': sum(slot_ms) / len(slot_ms),
            'slow_queries': slow_queries,
            'slow_query_rate': slow_queries / len(recent_metrics),
            'optimization_opportunities': len([m for m in recent_metrics if m.optimization_level == OptimizationLevel.BASIC])
        }
    
    def get_optimization_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """Get optimization recommendations for a query."""
        recommendations = []
        analysis = self.analyze_query(query)
        
        # Basic recommendations
        if analysis['has_select_star']:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Replace SELECT * with specific columns',
                'description': 'SELECT * can cause performance issues and unnecessary data transfer',
                'impact': 'medium',
                'effort': 'low'
            })
        
        if analysis['has_distinct'] and not analysis['has_group_by']:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': 'Review DISTINCT usage',
                'description': 'DISTINCT can be expensive, ensure it is necessary',
                'impact': 'medium',
                'effort': 'low'
            })
        
        if analysis['has_subquery']:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'title': 'Consider JOIN instead of subquery',
                'description': 'JOINs are often more efficient than subqueries',
                'impact': 'high',
                'effort': 'medium'
            })
        
        if analysis['has_order_by'] and not analysis['has_limit']:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': 'Add LIMIT clause',
                'description': 'ORDER BY without LIMIT can return large result sets',
                'impact': 'medium',
                'effort': 'low'
            })
        
        if analysis['table_count'] > 3:
            recommendations.append({
                'type': 'complexity',
                'priority': 'low',
                'title': 'Consider query complexity',
                'description': 'Multiple table joins can impact performance',
                'impact': 'low',
                'effort': 'high'
            })
        
        return recommendations
    
    def create_query_index(self, table: str, columns: List[str], index_type: str = "btree") -> str:
        """Generate CREATE INDEX statement."""
        index_name = f"idx_{table}_{'_'.join(columns)}"
        columns_str = ", ".join(columns)
        
        return f"CREATE INDEX {index_name} ON {table} ({columns_str}) USING {index_type};"
    
    def analyze_table_stats(self, table: str) -> Dict[str, Any]:
        """Analyze table statistics for optimization."""
        # This would typically query system tables
        # For now, return mock data
        return {
            'table_name': table,
            'row_count': 1000000,
            'size_bytes': 500000000,
            'index_count': 3,
            'last_analyzed': datetime.utcnow(),
            'fragmentation': 0.15,
            'recommendations': [
                'Consider adding index on frequently queried columns',
                'Update table statistics regularly',
                'Consider partitioning for large tables'
            ]
        }

class BigQueryOptimizer(QueryOptimizer):
    """BigQuery-specific query optimizer."""
    
    def __init__(self):
        """Initialize BigQuery optimizer."""
        super().__init__()
        self.bigquery_rules = self._load_bigquery_rules()
    
    def _load_bigquery_rules(self) -> List[OptimizationRule]:
        """Load BigQuery-specific optimization rules."""
        rules = [
            # BigQuery-specific optimizations
            OptimizationRule(
                rule_id="bigquery_partition_pruning",
                name="BigQuery Partition Pruning",
                description="Add partition filters for BigQuery tables",
                pattern=r"FROM\s+`([^`]+)`\s+WHERE",
                replacement="FROM `\\1` WHERE _PARTITIONTIME >= TIMESTAMP('start_date') AND _PARTITIONTIME <= TIMESTAMP('end_date') AND",
                conditions=["partitioned_table"],
                priority=1
            ),
            
            OptimizationRule(
                rule_id="bigquery_cluster_optimization",
                name="BigQuery Cluster Optimization",
                description="Optimize cluster key usage",
                pattern=r"WHERE\s+(\w+)\s*=\s*@(\w+)",
                replacement="WHERE \\1 = @\\2",
                conditions=["clustered_table"],
                priority=2
            ),
            
            OptimizationRule(
                rule_id="bigquery_unnest_optimization",
                name="BigQuery UNNEST Optimization",
                description="Optimize UNNEST operations",
                pattern=r"UNNEST\(([^)]+)\)",
                replacement="UNNEST(\\1) WITH OFFSET",
                conditions=["array_column"],
                priority=3
            ),
            
            OptimizationRule(
                rule_id="bigquery_window_function",
                name="BigQuery Window Function Optimization",
                description="Optimize window functions",
                pattern=r"ROW_NUMBER\(\)\s+OVER\s+\([^)]+\)",
                replacement="ROW_NUMBER() OVER (PARTITION BY key ORDER BY value)",
                conditions=["window_function"],
                priority=4
            ),
            
            OptimizationRule(
                rule_id="bigquery_approximate_functions",
                name="BigQuery Approximate Functions",
                description="Use approximate functions when precision is not critical",
                pattern=r"COUNT\(DISTINCT\s+([^)]+)\)",
                replacement="APPROX_COUNT_DISTINCT(\\1)",
                conditions=["large_dataset"],
                priority=5
            )
        ]
        
        return rules
    
    def optimize_bigquery_query(self, query: str) -> str:
        """Optimize BigQuery-specific query."""
        optimized_query = query
        
        # Apply BigQuery-specific rules
        for rule in self.bigquery_rules:
            if rule.enabled:
                try:
                    if re.search(rule.pattern, optimized_query, re.IGNORECASE):
                        optimized_query = re.sub(rule.pattern, rule.replacement, optimized_query, flags=re.IGNORECASE)
                        logger.debug(f"Applied BigQuery optimization rule: {rule.name}")
                except Exception as e:
                    logger.warning(f"Failed to apply BigQuery rule {rule.name}: {e}")
        
        # Apply general optimizations
        return self.optimize_query(optimized_query, OptimizationLevel.ADVANCED)
    
    def get_bigquery_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """Get BigQuery-specific optimization recommendations."""
        recommendations = []
        
        # Check for BigQuery-specific patterns
        if re.search(r'SELECT\s+\*', query, re.IGNORECASE):
            recommendations.append({
                'type': 'bigquery',
                'priority': 'high',
                'title': 'Avoid SELECT * in BigQuery',
                'description': 'BigQuery charges by bytes processed, SELECT * processes all columns',
                'impact': 'high',
                'effort': 'low'
            })
        
        if re.search(r'COUNT\(DISTINCT', query, re.IGNORECASE):
            recommendations.append({
                'type': 'bigquery',
                'priority': 'medium',
                'title': 'Consider APPROX_COUNT_DISTINCT',
                'description': 'Use approximate functions for better performance on large datasets',
                'impact': 'medium',
                'effort': 'low'
            })
        
        if re.search(r'UNNEST', query, re.IGNORECASE):
            recommendations.append({
                'type': 'bigquery',
                'priority': 'medium',
                'title': 'Optimize UNNEST operations',
                'description': 'Consider using WITH OFFSET for better performance',
                'impact': 'medium',
                'effort': 'low'
            })
        
        return recommendations

# Global optimizer instances
query_optimizer = QueryOptimizer()
bigquery_optimizer = BigQueryOptimizer()

def optimize_query(query: str, optimization_level: OptimizationLevel = OptimizationLevel.BASIC) -> str:
    """Optimize SQL query."""
    return query_optimizer.optimize_query(query, optimization_level)

def optimize_bigquery_query(query: str) -> str:
    """Optimize BigQuery query."""
    return bigquery_optimizer.optimize_bigquery_query(query)

def analyze_query(query: str) -> Dict[str, Any]:
    """Analyze query for optimization opportunities."""
    return query_optimizer.analyze_query(query)

def get_optimization_recommendations(query: str) -> List[Dict[str, Any]]:
    """Get optimization recommendations for a query."""
    return query_optimizer.get_optimization_recommendations(query)

def get_bigquery_recommendations(query: str) -> List[Dict[str, Any]]:
    """Get BigQuery-specific optimization recommendations."""
    return bigquery_optimizer.get_bigquery_recommendations(query)
