# Service configuration
SERVICE := nyc-mta-api

# Common targets
.PHONY: install dev run lint deploy

install:
	uv sync

dev:
	uv sync --all-extras

run:
	uv run uvicorn src.api:app --reload

lint:
	uv run ruff check --fix .

# Deploy to DigitalOcean App Platform
deploy:
	@echo "Deploying to DigitalOcean App Platform..."
	@if ! command -v doctl &> /dev/null; then \
		echo "Error: doctl CLI not found. Install from: https://docs.digitalocean.com/reference/doctl/how-to/install/"; \
		exit 1; \
	fi
	doctl apps create --spec .do/app.yaml
