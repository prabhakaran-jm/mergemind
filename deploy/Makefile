# MergeMind Makefile
# Provides convenient targets for development and deployment

.PHONY: help dev.api dev.ui dbt.run dbt.test seed deploy.api deploy.bot clean

# Default target
help:
	@echo "MergeMind Development Commands:"
	@echo "  dev.api     - Run FastAPI development server"
	@echo "  dev.ui      - Run UI development server"
	@echo "  dbt.run     - Run dbt models"
	@echo "  dbt.test    - Test dbt models"
	@echo "  seed        - Seed demo data"
	@echo "  deploy.api  - Deploy API to Cloud Run"
	@echo "  clean       - Clean build artifacts"

# Development targets
dev.api:
	@echo "Starting FastAPI development server..."
	cd app/backend/fastapi_app && python main.py

dev.ui:
	@echo "Starting UI development server..."
	cd app/frontend/web && npm run dev

# dbt targets
dbt.deps:
	@echo "Installing dbt packages..."
	cd warehouse/bigquery/dbt && dbt deps

dbt.run:
	@echo "Running dbt models..."
	cd warehouse/bigquery/dbt && dbt run

dbt.test:
	@echo "Testing dbt models..."
	cd warehouse/bigquery/dbt && dbt test

dbt.compile:
	@echo "Compiling dbt models..."
	cd warehouse/bigquery/dbt && dbt compile

dbt.ls:
	@echo "Listing dbt models..."
	cd warehouse/bigquery/dbt && dbt ls

# Data seeding
seed:
	@echo "Seeding demo data..."
	bash deploy/scripts/seed_demo.sh

# Deployment targets
deploy.api:
	@echo "Deploying API to Cloud Run..."
	bash deploy/scripts/deploy_api.sh


deploy.ui:
	@echo "Deploying UI to Cloud Run..."
	bash deploy/scripts/deploy_ui.sh

deploy.all:
	@echo "Deploying all services to Cloud Run..."
	bash deploy/scripts/deploy_api.sh
	bash deploy/scripts/deploy_ui.sh

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
