#!/bin/bash
# Test runner script with common configurations

# Exit on error
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
WORKERS=4
COVERAGE=1
SKIP_DB=0
TEST_PATH=""
WATCH=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cov)
            COVERAGE=0
            shift
            ;;
        --skip-db)
            SKIP_DB=1
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --watch)
            WATCH=1
            shift
            ;;
        --path)
            TEST_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Build test command
TEST_CMD="python tests/run_tests.py"

if [ $COVERAGE -eq 0 ]; then
    TEST_CMD="$TEST_CMD --cov-package=''"
fi

if [ $SKIP_DB -eq 1 ]; then
    TEST_CMD="$TEST_CMD --skip-db"
fi

TEST_CMD="$TEST_CMD --workers $WORKERS"

if [ ! -z "$TEST_PATH" ]; then
    TEST_CMD="$TEST_CMD --test-path $TEST_PATH"
fi

# Run tests
if [ $WATCH -eq 1 ]; then
    # Install ptw if not present
    pip show pytest-watch >/dev/null 2>&1 || pip install pytest-watch
    
    # Run with watch mode
    ptw --runner "$TEST_CMD"
else
    # Run tests directly
    $TEST_CMD
fi