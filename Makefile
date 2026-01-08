.PHONY: setup install lint format type-check test test-cov clean run-ingestion help

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
RESET := \033[0m

help: ## Show this help message
	@echo "Stranger Beers Monorepo"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"; } /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

setup: ## Initial project setup (install uv and dependencies)
	@echo "$(GREEN)Setting up Stranger Beers monorepo...$(RESET)"
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@uv sync --all-packages
	@echo "$(GREEN)Setup complete!$(RESET)"

install: ## Install all dependencies
	uv sync --all-packages

lint: ## Run linting (ruff)
	uv run ruff check apps packages

format: ## Format code (ruff format)
	uv run ruff format apps packages
	uv run ruff check --fix apps packages

type-check: ## Run type checking (mypy)
	uv run mypy apps packages

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=apps --cov=packages --cov-report=term-missing --cov-report=html

check: lint type-check test ## Run all checks (lint, type-check, test)

clean: ## Clean up build artifacts and caches
	@echo "$(GREEN)Cleaning up...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(RESET)"

# App runners
run-ingestion: ## Run the ingestion API locally
	uv run uvicorn apps.ingestion_api.src.main:app --reload --host 0.0.0.0 --port 8000

run-matching: ## Run the matching service
	@echo "Matching service not yet implemented"

run-comms: ## Run the communications service
	@echo "Communications service not yet implemented"

# Database commands (placeholders)
db-migrate: ## Create a new database migration
	@echo "Usage: make db-migrate message='migration description'"
	@echo "Not yet implemented"

db-upgrade: ## Apply database migrations
	@echo "Not yet implemented"

db-downgrade: ## Rollback database migration
	@echo "Not yet implemented"
