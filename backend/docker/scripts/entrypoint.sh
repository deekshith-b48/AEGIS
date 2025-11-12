#!/bin/bash
# Project AEGIS Docker Entrypoint Script
# Handles initialization, health checks, and service startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] AEGIS:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] AEGIS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] AEGIS:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] AEGIS:${NC} $1"
}

# Function to check if environment variables are set
check_env_vars() {
    log "Checking environment variables..."

    required_vars=(
        "DB_HOST"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi

    log_success "All required environment variables are set"
}

# Function to wait for database
wait_for_database() {
    log "Waiting for database to be ready..."

    ./wait-for-it.sh "${DB_HOST}:${DB_PORT}" -t 60 -s -- echo "Database is ready"

    # Additional check to ensure database is accepting connections
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
        log_warning "Database is not ready yet, waiting..."
        sleep 2
    done

    log_success "Database is ready and accepting connections"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."

    # Check if we need to initialize migrations
    if ! python -c "from database.database import Base; from sqlalchemy import create_engine; engine=create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'); Base.metadata.create_all(engine)" 2>/dev/null; then
        log_warning "Database tables might not exist, running Alembic migrations..."

        # Run Alembic migrations
        python -m alembic upgrade head

        if [[ $? -eq 0 ]]; then
            log_success "Database migrations completed successfully"
        else
            log_error "Database migrations failed"
            exit 1
        fi
    else
        log_success "Database tables already exist"
    fi
}

# Function to create initial data
create_initial_data() {
    log "Creating initial data..."

    # Create admin user if it doesn't exist
    python -c "
from database.database import get_db
from database.models import User, UserRole
from auth.auth_service import auth_service
import os

# Get database session
db = next(get_db())

# Check if admin user exists
admin_user = db.query(User).filter(User.email == 'admin@aegis.gov.in').first()

if not admin_user:
    # Create admin user
    admin_user = User(
        user_id='admin_001',
        email='admin@aegis.gov.in',
        name='System Administrator',
        password=auth_service.hash_password('admin123'),
        role=UserRole.SYSTEM,
        department='IT',
        is_active=True
    )

    db.add(admin_user)
    db.commit()

    print('✅ Admin user created: admin@aegis.gov.in / admin123')
else:
    print('✅ Admin user already exists')

db.close()
"

    log_success "Initial data creation completed"
}

# Function to setup directories
setup_directories() {
    log "Setting up directories..."

    directories=(
        "/app/logs"
        "/app/uploads"
        "/app/uploads/complaints"
        "/app/uploads/evidence"
        "/app/uploads/reports"
        "/app/static"
        "/app/temp"
        "/app/models"
        "/app/models/ai"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done

    # Set proper permissions
    chown -R aegis:aegis /app
    chmod -R 755 /app/uploads
    chmod -R 755 /app/static

    log_success "Directory setup completed"
}

# Function to start Redis if needed (for development)
start_redis() {
    if [[ "$AEGIS_ENV" == "development" ]] && [[ -z "${REDIS_HOST}" ]]; then
        log "Starting Redis for development..."
        redis-server --daemonize yes --appendonly yes
        log_success "Redis started for development"
    fi
}

# Function to perform health check
health_check() {
    log "Performing initial health check..."

    # Check application health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Application health check passed"
    else
        log_warning "Application health check failed (this might be normal during startup)"
    fi
}

# Function to start the application
start_application() {
    log "Starting Project AEGIS application..."

    # Set default values if not provided
    export WORKERS=${WORKERS:-4}
    export MAX_REQUESTS=${MAX_REQUESTS:-1000}
    export MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}
    export WORKER_TIMEOUT=${WORKER_TIMEOUT:-120}
    export WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}

    log "Configuration:"
    log "  Environment: $AEGIS_ENV"
    log "  Workers: $WORKERS"
    log "  Max Requests: $MAX_REQUESTS"
    log "  Worker Timeout: $WORKER_TIMEOUT seconds"
    log "  Log Level: $LOG_LEVEL"

    # Start the application using uWSGI for production
    if [[ "$AEGIS_ENV" == "production" ]]; then
        log "Starting with uWSGI (production mode)..."
        exec uwsgi --ini uwsgi.ini
    else
        log "Starting with Uvicorn (development mode)..."
        exec python -m uvicorn main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --max-requests $MAX_REQUESTS \
            --max-requests-jitter $MAX_REQUESTS_JITTER \
            --timeout $WORKER_TIMEOUT \
            --access-log \
            --log-level ${LOG_LEVEL:-info}
    fi
}

# Function to handle graceful shutdown
cleanup() {
    log "Received shutdown signal, performing graceful shutdown..."

    # Send SIGTERM to application process
    if [[ -n "$APP_PID" ]]; then
        kill -TERM "$APP_PID"
        wait "$APP_PID"
    fi

    log "Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution flow
main() {
    log "🚀 Starting Project AEGIS Docker Container"
    log "Environment: $AEGIS_ENV"
    log "Python version: $(python --version)"
    log "Working directory: $(pwd)"

    # Check if running as root in production
    if [[ "$AEGIS_ENV" == "production" ]] && [[ "$(id -u)" == "0" ]]; then
        log_error "Running as root in production is not allowed"
        exit 1
    fi

    # Run initialization steps
    check_env_vars
    setup_directories
    wait_for_database
    run_migrations
    create_initial_data

    # Start additional services if needed
    start_redis

    # Perform initial health check
    health_check

    log_success "🎉 Project AEGIS is ready to serve!"

    # Start the application
    start_application &
    APP_PID=$!

    # Wait for the application to finish
    wait "$APP_PID"
}

# Execute main function
main "$@"