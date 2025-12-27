# Service configuration
SERVICE := nyc-mta-api
PROJECT := nm-data-475018
REGION := us-central1
BUILDPLAT := linux/amd64

# Derived values
IMAGE := $(REGION)-docker.pkg.dev/$(PROJECT)/cloud-run-source-deploy/$(SERVICE):latest

# Common targets
.PHONY: install dev run lint build-gc deploy-gc deploy-do

install:
	uv sync

dev:
	uv sync --all-extras

run:
	uv run uvicorn api:app --reload

lint:
	uv run ruff check --fix .

# Build and push Docker image
build-gc:
	@gcloud services enable run.googleapis.com artifactregistry.googleapis.com
	@gcloud auth configure-docker $(REGION)-docker.pkg.dev
	@echo "Building $(SERVICE)..."
	docker buildx build --platform $(BUILDPLAT) -t $(IMAGE) --push -f Dockerfile .

# Deploy to GCP Cloud Run
deploy-gc:
	gcloud run deploy $(SERVICE) \
		--project $(PROJECT) \
		--image $(IMAGE) \
		--region $(REGION) \
		--platform managed \
		--execution-environment gen2 \
		--allow-unauthenticated \
		--cpu 1 \
		--memory 256Mi \
		--min-instances 0 \
		--max-instances 1

# Deploy to DigitalOcean App Platform
deploy-do:
	@echo "Deploying to DigitalOcean App Platform..."
	@if ! command -v doctl &> /dev/null; then \
		echo "Error: doctl CLI not found. Install from: https://docs.digitalocean.com/reference/doctl/how-to/install/"; \
		exit 1; \
	fi
	doctl apps create --spec .do/app.yaml
