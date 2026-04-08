.PHONY: help setup dev build start stop restart logs test-mock test-real mode-mock mode-real validate clean

# Color output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m

help: ## Show this help message
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo "$(BLUE) QA Multi-Agent SRE System$(NC)"
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup & Development:$(NC)"
	@echo "  make setup          - Initialize project (first time only)"
	@echo "  make dev            - Start development server"
	@echo "  make build          - Build Docker images"
	@echo ""
	@echo "$(YELLOW)Docker Management:$(NC)"
	@echo "  make start          - Start Docker containers"
	@echo "  make stop           - Stop containers"
	@echo "  make restart        - Restart containers"
	@echo "  make logs           - View backend logs (live)"
	@echo "  make clean          - Remove containers and volumes"
	@echo ""
	@echo "$(YELLOW)Mode Switching:$(NC)"
	@echo "  make mode-mock      - Switch to MOCK mode (testing)"
	@echo "  make mode-real      - Switch to REAL mode (production)"
	@echo "  make mode-status    - Show current mode"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  make test-mock      - Test with mock integrations"
	@echo "  make test-real      - Test with real integrations"
	@echo "  make validate       - Validate system health"
	@echo ""
	@echo "$(YELLOW)Endpoints:$(NC)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""

# ════════════════════════════════════════ SETUP ════════════════════════════════════════

setup: ## Initialize project (first time only)
	@echo "$(BLUE)Setting up project...$(NC)"
	@mkdir -p data logs uploads
	@cp .env.example .env || echo ".env already exists"
	@echo "$(GREEN)✅ Setup complete$(NC)"
	@echo "$(YELLOW)Next: make dev$(NC)"

# ════════════════════════════════════════ DOCKER ════════════════════════════════════════

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker compose build --no-cache
	@echo "$(GREEN)✅ Build complete$(NC)"

start: ## Start Docker containers
	@echo "$(BLUE)Starting containers...$(NC)"
	@docker compose up -d
	@echo "$(GREEN)✅ Containers started$(NC)"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@sleep 5
	@make validate

stop: ## Stop Docker containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	@docker compose stop
	@echo "$(GREEN)✅ Containers stopped$(NC)"

restart: ## Restart Docker containers
	@echo "$(BLUE)Restarting containers...$(NC)"
	@docker compose restart
	@sleep 3
	@echo "$(GREEN)✅ Containers restarted$(NC)"
	@make validate

logs: ## View backend logs (live)
	@docker logs qa-multiagent-backend -f --tail=50

clean: ## Remove all containers and volumes
	@echo "$(YELLOW)WARNING: This will remove all data!$(NC)"
	@read -p "Continue? (y/n) " -n1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "$(GREEN)✅ Cleaned$(NC)"; \
	fi

dev: build start logs ## Full development setup with live logs

# ════════════════════════════════════════ MODE SWITCHING ════════════════════════════════════════

mode-mock: ## Switch to MOCK mode (testing)
	@echo "$(BLUE)Switching to MOCK mode...$(NC)"
	@bash switch-mode.sh mock
	@echo "$(GREEN)✅ Mode switched to MOCK$(NC)"
	@echo ""
	@echo "Next: docker compose restart backend"

mode-real: ## Switch to REAL mode (production)
	@bash switch-mode.sh real

mode-status: ## Show current mode
	@bash switch-mode.sh status

# ════════════════════════════════════════ TESTING ════════════════════════════════════════

validate: ## Validate system health
	@echo "$(BLUE)Validating system...$(NC)"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:8000/api/health | jq '{status: .status, database: .database, mock_mode: .mock_mode}' || echo "$(RED)❌ Backend not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)Endpoints:$(NC)"
	@echo "  Frontend: http://localhost:3000 (open in browser)"
	@echo "  Backend:  http://localhost:8000/api/health"
	@echo "  Docs:     http://localhost:8000/docs"

test-mock: ## Test with mock integrations
	@echo "$(BLUE)Testing MOCK mode...$(NC)"
	@TRACE=$$(curl -s -X POST http://localhost:8000/api/incidents \
		-F "title=Mock Test $$(date +%s)" \
		-F "description=Testing mock integration" \
		-F "reporter_email=test@company.com" | jq -r '.trace_id'); \
	echo "Created incident: $$TRACE"; \
	sleep 5; \
	echo ""; \
	echo "$(YELLOW)Result:$(NC)"; \
	curl -s "http://localhost:8000/api/incidents/$$TRACE" | jq '{status: .status, severity: .severity, module: .affected_module, ticket: .ticket_id}'; \
	echo "$(GREEN)✅ Mock test complete$(NC)"

test-real: ## Test with real integrations
	@echo "$(BLUE)Testing REAL mode...$(NC)"
	@echo "$(YELLOW)Prerequisites:$(NC)"
	@echo "  • MOCK_INTEGRATIONS=false in .env"
	@echo "  • Valid API keys configured"
	@echo "  • Docker restarted after env changes"
	@echo ""
	@TRACE=$$(curl -s -X POST http://localhost:8000/api/incidents \
		-F "title=Real Integration Test $$(date +%s)" \
		-F "description=Testing real Trello, Slack, SendGrid" \
		-F "reporter_email=oncall@company.com" | jq -r '.trace_id'); \
	echo "Created incident: $$TRACE"; \
	sleep 8; \
	echo ""; \
	echo "$(YELLOW)Result:$(NC)"; \
	curl -s "http://localhost:8000/api/incidents/$$TRACE" | jq '{status: .status, severity: .severity, ticket_id: .ticket_id, ticket_url: .ticket_url}'; \
	echo ""; \
	echo "$(YELLOW)Verify Manually:$(NC)"; \
	echo "  ✓ Check Trello board for new card"; \
	echo "  ✓ Check #incidents Slack channel"; \
	echo "  ✓ Check email inbox"; \
	echo "$(GREEN)✅ Real test initiated$(NC)"

# ════════════════════════════════════════ DATABASE ════════════════════════════════════════

db-shell: ## Open SQLite database shell
	@sqlite3 data/incidents.db

db-incidents: ## Show all incidents
	@sqlite3 data/incidents.db "SELECT id, trace_id, title, status FROM incidents LIMIT 10;"

db-reset: ## Reset database (DESTRUCTIVE!)
	@echo "$(RED)WARNING: This will DELETE all incidents!$(NC)"
	@read -p "Type 'yes' to confirm: " -r; \
	if [ "$$REPLY" = "yes" ]; then \
		rm -f data/incidents.db*; \
		echo "$(GREEN)✅ Database reset$(NC)"; \
	fi

# ════════════════════════════════════════ DOCUMENTATION ════════════════════════════════════════

docs-open: ## Open API documentation
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs

credentials-guide: ## Show credentials guide
	@cat CREDENTIALS_GUIDE.md | head -50

# ════════════════════════════════════════ GIT ════════════════════════════════════════

git-status: ## Show git status
	@git status

git-commit: ## Commit current changes
	@git add -A && git commit -m "WIP: $(shell date)"

git-push: ## Push to remote
	@git push origin feature/implementation

git-pull: ## Pull latest changes
	@git pull origin feature/implementation

# Default
.DEFAULT_GOAL := help
