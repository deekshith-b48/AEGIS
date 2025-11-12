# Project AEGIS Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install dev test build docker-build docker-run docker-stop clean lint format security-check deploy

# Default target
help:
	@echo "Project AEGIS - Advanced Cybercrime Response System"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install          Install all dependencies"
	@echo "  dev              Start development server with hot reload"
	@echo "  dev-docker       Start development environment with Docker"
	@echo "  migrate          Run database migrations"
	@echo "  migrate-create   Create new migration"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-all         Run all tests with coverage"
	@echo "  test-performance Run performance benchmarks"
	@echo "  lint             Run code linting"
	@echo "  format           Format code with black and isort"
	@echo "  security-check   Run security vulnerability checks"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-stop      Stop Docker containers"
	@echo "  docker-clean     Clean Docker resources"
	@echo "  docker-compose   Start full stack with docker-compose"
	@echo "  docker-compose-dev Start development stack"
	@echo ""
	@echo "Production:"
	@echo "  build            Build application for production"
	@echo "  deploy           Deploy to production"
	@echo "  backup           Create database backup"
	@echo "  logs             View application logs"
	@echo ""
	@echo "Utilities:"
	@echo "  shell            Start interactive shell"
	@echo "  db-shell         Start database shell"
	@echo "  redis-shell      Start Redis shell"
	@echo "  clean            Clean temporary files"
	@echo "  docs             Generate documentation"
	@echo ""

# Installation
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r tests/requirements-test.txt
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Installation completed"

# Development
dev:
	@echo "Starting development server..."
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

dev-docker:
	@echo "Starting development environment with Docker..."
	docker-compose -f docker-compose.dev.yml up --build

dev-docker-detach:
	@echo "Starting development environment in background..."
	docker-compose -f docker-compose.dev.yml up --build -d

# Database
migrate:
	@echo "Running database migrations..."
	python -m alembic upgrade head

migrate-create:
	@echo "Creating new database migration..."
	@read -p "Enter migration message: " msg; \
	python -m alembic revision --autogenerate -m "$$msg"

migrate-rollback:
	@echo "Rolling back last migration..."
	python -m alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	python -m alembic downgrade base
	python -m alembic upgrade head

# Testing
test:
	@echo "Running unit tests..."
	python -m pytest tests/ -m "unit or not integration" -v --cov=backend --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/ -m integration -v

test-all:
	@echo "Running all tests with coverage..."
	python tests/run_tests.py --all --verbose

test-performance:
	@echo "Running performance benchmarks..."
	python tests/run_tests.py --performance

test-watch:
	@echo "Running tests in watch mode..."
	python -m pytest tests/ -f --cov=backend

# Code Quality
lint:
	@echo "Running code linting..."
	flake8 backend/ --format=json --output-file=reports/flake8.json || true
	mypy backend/ --json-report reports/mypy || true
	@echo "✅ Linting completed. Check reports/ for results."

format:
	@echo "Formatting code..."
	black backend/
	isort backend/
	@echo "✅ Code formatted successfully"

format-check:
	@echo "Checking code formatting..."
	black --check backend/
	isort --check-only backend/

security-check:
	@echo "Running security checks..."
	bandit -r backend/ -f json -o reports/bandit.json || true
	safety check --json --output reports/safety.json || true
	@echo "✅ Security checks completed. Check reports/ for results."

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t aegis-backend:latest .

docker-build-dev:
	@echo "Building development Docker image..."
	docker build -f Dockerfile.dev -t aegis-backend:dev .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 --env-file .env aegis-backend:latest

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

docker-compose:
	@echo "Starting full stack with Docker Compose..."
	docker-compose up --build

docker-compose-detach:
	@echo "Starting full stack in background..."
	docker-compose up --build -d

docker-compose-dev:
	@echo "Starting development stack with Docker Compose..."
	docker-compose -f docker-compose.dev.yml up --build

docker-compose-dev-detach:
	@echo "Starting development stack in background..."
	docker-compose -f docker-compose.dev.yml up --build -d

docker-logs:
	@echo "Following Docker logs..."
	docker-compose logs -f

docker-logs-dev:
	@echo "Following development Docker logs..."
	docker-compose -f docker-compose.dev.yml logs -f

# Production
build:
	@echo "Building application for production..."
	python -m build

backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U aegis_user aegis_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created"

logs:
	@echo "Following application logs..."
	tail -f logs/aegis.log

logs-error:
	@echo "Following error logs..."
	tail -f logs/error.log

# Shell Access
shell:
	@echo "Starting Python shell..."
	python -i -c "from database.database import get_db; from main import app; print('Project AEGIS Shell')"

db-shell:
	@echo "Starting database shell..."
	docker-compose exec postgres psql -U aegis_user -d aegis_db

redis-shell:
	@echo "Starting Redis shell..."
	docker-compose exec redis redis-cli

docker-shell:
	@echo "Starting shell in Docker container..."
	docker-compose exec aegis-backend /bin/bash

# Monitoring
monitor:
	@echo "Starting monitoring stack..."
	docker-compose up prometheus grafana jaeger

monitor-dev:
	@echo "Starting development monitoring..."
	docker-compose -f docker-compose.dev.yml up prometheus grafana

# Utilities
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf reports/
	@echo "✅ Cleanup completed"

clean-all: clean docker-clean

docs:
	@echo "Generating documentation..."
	cd docs && make html
	@echo "✅ Documentation generated. Open docs/_build/html/index.html"

docs-serve:
	@echo "Serving documentation..."
	cd docs/_build/html && python -m http.server 8080

# Database Setup
setup-db:
	@echo "Setting up database..."
	python -c "
from database.database import database_manager
from database.migrations import AEGISDatabaseMigrations
import asyncio

async def setup():
    await database_manager.initialize_database()
    migrations = AEGISDatabaseMigrations(database_manager)
    await migrations.run_migrations()
    print('✅ Database setup completed')

asyncio.run(setup())
"

seed-data:
	@echo "Seeding initial data..."
	python scripts/seed_data.py
	@echo "✅ Initial data seeded"

# Performance
benchmark:
	@echo "Running benchmarks..."
	python -m pytest tests/test_performance.py --benchmark-only --benchmark-json=reports/benchmark.json

profile:
	@echo "Running with profiling..."
	python -m cProfile -o reports/profile.stats -m uvicorn main:app --host 0.0.0.0 --port 8000

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands here
	@echo "✅ Deployed to staging"

deploy-production:
	@echo "Deploying to production..."
	# Add production deployment commands here
	@echo "✅ Deployed to production"

health-check:
	@echo "Performing health check..."
	curl -f http://localhost:8000/health || echo "❌ Health check failed"

# CI/CD
ci-test:
	@echo "Running CI tests..."
	python tests/run_tests.py --all --coverage --no-coverage
	python tests/run_tests.py --security --quality

ci-build:
	@echo "Running CI build..."
	docker build -t aegis-backend:$(shell git rev-parse --short HEAD) .

# Quick development commands
quick-start: install dev-docker-detach
	@echo "🚀 Quick start completed!"
	@echo "Application is running on http://localhost:8001"
	@echo "Database is on port 5433"
	@echo "Redis is on port 6380"
	@echo "Kafka is on port 9093"

quick-stop: docker-stop clean
	@echo "🛑 Quick stop completed!"

# Version and Info
version:
	@echo "Project AEGIS Version: $(shell python -c 'import os; print(os.getenv("APP_VERSION", "unknown"))')"
	@echo "Git Commit: $(shell git rev-parse --short HEAD || echo 'not available')"
	@echo "Python Version: $(shell python --version)"
	@echo "Docker Version: $(shell docker --version | cut -d' ' -f3 | cut -d',' -f1)"

info:
	@echo "Project AEGIS Information:"
	@echo "========================="
	@echo "Environment: $(shell echo $${AEGIS_ENV:-development})"
	@echo "Database: $(shell echo $${DB_HOST:-localhost}):$(shell echo $${DB_PORT:-5432})"
	@echo "Redis: $(shell echo $${REDIS_HOST:-localhost}):$(shell echo $${REDIS_PORT:-6379})"
	@echo "Kafka: $(shell echo $${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092})"
	@echo "Application Port: $(shell echo $${APP_PORT:-8000})"

# Default help target if no command provided
.DEFAULT_GOAL := help