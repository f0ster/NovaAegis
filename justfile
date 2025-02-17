# Development workflow commands

# Install dependencies
setup:
    pipenv install --dev
    pipenv run playwright install
    docker-compose pull

# Start development environment
up:
    docker-compose up -d
    pipenv run alembic upgrade head
    pipenv run python -m nova_aegis.web.app

# Run tests
test:
    pipenv run pytest

# Run specific test
test-e2e:
    pipenv run pytest tests/e2e/test_exploration_companion.py -v

# Run browser automation test
test-browser:
    docker-compose up -d postgres redis
    pipenv run pytest tests/e2e/test_exploration_companion.py::test_exploration_companion_research_cycle -v

# Clean up
clean:
    docker-compose down -v
    rm -rf .pytest_cache
    rm -rf __pycache__
    rm -rf .coverage

# Format code
format:
    pipenv run black .
    pipenv run isort .

# Type check
typecheck:
    pipenv run mypy nova_aegis

# Lint
lint:
    pipenv run pylint nova_aegis

# Run complete test suite with coverage
test-coverage:
    pipenv run pytest --cov=nova_aegis --cov-report=html

# Run development server
dev:
    docker-compose up -d
    pipenv run uvicorn nova_aegis.web.app:app --reload

# Run demo
demo:
    docker-compose up -d
    pipenv run python examples/research_companion_demo.py

# Initialize database
init-db:
    docker-compose up -d postgres
    sleep 5
    pipenv run alembic upgrade head
    pipenv run python -m nova_aegis.seed

# Reset database
reset-db:
    docker-compose down -v postgres
    docker-compose up -d postgres
    sleep 10  # Increased wait time for postgres to start
    pipenv run alembic upgrade head
    pipenv run python -m nova_aegis.seed

# Show logs
logs:
    docker-compose logs -f

# Run complete setup and test
bootstrap: setup init-db test-e2e

# Launch dashboard in background and monitor
dashboard:
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Start required services
    docker-compose up -d postgres redis
    
    # Start dashboard in background, capturing output
    pipenv run python -m nova_aegis.web.app > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    
    # Wait for dashboard to start
    echo "Starting dashboard (PID: $DASHBOARD_PID)..."
    until grep -q "Running on local URL" logs/dashboard.log 2>/dev/null; do
        if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
            echo "Dashboard failed to start. Check logs/dashboard.log"
            exit 1
        fi
        sleep 0.1
    done
    
    # Show URL
    grep "Running on local URL" logs/dashboard.log
    
    # Monitor logs
    tail -f logs/dashboard.log

# Stop dashboard
dashboard-stop:
    #!/usr/bin/env bash
    pkill -f "python -m nova_aegis.web.app" || true