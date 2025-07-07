.PHONY: help setup up down logs worker clean start-example deploy-dmn debug-bridge-build

help:
	@echo "TraceRail Bootstrap - Application Stack Commands"
	@echo "================================================"
	@echo ""
	@echo "Setup & Verification:"
	@echo "  setup           Run interactive environment setup to create .env file"
	@echo ""
	@echo "Application Lifecycle:"
	@echo "  up             Start all Docker services (Temporal, Grafana, etc.)"
	@echo "  down           Stop all Docker services"
	@echo "  logs           Follow logs from all Docker services"
	@echo "  worker         Start the Temporal worker process"
	@echo "  clean          Stop services and remove Docker volumes"
	@echo ""
	@echo "Workflow Interaction:"
	@echo "  start-example  Run a sample workflow with a test message"
	@echo "  deploy-dmn     Deploy DMN files from the /dmn directory to Flowable"
	@echo ""
	@echo "Debugging:"
	@echo "  debug-bridge-build  Run a verbose, no-cache build for the bridge service"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup     # Run interactive setup"
	@echo "  make up        # Start services"
	@echo "  make worker    # Start worker (in another terminal)"
	@echo ""
	@echo "Web Interfaces:"
	@echo "  Temporal UI:   http://localhost:8233"
	@echo "  Flowable DMN:  http://localhost:8082/flowable-rest/docs/"
	@echo "  Task Bridge:   http://localhost:7070/docs"
	@echo "  Grafana:       http://localhost:3000"
	@echo ""

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

worker:
	poetry run python workers/worker.py

clean:
	docker compose down -v --remove-orphans

setup:
	./bin/setup-env.sh

start-example:
	poetry run python cli/start_example.py "This is an example workflow run from the Makefile"

deploy-dmn:
	poetry run python bin/deploy-dmn.py

debug-bridge-build:
	@echo "🛠️  Debugging the bridge service build..."
	@echo "Stopping and removing any old bridge containers..."
	@docker compose rm -s -f bridge || true
	@echo "Building bridge service with verbose output (this may take a moment)..."
	@docker compose build --no-cache --progress=plain bridge
