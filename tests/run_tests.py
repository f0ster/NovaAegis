#!/usr/bin/env python3
"""
Test runner with database and Docker management.
Ensures clean test environment and proper resource cleanup.
"""
import os
import sys
import asyncio
import argparse
import subprocess
from pathlib import Path
import docker
import psycopg2
import pytest
import structlog
from nova_aegis import __version__

logger = structlog.get_logger()

class TestEnvironment:
    """Manages test environment setup and teardown."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.test_db_name = "test_db"
        self.container_name = "tenx_test_postgres"
        self.container = None
        
    def setup(self):
        """Set up test environment."""
        logger.info("setting_up_test_environment")
        
        try:
            # Start PostgreSQL container
            self.start_postgres()
            
            # Wait for database to be ready
            self.wait_for_postgres()
            
            # Create test database
            self.create_test_db()
            
            logger.info("test_environment_ready")
            return True
            
        except Exception as e:
            logger.error("setup_failed", error=str(e))
            self.teardown()
            return False
    
    def teardown(self):
        """Clean up test environment."""
        logger.info("cleaning_up_test_environment")
        
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                logger.info("postgres_container_removed")
            except Exception as e:
                logger.error("container_cleanup_failed", error=str(e))
    
    def start_postgres(self):
        """Start PostgreSQL container."""
        logger.info("starting_postgres_container")
        
        # Remove existing container if any
        try:
            existing = self.docker_client.containers.get(self.container_name)
            existing.stop()
            existing.remove()
        except docker.errors.NotFound:
            pass
        
        # Start new container
        self.container = self.docker_client.containers.run(
            "postgres:15-alpine",
            name=self.container_name,
            environment={
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "postgres",
                "POSTGRES_DB": "postgres"
            },
            ports={'5432/tcp': 5432},
            detach=True,
            remove=True
        )
        
        logger.info("postgres_container_started", id=self.container.id[:12])
    
    def wait_for_postgres(self, max_attempts: int = 30):
        """Wait for PostgreSQL to be ready."""
        logger.info("waiting_for_postgres")
        
        for i in range(max_attempts):
            try:
                conn = psycopg2.connect(
                    dbname="postgres",
                    user="postgres",
                    password="postgres",
                    host="localhost",
                    port=5432
                )
                conn.close()
                logger.info("postgres_ready")
                return
            except psycopg2.OperationalError:
                if i == max_attempts - 1:
                    raise
                asyncio.sleep(1)
    
    def create_test_db(self):
        """Create test database."""
        logger.info("creating_test_database")
        
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Drop test database if it exists
            cur.execute(f"DROP DATABASE IF EXISTS {self.test_db_name}")
            # Create fresh test database
            cur.execute(f"CREATE DATABASE {self.test_db_name}")
        
        conn.close()
        logger.info("test_database_created")

def run_tests(args):
    """Run pytest with provided arguments."""
    logger.info("running_tests", args=args)
    
    # Set test database URL
    os.environ["TEST_DATABASE_URL"] = (
        "postgresql://postgres:postgres@localhost:5432/test_db"
    )
    
    # Construct pytest arguments
    pytest_args = [
        "-v",
        "--asyncio-mode=auto",
        f"--cov={args.cov_package}" if args.cov_package else "",
        "--cov-report=term-missing" if args.cov_package else "",
        "-n", str(args.workers) if args.workers > 1 else "0"
    ]
    
    if args.test_path:
        pytest_args.append(args.test_path)
    else:
        pytest_args.append("tests/")
    
    # Run tests
    return pytest.main(pytest_args)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=f"TenX Reactive Research Test Runner v{__version__}"
    )
    parser.add_argument(
        "--test-path",
        help="Specific test path to run"
    )
    parser.add_argument(
        "--cov-package",
        default="nova_aegis",
        help="Package to measure coverage for"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes"
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database setup (use existing)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    # Set up test environment
    env = TestEnvironment()
    if not args.skip_db:
        if not env.setup():
            sys.exit(1)
    
    try:
        # Run tests
        result = run_tests(args)
        sys.exit(result)
    finally:
        # Clean up
        if not args.skip_db:
            env.teardown()

if __name__ == "__main__":
    main()