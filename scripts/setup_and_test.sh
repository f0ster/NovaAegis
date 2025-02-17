#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting NovaAegis setup and testing...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check Python version with pyenv
if ! command -v pyenv &> /dev/null; then
    echo -e "${RED}pyenv is required but not installed.${NC}"
    echo "Install pyenv first: https://github.com/pyenv/pyenv#installation"
    exit 1
fi

# Add local bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Ensure correct Python version
PYTHON_VERSION="3.9.0"
if ! pyenv versions | grep -q $PYTHON_VERSION; then
    echo -e "\n${GREEN}Installing Python $PYTHON_VERSION with pyenv...${NC}"
    pyenv install $PYTHON_VERSION
fi
pyenv local $PYTHON_VERSION

# Add pyenv to PATH and initialize
eval "$(pyenv init -)"
eval "$(pyenv init --path)"

# Install pipenv if needed
if ! command -v pipenv &> /dev/null; then
    echo -e "\n${GREEN}Installing pipenv...${NC}"
    python -m pip install --user pipenv
    # Reload PATH to include newly installed pipenv
    export PATH="$HOME/.local/bin:$PATH"
fi

# Ensure pipenv uses pyenv's Python
export PIPENV_PYTHON="$(pyenv which python)"

# Install dependencies with pipenv
echo -e "\n${GREEN}Installing dependencies...${NC}"
pipenv install --dev

# Start Docker services
echo -e "\n${GREEN}Starting Docker services...${NC}"
docker-compose down -v # Clean start
docker-compose up -d

# Wait for PostgreSQL
echo -e "\n${GREEN}Waiting for PostgreSQL...${NC}"
until docker-compose exec -T postgres pg_isready; do
    echo "Waiting for postgres..."
    sleep 2
done

# Run database migrations
echo -e "\n${GREEN}Running database migrations...${NC}"
pipenv run alembic upgrade head

# Run setup verification
echo -e "\n${GREEN}Running setup verification...${NC}"
pipenv run python scripts/test_setup.py

# Run E2E test
echo -e "\n${GREEN}Running E2E test...${NC}"
pipenv run pytest tests/e2e/test_exploration_companion.py -v

# Start NovaAegis
echo -e "\n${GREEN}Starting NovaAegis...${NC}"
pipenv run python -m nova_aegis.web.app &
APP_PID=$!

# Wait for app to start
echo "Waiting for app to start..."
sleep 5

# Run demo research workflow
echo -e "\n${GREEN}Running demo research workflow...${NC}"
pipenv run python examples/research_companion_demo.py

# Cleanup
echo -e "\n${GREEN}Cleaning up...${NC}"
kill $APP_PID
docker-compose down

echo -e "\n${GREEN}Setup and testing complete!${NC}"
echo -e "You can now start NovaAegis with: ${GREEN}pipenv run just up${NC}"

# Print helpful commands
echo -e "\nUseful commands:"
echo -e "${GREEN}pipenv run just up${NC}     - Start NovaAegis"
echo -e "${GREEN}pipenv run just test${NC}   - Run tests"
echo -e "${GREEN}pipenv run just demo${NC}   - Run demo"
echo -e "${GREEN}pipenv run just logs${NC}   - Show logs"