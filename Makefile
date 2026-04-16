.PHONY: setup install run dev lint format typecheck test help

PYTHON  ?= python
VENV    := .venv
UVICORN := uvicorn app.main:app

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Create venv + install deps + copy .env.example
	$(PYTHON) -m venv $(VENV)
	$(VENV)/Scripts/pip install --upgrade pip
	$(VENV)/Scripts/pip install -r requirements.txt
	@[ -f .env ] || cp .env.example .env && echo "Created .env — set your tokens!"

install:  ## Install dependencies into active venv
	pip install -r requirements.txt

install-dev:  ## Install dev dependencies
	pip install -r requirements-dev.txt

run:  ## Start server (production mode)
	$(UVICORN) --host 0.0.0.0 --port 8000

dev:  ## Start server with hot-reload
	$(UVICORN) --host 0.0.0.0 --port 8000 --reload --log-level debug

lint:  ## Run ruff linter
	ruff check app/

format:  ## Auto-format with ruff
	ruff format app/

typecheck:  ## Run mypy type checker
	mypy app/

test:  ## Run tests
	pytest tests/ -v
