#!/bin/bash
# Performance optimization setup script for MergeMind

set -e

echo "🚀 Setting up MergeMind performance optimization..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Check if Redis is available (optional)
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis CLI found"
    REDIS_AVAILABLE=true
else
    echo "⚠️  Redis CLI not found - caching will use in-memory fallback"
    REDIS_AVAILABLE=false
fi

echo "✅ Prerequisites check passed."

# Create necessary directories
echo "📁 Creating performance directories..."
mkdir -p performance/cache
mkdir -p performance/optimization
mkdir -p performance/async
mkdir -p performance/monitoring
mkdir -p performance/logs
mkdir -p performance/config

echo "✅ Performance directories created."

# Install Python dependencies
echo "🔧 Installing Python dependencies..."

# Install cache dependencies
if [ -f "performance/cache/requirements.txt" ]; then
    pip3 install -r performance/cache/requirements.txt
fi

# Install optimization dependencies
if [ -f "performance/optimization/requirements.txt" ]; then
    pip3 install -r performance/optimization/requirements.txt
fi

# Install async dependencies
if [ -f "performance/async/requirements.txt" ]; then
    pip3 install -r performance/async/requirements.txt
fi

# Install monitoring dependencies
if [ -f "performance/monitoring/requirements.txt" ]; then
    pip3 install -r performance/monitoring/requirements.txt
fi

echo "✅ Dependencies installed."

# Create performance configuration
echo "⚙️ Creating performance configuration..."

cat > performance/config/performance_config.yml << EOF
# MergeMind Performance Configuration

performance:
  # Caching configuration
  cache:
    redis:
      host: "localhost"
      port: 6379
      db: 0
      password: null
      max_connections: 20
      socket_timeout: 5
      socket_connect_timeout: 5
      retry_on_timeout: true
    
    memory:
      max_size: 10000
      default_ttl: 3600
    
    namespaces:
      mr_data: 1800      # 30 minutes
      user_data: 3600    # 1 hour
      project_data: 7200 # 2 hours
      ai_summaries: 86400 # 24 hours
      risk_scores: 1800   # 30 minutes
      reviewer_suggestions: 3600 # 1 hour
      api_responses: 300  # 5 minutes
      static_data: 86400  # 24 hours
  
  # Query optimization
  query_optimization:
    enabled: true
    optimization_level: "intermediate"  # basic, intermediate, advanced, aggressive
    slow_query_threshold: 5.0  # seconds
    high_bytes_threshold: 1000000000  # 1GB
    high_slots_threshold: 1000000  # 1M slot-ms
    
    rules:
      select_star_elimination: true
      unnecessary_distinct: true
      index_hint: true
      join_optimization: true
      subquery_to_join: true
      date_function_optimization: true
      string_function_optimization: true
      aggregation_optimization: true
      limit_optimization: true
      partition_pruning: true
  
  # Async processing
  async:
    max_concurrent_tasks: 10
    max_workers: 4
    task_timeout: 300  # 5 minutes
    max_retries: 3
    
    batch_processing:
      batch_size: 100
      max_concurrent_batches: 5
    
    rate_limiting:
      enabled: true
      requests_per_second: 10
      burst_size: 20
  
  # Performance monitoring
  monitoring:
    enabled: true
    collection_interval: 1.0  # seconds
    metrics_retention_hours: 24
    alert_check_interval: 60  # seconds
    
    system_metrics:
      cpu: true
      memory: true
      disk: true
      network: true
      processes: true
    
    application_metrics:
      requests: true
      errors: true
      cache: true
      database: true
      ai_requests: true
    
    alerts:
      high_cpu_usage:
        threshold: 80.0
        level: "warning"
      critical_cpu_usage:
        threshold: 95.0
        level: "critical"
      high_memory_usage:
        threshold: 85.0
        level: "warning"
      critical_memory_usage:
        threshold: 95.0
        level: "critical"
      high_disk_usage:
        threshold: 90.0
        level: "warning"
      low_cache_hit_rate:
        threshold: 50.0
        level: "warning"
      high_error_rate:
        threshold: 10.0
        level: "error"
      slow_request_duration:
        threshold: 5.0
        level: "warning"
  
  # Database optimization
  database:
    connection_pooling:
      enabled: true
      max_connections: 20
      min_connections: 2
      connection_timeout: 30
    
    query_optimization:
      enabled: true
      explain_queries: false
      slow_query_logging: true
      query_cache_size: 1000
    
    bigquery:
      optimization_enabled: true
      use_approximate_functions: true
      partition_pruning: true
      cluster_optimization: true
  
  # API optimization
  api:
    response_compression:
      enabled: true
      min_size: 1024  # bytes
    
    request_validation:
      enabled: true
      max_request_size: 10485760  # 10MB
    
    rate_limiting:
      enabled: true
      requests_per_minute: 100
      requests_per_hour: 1000
    
    caching:
      enabled: true
      default_ttl: 300  # 5 minutes
      max_cache_size: 1000
  
  # AI optimization
  ai:
    request_batching:
      enabled: true
      batch_size: 10
      batch_timeout: 1.0  # seconds
    
    response_caching:
      enabled: true
      ttl: 3600  # 1 hour
    
    model_optimization:
      enabled: true
      use_approximate_models: false
      max_tokens: 1000
      temperature: 0.7
EOF

echo "✅ Performance configuration created."

# Create performance monitoring script
echo "📊 Creating performance monitoring script..."

cat > performance/monitor_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Performance monitoring script for MergeMind.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add performance modules to path
sys.path.append(str(Path(__file__).parent))

from monitoring.performance_monitor import (
    performance_collector, 
    alert_manager, 
    performance_dashboard,
    start_performance_monitoring,
    stop_performance_monitoring
)

def check_performance_status():
    """Check overall performance status."""
    print("🚀 MergeMind Performance Status Check")
    print("=" * 50)
    
    # Get dashboard data
    dashboard_data = performance_dashboard.get_dashboard_data(1)  # Last hour
    
    # System health
    print(f"\n🏥 System Health: {dashboard_data['system_health'].upper()}")
    
    # KPIs
    kpis = dashboard_data.get('kpis', {})
    print(f"\n📊 Key Performance Indicators:")
    if 'cpu_avg' in kpis:
        print(f"  CPU Usage: {kpis['cpu_avg']:.1f}% (max: {kpis.get('cpu_max', 0):.1f}%)")
    if 'memory_avg' in kpis:
        print(f"  Memory Usage: {kpis['memory_avg']:.1f}% (max: {kpis.get('memory_max', 0):.1f}%)")
    if 'request_duration_avg' in kpis:
        print(f"  Request Duration: {kpis['request_duration_avg']:.3f}s (p95: {kpis.get('request_duration_p95', 0):.3f}s)")
    if 'cache_hit_rate_avg' in kpis:
        print(f"  Cache Hit Rate: {kpis['cache_hit_rate_avg']:.1f}%")
    
    # Active alerts
    active_alerts = dashboard_data.get('alerts', [])
    print(f"\n🚨 Active Alerts: {len(active_alerts)}")
    for alert in active_alerts[:5]:  # Show first 5 alerts
        print(f"  {alert['level'].upper()}: {alert['message']} ({alert['metric']}={alert['value']})")
    
    # System metrics
    system_metrics = dashboard_data.get('system_metrics', {})
    print(f"\n💻 System Metrics:")
    print(f"  CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
    print(f"  Memory: {system_metrics.get('memory_percent', 0):.1f}%")
    print(f"  Disk: {system_metrics.get('disk_usage_percent', 0):.1f}%")
    print(f"  Processes: {system_metrics.get('process_count', 0)}")
    
    # Application metrics
    app_metrics = dashboard_data.get('app_metrics', {})
    print(f"\n📱 Application Metrics:")
    print(f"  Requests: {app_metrics.get('request_count', 0)}")
    print(f"  Errors: {app_metrics.get('error_count', 0)}")
    print(f"  Cache Hits: {app_metrics.get('cache_hits', 0)}")
    print(f"  Cache Misses: {app_metrics.get('cache_misses', 0)}")
    print(f"  Database Queries: {app_metrics.get('database_queries', 0)}")
    print(f"  AI Requests: {app_metrics.get('ai_requests', 0)}")
    
    print("\n" + "=" * 50)
    print("Performance status check completed.")

def monitor_performance_realtime():
    """Monitor performance in real-time."""
    print("🚀 MergeMind Real-time Performance Monitor")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            # Clear screen (Unix/Linux/Mac)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Get current dashboard data
            dashboard_data = performance_dashboard.get_dashboard_data(0.1)  # Last 6 minutes
            
            # Display header
            print("🚀 MergeMind Real-time Performance Monitor")
            print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            
            # System health
            health = dashboard_data['system_health']
            health_emoji = "🟢" if health == "excellent" else "🟡" if health == "good" else "🟠" if health == "fair" else "🔴"
            print(f"\n{health_emoji} System Health: {health.upper()}")
            
            # System metrics
            system_metrics = dashboard_data.get('system_metrics', {})
            print(f"\n💻 System Resources:")
            print(f"  CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
            print(f"  Memory: {system_metrics.get('memory_percent', 0):.1f}%")
            print(f"  Disk: {system_metrics.get('disk_usage_percent', 0):.1f}%")
            
            # Application metrics
            app_metrics = dashboard_data.get('app_metrics', {})
            print(f"\n📱 Application:")
            print(f"  Requests: {app_metrics.get('request_count', 0)}")
            print(f"  Errors: {app_metrics.get('error_count', 0)}")
            print(f"  Active Connections: {app_metrics.get('active_connections', 0)}")
            
            # Cache metrics
            cache_hits = app_metrics.get('cache_hits', 0)
            cache_misses = app_metrics.get('cache_misses', 0)
            total_cache = cache_hits + cache_misses
            cache_rate = (cache_hits / total_cache * 100) if total_cache > 0 else 0
            print(f"  Cache Hit Rate: {cache_rate:.1f}% ({cache_hits}/{total_cache})")
            
            # Active alerts
            active_alerts = dashboard_data.get('alerts', [])
            if active_alerts:
                print(f"\n🚨 Active Alerts ({len(active_alerts)}):")
                for alert in active_alerts[:3]:  # Show first 3 alerts
                    level_emoji = "🔴" if alert['level'] == 'critical' else "🟠" if alert['level'] == 'error' else "🟡"
                    print(f"  {level_emoji} {alert['message']}")
            else:
                print(f"\n✅ No active alerts")
            
            print("\n" + "=" * 50)
            print("Press Ctrl+C to stop monitoring")
            
            # Wait before next update
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

def generate_performance_report(hours=24):
    """Generate performance report."""
    print(f"📊 MergeMind Performance Report (Last {hours} hours)")
    print("=" * 50)
    
    # Get dashboard data
    dashboard_data = performance_dashboard.get_dashboard_data(hours)
    
    # Generate report
    report = {
        'report_generated': datetime.now().isoformat(),
        'time_range_hours': hours,
        'system_health': dashboard_data['system_health'],
        'kpis': dashboard_data.get('kpis', {}),
        'alerts': dashboard_data.get('alerts', []),
        'system_metrics': dashboard_data.get('system_metrics', {}),
        'app_metrics': dashboard_data.get('app_metrics', {}),
        'recommendations': []
    }
    
    # Generate recommendations
    kpis = report['kpis']
    if kpis.get('cpu_avg', 0) > 70:
        report['recommendations'].append("Consider optimizing CPU-intensive operations")
    if kpis.get('memory_avg', 0) > 80:
        report['recommendations'].append("Consider increasing memory or optimizing memory usage")
    if kpis.get('request_duration_avg', 0) > 2.0:
        report['recommendations'].append("Consider optimizing slow API endpoints")
    if kpis.get('cache_hit_rate_avg', 0) < 70:
        report['recommendations'].append("Consider improving cache strategy")
    
    # Save report
    report_file = f"performance/reports/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Report saved to: {report_file}")
    
    # Display summary
    print(f"\n📈 Performance Summary:")
    print(f"  System Health: {report['system_health'].upper()}")
    print(f"  Active Alerts: {len(report['alerts'])}")
    print(f"  Recommendations: {len(report['recommendations'])}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    return report_file

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MergeMind Performance Monitor")
    parser.add_argument("--status", action="store_true", help="Check performance status")
    parser.add_argument("--monitor", action="store_true", help="Real-time monitoring")
    parser.add_argument("--report", action="store_true", help="Generate performance report")
    parser.add_argument("--hours", type=int, default=24, help="Hours for report")
    
    args = parser.parse_args()
    
    if args.status:
        check_performance_status()
    elif args.monitor:
        monitor_performance_realtime()
    elif args.report:
        generate_performance_report(args.hours)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
EOF

chmod +x performance/monitor_performance.py

echo "✅ Performance monitoring script created."

# Create performance optimization script
echo "🔧 Creating performance optimization script..."

cat > performance/optimize_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Performance optimization script for MergeMind.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add performance modules to path
sys.path.append(str(Path(__file__).parent))

from optimization.query_optimizer import query_optimizer, bigquery_optimizer
from cache.redis_cache import cache_manager
from async.async_optimizer import async_task_manager

def optimize_queries():
    """Optimize database queries."""
    print("🔍 Optimizing Database Queries...")
    
    # Example queries to optimize
    sample_queries = [
        "SELECT * FROM merge_requests WHERE project_id = 123",
        "SELECT DISTINCT author_id FROM merge_requests WHERE state = 'merged'",
        "SELECT COUNT(*) FROM merge_requests WHERE created_at > '2024-01-01'",
        "SELECT mr.*, p.name FROM merge_requests mr JOIN projects p ON mr.project_id = p.id",
        "SELECT * FROM merge_requests WHERE DATE(created_at) = '2024-01-01'"
    ]
    
    optimizations = []
    
    for query in sample_queries:
        # Analyze query
        analysis = query_optimizer.analyze_query(query)
        
        # Get recommendations
        recommendations = query_optimizer.get_optimization_recommendations(query)
        
        # Optimize query
        optimized_query = query_optimizer.optimize_query(query)
        
        # BigQuery-specific optimization
        bigquery_optimized = bigquery_optimizer.optimize_bigquery_query(query)
        bigquery_recommendations = bigquery_optimizer.get_bigquery_recommendations(query)
        
        optimization = {
            'original_query': query,
            'optimized_query': optimized_query,
            'bigquery_optimized': bigquery_optimized,
            'analysis': analysis,
            'recommendations': recommendations,
            'bigquery_recommendations': bigquery_recommendations
        }
        
        optimizations.append(optimization)
        
        print(f"  ✅ Optimized query: {query[:50]}...")
    
    # Save optimizations
    optimization_file = f"performance/optimizations/query_optimizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(optimization_file), exist_ok=True)
    
    with open(optimization_file, 'w') as f:
        json.dump(optimizations, f, indent=2, default=str)
    
    print(f"Query optimizations saved to: {optimization_file}")
    
    return optimizations

def optimize_cache():
    """Optimize cache configuration."""
    print("💾 Optimizing Cache Configuration...")
    
    # Get cache statistics
    cache_stats = cache_manager.get_stats()
    
    print(f"  Cache Statistics:")
    print(f"    Hits: {cache_stats['combined']['hits']}")
    print(f"    Misses: {cache_stats['combined']['misses']}")
    print(f"    Hit Rate: {cache_stats['combined']['hit_rate']:.2%}")
    
    # Cache optimization recommendations
    recommendations = []
    
    if cache_stats['combined']['hit_rate'] < 0.7:
        recommendations.append("Consider increasing cache TTL for frequently accessed data")
        recommendations.append("Review cache key strategy for better hit rates")
    
    if cache_stats['combined']['misses'] > cache_stats['combined']['hits']:
        recommendations.append("Consider pre-warming cache for critical data")
        recommendations.append("Review cache invalidation strategy")
    
    # Save cache optimization report
    cache_report = {
        'timestamp': datetime.now().isoformat(),
        'cache_stats': cache_stats,
        'recommendations': recommendations
    }
    
    cache_file = f"performance/optimizations/cache_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    with open(cache_file, 'w') as f:
        json.dump(cache_report, f, indent=2, default=str)
    
    print(f"Cache optimization report saved to: {cache_file}")
    
    if recommendations:
        print(f"  💡 Recommendations:")
        for rec in recommendations:
            print(f"    - {rec}")
    
    return cache_report

def optimize_async_processing():
    """Optimize async processing."""
    print("⚡ Optimizing Async Processing...")
    
    # Get async task manager statistics
    async_stats = async_task_manager.get_stats()
    
    print(f"  Async Task Statistics:")
    print(f"    Total Tasks: {async_stats['total_tasks']}")
    print(f"    Completed: {async_stats['completed_tasks']}")
    print(f"    Failed: {async_stats['failed_tasks']}")
    print(f"    Success Rate: {async_stats['success_rate']:.2%}")
    print(f"    Avg Execution Time: {async_stats['avg_execution_time']:.2f}s")
    
    # Async optimization recommendations
    recommendations = []
    
    if async_stats['success_rate'] < 0.9:
        recommendations.append("Review failed task error handling")
        recommendations.append("Consider increasing retry attempts")
    
    if async_stats['avg_execution_time'] > 5.0:
        recommendations.append("Consider optimizing slow tasks")
        recommendations.append("Review task priority and resource allocation")
    
    if async_stats['running_tasks'] > 8:
        recommendations.append("Consider increasing max concurrent tasks")
    
    # Save async optimization report
    async_report = {
        'timestamp': datetime.now().isoformat(),
        'async_stats': async_stats,
        'recommendations': recommendations
    }
    
    async_file = f"performance/optimizations/async_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(async_file), exist_ok=True)
    
    with open(async_file, 'w') as f:
        json.dump(async_report, f, indent=2, default=str)
    
    print(f"Async optimization report saved to: {async_file}")
    
    if recommendations:
        print(f"  💡 Recommendations:")
        for rec in recommendations:
            print(f"    - {rec}")
    
    return async_report

def generate_optimization_report():
    """Generate comprehensive optimization report."""
    print("📊 Generating Performance Optimization Report...")
    
    # Run all optimizations
    query_optimizations = optimize_queries()
    cache_optimization = optimize_cache()
    async_optimization = optimize_async_processing()
    
    # Compile comprehensive report
    report = {
        'report_generated': datetime.now().isoformat(),
        'query_optimizations': query_optimizations,
        'cache_optimization': cache_optimization,
        'async_optimization': async_optimization,
        'summary': {
            'total_queries_optimized': len(query_optimizations),
            'cache_hit_rate': cache_optimization['cache_stats']['combined']['hit_rate'],
            'async_success_rate': async_optimization['async_stats']['success_rate']
        }
    }
    
    # Save comprehensive report
    report_file = f"performance/reports/optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"Comprehensive optimization report saved to: {report_file}")
    
    # Display summary
    print(f"\n📈 Optimization Summary:")
    print(f"  Queries Optimized: {report['summary']['total_queries_optimized']}")
    print(f"  Cache Hit Rate: {report['summary']['cache_hit_rate']:.2%}")
    print(f"  Async Success Rate: {report['summary']['async_success_rate']:.2%}")
    
    return report_file

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MergeMind Performance Optimizer")
    parser.add_argument("--queries", action="store_true", help="Optimize database queries")
    parser.add_argument("--cache", action="store_true", help="Optimize cache configuration")
    parser.add_argument("--async", action="store_true", help="Optimize async processing")
    parser.add_argument("--all", action="store_true", help="Run all optimizations")
    
    args = parser.parse_args()
    
    if args.queries:
        optimize_queries()
    elif args.cache:
        optimize_cache()
    elif args.async:
        optimize_async_processing()
    elif args.all:
        generate_optimization_report()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
EOF

chmod +x performance/optimize_performance.py

echo "✅ Performance optimization script created."

# Create performance test script
echo "🧪 Creating performance test script..."

cat > performance/test_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Performance test script for MergeMind.
"""

import os
import sys
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Add performance modules to path
sys.path.append(str(Path(__file__).parent))

from cache.redis_cache import cache_manager, cached
from optimization.query_optimizer import optimize_query, analyze_query
from async.async_optimizer import async_task_manager, async_task, TaskPriority
from monitoring.performance_monitor import (
    performance_collector, 
    record_request_metrics, 
    record_cache_metrics,
    record_database_metrics,
    record_ai_metrics
)

def test_cache_performance():
    """Test cache performance."""
    print("💾 Testing Cache Performance...")
    
    # Test cache operations
    test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
    
    # Test set operation
    start_time = time.time()
    success = cache_manager.set("test_key", test_data, ttl=300, namespace="test")
    set_time = time.time() - start_time
    
    # Test get operation
    start_time = time.time()
    retrieved_data = cache_manager.get("test_key", namespace="test")
    get_time = time.time() - start_time
    
    # Test cache decorator
    @cached(ttl=300, namespace="test")
    def expensive_function(n):
        time.sleep(0.1)  # Simulate expensive operation
        return n * 2
    
    # First call (cache miss)
    start_time = time.time()
    result1 = expensive_function(5)
    first_call_time = time.time() - start_time
    
    # Second call (cache hit)
    start_time = time.time()
    result2 = expensive_function(5)
    second_call_time = time.time() - start_time
    
    print(f"  Cache Set: {set_time:.4f}s")
    print(f"  Cache Get: {get_time:.4f}s")
    print(f"  First Call: {first_call_time:.4f}s")
    print(f"  Second Call: {second_call_time:.4f}s")
    print(f"  Cache Speedup: {first_call_time/second_call_time:.2f}x")
    
    # Record cache metrics
    record_cache_metrics(True)  # Hit
    record_cache_metrics(False)  # Miss
    
    return {
        'set_time': set_time,
        'get_time': get_time,
        'first_call_time': first_call_time,
        'second_call_time': second_call_time,
        'speedup': first_call_time/second_call_time
    }

def test_query_optimization():
    """Test query optimization."""
    print("🔍 Testing Query Optimization...")
    
    # Test queries
    test_queries = [
        "SELECT * FROM merge_requests WHERE project_id = 123",
        "SELECT DISTINCT author_id FROM merge_requests WHERE state = 'merged'",
        "SELECT COUNT(*) FROM merge_requests WHERE created_at > '2024-01-01'"
    ]
    
    results = []
    
    for query in test_queries:
        # Analyze query
        analysis = analyze_query(query)
        
        # Optimize query
        optimized = optimize_query(query)
        
        results.append({
            'original': query,
            'optimized': optimized,
            'analysis': analysis
        })
        
        print(f"  ✅ Optimized: {query[:50]}...")
    
    return results

async def test_async_performance():
    """Test async performance."""
    print("⚡ Testing Async Performance...")
    
    # Test async task
    @async_task(priority=TaskPriority.HIGH, max_retries=2, timeout=10.0)
    async def test_task(n):
        await asyncio.sleep(0.1)  # Simulate async work
        return n * 2
    
    # Submit multiple tasks
    start_time = time.time()
    task_ids = []
    
    for i in range(10):
        task_id = await async_task_manager.submit_task(
            test_task(i),
            priority=TaskPriority.NORMAL
        )
        task_ids.append(task_id)
    
    # Wait for completion
    results = []
    for task_id in task_ids:
        result = await async_task_manager.get_task_result(task_id)
        results.append(result)
    
    total_time = time.time() - start_time
    
    print(f"  Tasks Submitted: {len(task_ids)}")
    print(f"  Total Time: {total_time:.4f}s")
    print(f"  Avg Time per Task: {total_time/len(task_ids):.4f}s")
    
    return {
        'tasks': len(task_ids),
        'total_time': total_time,
        'avg_time': total_time/len(task_ids),
        'results': results
    }

def test_performance_monitoring():
    """Test performance monitoring."""
    print("📊 Testing Performance Monitoring...")
    
    # Simulate various operations
    for i in range(10):
        # Simulate request
        duration = 0.1 + (i * 0.01)  # Varying durations
        status_code = 200 if i < 8 else 500  # Some errors
        record_request_metrics(duration, status_code)
        
        # Simulate database query
        query_duration = 0.05 + (i * 0.005)
        record_database_metrics(query_duration)
        
        # Simulate AI request
        ai_duration = 0.2 + (i * 0.02)
        record_ai_metrics(ai_duration)
        
        time.sleep(0.01)  # Small delay
    
    # Get performance statistics
    stats = performance_collector.get_metric_summary(0.1)  # Last 6 minutes
    
    print(f"  Metrics Collected: {stats['total_metrics']}")
    print(f"  Request Metrics: {len(stats['metrics_by_name'].get('app.request_duration', []))}")
    print(f"  Database Metrics: {len(stats['metrics_by_name'].get('app.database_query_duration', []))}")
    print(f"  AI Metrics: {len(stats['metrics_by_name'].get('app.ai_request_duration', []))}")
    
    return stats

def run_performance_tests():
    """Run all performance tests."""
    print("🚀 MergeMind Performance Test Suite")
    print("=" * 50)
    
    test_results = {}
    
    # Test cache performance
    try:
        test_results['cache'] = test_cache_performance()
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        test_results['cache'] = {'error': str(e)}
    
    # Test query optimization
    try:
        test_results['queries'] = test_query_optimization()
    except Exception as e:
        print(f"❌ Query optimization test failed: {e}")
        test_results['queries'] = {'error': str(e)}
    
    # Test async performance
    try:
        test_results['async'] = asyncio.run(test_async_performance())
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        test_results['async'] = {'error': str(e)}
    
    # Test performance monitoring
    try:
        test_results['monitoring'] = test_performance_monitoring()
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        test_results['monitoring'] = {'error': str(e)}
    
    # Save test results
    import json
    test_file = f"performance/tests/performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\nTest results saved to: {test_file}")
    
    # Display summary
    print(f"\n📈 Test Summary:")
    for test_name, result in test_results.items():
        if 'error' in result:
            print(f"  ❌ {test_name}: FAILED")
        else:
            print(f"  ✅ {test_name}: PASSED")
    
    return test_results

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MergeMind Performance Test Suite")
    parser.add_argument("--cache", action="store_true", help="Test cache performance")
    parser.add_argument("--queries", action="store_true", help="Test query optimization")
    parser.add_argument("--async", action="store_true", help="Test async performance")
    parser.add_argument("--monitoring", action="store_true", help="Test performance monitoring")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.cache:
        test_cache_performance()
    elif args.queries:
        test_query_optimization()
    elif args.async:
        asyncio.run(test_async_performance())
    elif args.monitoring:
        test_performance_monitoring()
    elif args.all:
        run_performance_tests()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
EOF

chmod +x performance/test_performance.py

echo "✅ Performance test script created."

# Create performance documentation
echo "📚 Creating performance documentation..."

cat > performance/README.md << 'EOF'
# MergeMind Performance Optimization

Comprehensive performance optimization system for MergeMind, including caching, query optimization, async processing, and performance monitoring.

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Performance Layer"
        CACHE[Redis Cache]
        OPT[Query Optimizer]
        ASYNC[Async Manager]
        MON[Performance Monitor]
    end
    
    subgraph "Application Layer"
        API[FastAPI Application]
        UI[React Application]
        BOT[Slack Bot]
    end
    
    subgraph "Data Layer"
        BQ[BigQuery]
        GL[GitLab API]
        VAI[Vertex AI]
    end
    
    API --> CACHE
    API --> OPT
    API --> ASYNC
    API --> MON
    
    UI --> CACHE
    BOT --> ASYNC
    
    OPT --> BQ
    ASYNC --> GL
    MON --> VAI
```

## 📦 Components

### Caching System
- **Redis Cache**: High-performance distributed caching
- **Memory Cache**: In-memory fallback cache
- **Cache Manager**: Multi-layer cache management
- **Cache Decorators**: Easy caching integration

### Query Optimization
- **Query Analyzer**: SQL query analysis
- **Optimization Rules**: Automated query optimization
- **BigQuery Optimizer**: BigQuery-specific optimizations
- **Performance Metrics**: Query performance tracking

### Async Processing
- **Task Manager**: Priority-based task execution
- **Batch Processor**: Efficient batch processing
- **Rate Limiter**: Request rate control
- **Connection Pool**: Database connection management

### Performance Monitoring
- **Metrics Collector**: System and application metrics
- **Alert Manager**: Performance alerting
- **Dashboard**: Real-time performance dashboard
- **Performance Reports**: Comprehensive performance analysis

## 🚀 Quick Start

### Setup
```bash
# Run performance setup
./performance/setup.sh

# Test performance components
python3 performance/test_performance.py --all

# Monitor performance
python3 performance/monitor_performance.py --status
```

### Usage Examples

#### Caching
```python
from performance.cache.redis_cache import cached, cache_manager

# Cache function results
@cached(ttl=300, namespace="mr_data")
def get_merge_request(mr_id: int):
    # Expensive operation
    return fetch_mr_from_api(mr_id)

# Direct cache operations
cache_manager.set("key", "value", ttl=3600, namespace="default")
value = cache_manager.get("key", namespace="default")
```

#### Query Optimization
```python
from performance.optimization.query_optimizer import optimize_query, analyze_query

# Analyze query
analysis = analyze_query("SELECT * FROM merge_requests WHERE project_id = 123")

# Optimize query
optimized = optimize_query("SELECT * FROM merge_requests WHERE project_id = 123")

# Get recommendations
recommendations = get_optimization_recommendations(query)
```

#### Async Processing
```python
from performance.async.async_optimizer import async_task, TaskPriority

# Async task execution
@async_task(priority=TaskPriority.HIGH, max_retries=3, timeout=30.0)
async def process_mr_data(mr_id: int):
    # Async operation
    return await fetch_and_process_mr(mr_id)

# Batch processing
@async_batch(batch_size=100, max_concurrent=5)
async def process_mr_batch(mr_ids: List[int]):
    # Process batch
    return await process_multiple_mrs(mr_ids)
```

#### Performance Monitoring
```python
from performance.monitoring.performance_monitor import (
    record_request_metrics, 
    record_cache_metrics,
    record_database_metrics
)

# Record metrics
record_request_metrics(duration=0.5, status_code=200)
record_cache_metrics(hit=True)
record_database_metrics(duration=0.1)
```

## ⚙️ Configuration

### Environment Variables
```bash
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password

# Performance thresholds
SLOW_QUERY_THRESHOLD=5.0
HIGH_CPU_THRESHOLD=80.0
HIGH_MEMORY_THRESHOLD=85.0
```

### Performance Configuration
```yaml
# performance/config/performance_config.yml
performance:
  cache:
    redis:
      host: "localhost"
      port: 6379
      max_connections: 20
    
    memory:
      max_size: 10000
      default_ttl: 3600
  
  query_optimization:
    enabled: true
    optimization_level: "intermediate"
    slow_query_threshold: 5.0
  
  async:
    max_concurrent_tasks: 10
    max_workers: 4
    task_timeout: 300
  
  monitoring:
    enabled: true
    collection_interval: 1.0
    metrics_retention_hours: 24
```

## 🔧 Management

### Performance Monitoring
```bash
# Check performance status
python3 performance/monitor_performance.py --status

# Real-time monitoring
python3 performance/monitor_performance.py --monitor

# Generate performance report
python3 performance/monitor_performance.py --report --hours 24
```

### Performance Optimization
```bash
# Optimize database queries
python3 performance/optimize_performance.py --queries

# Optimize cache configuration
python3 performance/optimize_performance.py --cache

# Optimize async processing
python3 performance/optimize_performance.py --async

# Run all optimizations
python3 performance/optimize_performance.py --all
```

### Performance Testing
```bash
# Test cache performance
python3 performance/test_performance.py --cache

# Test query optimization
python3 performance/test_performance.py --queries

# Test async performance
python3 performance/test_performance.py --async

# Test performance monitoring
python3 performance/test_performance.py --monitoring

# Run all tests
python3 performance/test_performance.py --all
```

## 📊 Performance Metrics

### System Metrics
- **CPU Usage**: Processor utilization
- **Memory Usage**: RAM utilization
- **Disk Usage**: Storage utilization
- **Network I/O**: Network traffic
- **Process Count**: Active processes

### Application Metrics
- **Request Count**: HTTP requests
- **Request Duration**: Response times
- **Error Count**: Failed requests
- **Cache Hit Rate**: Cache effectiveness
- **Database Queries**: Query count and duration
- **AI Requests**: AI service usage

### Performance KPIs
- **Response Time**: API response times
- **Throughput**: Requests per second
- **Error Rate**: Error percentage
- **Cache Hit Rate**: Cache efficiency
- **Resource Utilization**: System resource usage

## 🚨 Alerting

### Alert Rules
- **High CPU Usage**: > 80% CPU utilization
- **High Memory Usage**: > 85% memory utilization
- **Slow Requests**: > 5s response time
- **Low Cache Hit Rate**: < 50% cache hits
- **High Error Rate**: > 10% error rate

### Alert Levels
- **INFO**: Informational alerts
- **WARNING**: Performance degradation
- **ERROR**: Service impact
- **CRITICAL**: System failure

## 🔍 Optimization Strategies

### Caching Optimization
- **Cache Warming**: Pre-load frequently accessed data
- **Cache Invalidation**: Smart cache invalidation
- **Cache Partitioning**: Distribute cache load
- **Cache Compression**: Reduce memory usage

### Query Optimization
- **Index Optimization**: Proper indexing strategy
- **Query Rewriting**: Optimize query structure
- **Partition Pruning**: Limit data scanning
- **Join Optimization**: Efficient join strategies

### Async Optimization
- **Task Prioritization**: Priority-based execution
- **Resource Pooling**: Efficient resource usage
- **Batch Processing**: Group operations
- **Rate Limiting**: Control request rates

### Monitoring Optimization
- **Metric Sampling**: Reduce metric collection overhead
- **Alert Tuning**: Optimize alert thresholds
- **Dashboard Optimization**: Efficient visualization
- **Report Generation**: Automated reporting

## 📈 Performance Tuning

### Database Tuning
- **Connection Pooling**: Optimize database connections
- **Query Caching**: Cache frequent queries
- **Index Optimization**: Improve query performance
- **Partitioning**: Optimize large tables

### Application Tuning
- **Memory Management**: Optimize memory usage
- **CPU Optimization**: Efficient CPU utilization
- **I/O Optimization**: Reduce disk I/O
- **Network Optimization**: Minimize network overhead

### Infrastructure Tuning
- **Load Balancing**: Distribute load
- **Auto Scaling**: Dynamic resource allocation
- **Resource Monitoring**: Track resource usage
- **Capacity Planning**: Plan for growth

## 🛠️ Development

### Adding Performance Features
1. **Design**: Plan performance feature
2. **Implementation**: Implement efficiently
3. **Testing**: Performance testing
4. **Monitoring**: Track performance impact
5. **Optimization**: Continuous improvement

### Performance Testing
```bash
# Load testing
python3 performance/load_test.py --users 100 --duration 300

# Stress testing
python3 performance/stress_test.py --max-load 1000

# Benchmark testing
python3 performance/benchmark_test.py --iterations 1000
```

## 📄 License

This performance optimization system is part of the MergeMind project and is licensed under the MIT License.
EOF

echo "✅ Performance documentation created."

# Set final permissions
echo "🔐 Setting final permissions..."
chmod 700 performance/
chmod 600 performance/config/performance_config.yml

echo ""
echo "🎉 Performance optimization setup complete!"
echo ""
echo "📊 Performance Components:"
echo "   ✅ Redis Cache - High-performance distributed caching"
echo "   ✅ Query Optimizer - SQL query optimization"
echo "   ✅ Async Manager - Priority-based task execution"
echo "   ✅ Performance Monitor - Real-time performance monitoring"
echo "   ✅ Alert Manager - Performance alerting"
echo "   ✅ Dashboard - Performance visualization"
echo "   ✅ Optimization Tools - Automated optimization"
echo "   ✅ Testing Suite - Performance testing"
echo ""
echo "🔧 Management Commands:"
echo "   Monitor: python3 performance/monitor_performance.py --status"
echo "   Optimize: python3 performance/optimize_performance.py --all"
echo "   Test: python3 performance/test_performance.py --all"
echo "   Real-time: python3 performance/monitor_performance.py --monitor"
echo ""
echo "📚 Documentation: performance/README.md"
echo ""
echo "⚠️  Important Performance Notes:"
echo "   - Monitor cache hit rates"
echo "   - Optimize slow queries"
echo "   - Use async processing for I/O operations"
echo "   - Set up performance alerts"
echo "   - Regular performance testing"
