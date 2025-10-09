# GitLab Fivetran Connector Makefile

.PHONY: help install test build deploy clean lint format

# Default target
help:
	@echo "GitLab Fivetran Connector Commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  build       - Build Docker image"
	@echo "  deploy      - Deploy to Cloud Run"
	@echo "  clean       - Clean up build artifacts"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v
	python test_connector.py

# Build Docker image
build:
	docker build -t gitlab-connector:latest .

# Deploy to Cloud Run
deploy:
	bash deploy.sh

# Clean up
clean:
	docker system prune -f
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf logs/

# Lint code
lint:
	python -m flake8 .
	python -m mypy .

# Format code
format:
	python -m black .
	python -m isort .

# Run connector locally
run:
	python connector.py

# Run health check
health:
	python health.py

# Test with sample data
test-sample:
	python -c "from connector import GitLabConnector; c = GitLabConnector(); print(list(c.read('merge_requests'))[:1])"
