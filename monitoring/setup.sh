#!/bin/bash
# Setup script for MergeMind monitoring stack

set -e

echo "🚀 Setting up MergeMind monitoring stack..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "❌ GCP_PROJECT_ID environment variable is not set."
    exit 1
fi

if [ -z "$GITLAB_BASE_URL" ]; then
    echo "❌ GITLAB_BASE_URL environment variable is not set."
    exit 1
fi

if [ -z "$GITLAB_TOKEN" ]; then
    echo "❌ GITLAB_TOKEN environment variable is not set."
    exit 1
fi

echo "✅ Prerequisites check passed."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p prometheus/rules
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/dashboards
mkdir -p alertmanager

# Create credentials file if it doesn't exist
if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json not found. Please create it with your GCP service account key."
    echo "   You can download it from: https://console.cloud.google.com/iam-admin/serviceaccounts"
    exit 1
fi

# Set up environment file
echo "🔧 Setting up environment..."
cat > .env << EOF
# GCP Configuration
GCP_PROJECT_ID=${GCP_PROJECT_ID}
BQ_DATASET_RAW=${BQ_DATASET_RAW:-mergemind_raw}
BQ_DATASET_MODELED=${BQ_DATASET_MODELED:-mergemind}
VERTEX_LOCATION=${VERTEX_LOCATION:-us-central1}

# GitLab Configuration
GITLAB_BASE_URL=${GITLAB_BASE_URL}
GITLAB_TOKEN=${GITLAB_TOKEN}

# Monitoring Configuration
PROMETHEUS_RETENTION=${PROMETHEUS_RETENTION:-30d}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
EOF

echo "✅ Environment file created."

# Build custom exporters
echo "🔨 Building custom exporters..."
docker-compose build

# Start monitoring stack
echo "🚀 Starting monitoring stack..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus health check failed"
fi

# Check Alertmanager
if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager health check failed"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana health check failed"
fi

# Check custom exporters
for exporter in bigquery-exporter gitlab-exporter vertex-ai-exporter; do
    if curl -f http://localhost:8081/health > /dev/null 2>&1; then
        echo "✅ $exporter is healthy"
    else
        echo "❌ $exporter health check failed"
    fi
done

echo ""
echo "🎉 Monitoring stack setup complete!"
echo ""
echo "📊 Access URLs:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Alertmanager: http://localhost:9093"
echo ""
echo "🔧 Custom Exporters:"
echo "   BigQuery: http://localhost:8081"
echo "   GitLab: http://localhost:8082"
echo "   Vertex AI: http://localhost:8083"
echo ""
echo "📈 Next steps:"
echo "   1. Import dashboards in Grafana"
echo "   2. Configure alert notifications"
echo "   3. Set up log aggregation"
echo "   4. Configure SLO monitoring"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop stack: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: docker-compose pull && docker-compose up -d"
