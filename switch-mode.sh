#!/bin/bash

# 🔐 Interactive Mode Switcher: MOCK ↔ REAL
# This script toggles between mock and real integrations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Helper functions
print_header() {
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

check_env() {
  if [ ! -f .env ]; then
    print_error ".env file not found"
    echo "Creating from .env.example..."
    cp .env.example .env
  fi
}

get_current_mode() {
  if grep -q "^MOCK_INTEGRATIONS=true" .env 2>/dev/null; then
    echo "mock"
  elif grep -q "^MOCK_INTEGRATIONS=false" .env 2>/dev/null; then
    echo "real"
  else
    echo "unknown"
  fi
}

show_current_status() {
  MODE=$(get_current_mode)
  echo ""
  if [ "$MODE" = "mock" ]; then
    print_success "Current Mode: MOCK (testing)"
    echo "  • No real API calls"
    echo "  • Mock LLM responses"
    echo "  • Instant feedback"
  elif [ "$MODE" = "real" ]; then
    print_warning "Current Mode: REAL (production)"
    echo "  • Real API calls to Trello, Slack, SendGrid"
    echo "  • Real Claude LLM"
    echo "  • Uses actual quotas"
  else
    print_error "Unknown mode"
  fi
  echo ""
}

switch_to_mock() {
  print_header "Switching to MOCK Mode"
  
  # Backup real .env if needed
  if [ -f .env ] && grep -q "^MOCK_INTEGRATIONS=false" .env 2>/dev/null; then
    cp .env .env.real_backup
    print_success "Backed up real credentials to .env.real_backup"
  fi
  
  # Apply mock settings
  sed -i '' 's/^MOCK_INTEGRATIONS=.*/MOCK_INTEGRATIONS=true/' .env
  sed -i '' 's/^MOCK_EMAIL=.*/MOCK_EMAIL=true/' .env
  
  print_success "Settings updated:"
  echo "  • MOCK_INTEGRATIONS=true"
  echo "  • MOCK_EMAIL=true"
  
  # Show next steps
  echo ""
  echo "Next steps:"
  echo "  1. Restart Docker: docker compose restart backend"
  echo "  2. Test: curl http://localhost:8000/api/health | jq '.mock_mode'"
  echo "  3. Create incident: curl -X POST http://localhost:8000/api/incidents ..."
}

switch_to_real() {
  print_header "Switching to REAL Mode"
  
  if [ ! -f .env.real_backup ]; then
    print_warning "No real credentials backup found. You'll need to enter them manually."
  fi
  
  # Disable mock
  sed -i '' 's/^MOCK_INTEGRATIONS=.*/MOCK_INTEGRATIONS=false/' .env
  sed -i '' 's/^MOCK_EMAIL=.*/MOCK_EMAIL=false/' .env
  
  print_success "Mock mode disabled. Now collecting credentials..."
  echo ""
  
  # LLM
  echo "═══════════════════════════════════════════"
  echo "1️⃣  ANTHROPIC (Claude LLM)"
  echo "═══════════════════════════════════════════"
  echo "Get key at: https://console.anthropic.com"
  read -p "Enter ANTHROPIC_API_KEY (or press Enter to keep existing): " ANTHROPIC
  if [ -n "$ANTHROPIC" ]; then
    sed -i '' "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC|" .env
  fi
  
  # Trello
  echo ""
  echo "═══════════════════════════════════════════"
  echo "2️⃣  TRELLO (Ticketing)"
  echo "═══════════════════════════════════════════"
  echo "Get keys at: https://trello.com/app-key"
  read -p "Enter TRELLO_API_KEY (or press Enter to skip): " TRELLO_KEY
  if [ -n "$TRELLO_KEY" ]; then
    sed -i '' "s|TRELLO_API_KEY=.*|TRELLO_API_KEY=$TRELLO_KEY|" .env
  fi
  
  read -p "Enter TRELLO_API_TOKEN (or press Enter to skip): " TRELLO_TOKEN
  if [ -n "$TRELLO_TOKEN" ]; then
    sed -i '' "s|TRELLO_API_TOKEN=.*|TRELLO_API_TOKEN=$TRELLO_TOKEN|" .env
  fi
  
  read -p "Enter TRELLO_BOARD_ID (or press Enter to skip): " TRELLO_BOARD
  if [ -n "$TRELLO_BOARD" ]; then
    sed -i '' "s|TRELLO_BOARD_ID=.*|TRELLO_BOARD_ID=$TRELLO_BOARD|" .env
  fi
  
  read -p "Enter TRELLO_LIST_ID (or press Enter to skip): " TRELLO_LIST
  if [ -n "$TRELLO_LIST" ]; then
    sed -i '' "s|TRELLO_LIST_ID=.*|TRELLO_LIST_ID=$TRELLO_LIST|" .env
  fi
  
  read -p "Enter TRELLO_DONE_LIST_ID (or press Enter to skip): " TRELLO_DONE
  if [ -n "$TRELLO_DONE" ]; then
    sed -i '' "s|TRELLO_DONE_LIST_ID=.*|TRELLO_DONE_LIST_ID=$TRELLO_DONE|" .env
  fi
  
  # Slack
  echo ""
  echo "═══════════════════════════════════════════"
  echo "3️⃣  SLACK (Notifications)"
  echo "═══════════════════════════════════════════"
  echo "Get webhook at: https://api.slack.com/apps"
  read -p "Enter SLACK_WEBHOOK_URL (or press Enter to skip): " SLACK
  if [ -n "$SLACK" ]; then
    sed -i '' "s|SLACK_WEBHOOK_URL=.*|SLACK_WEBHOOK_URL=$SLACK|" .env
  fi
  
  # SendGrid
  echo ""
  echo "═══════════════════════════════════════════"
  echo "4️⃣  SENDGRID (Email)"
  echo "═══════════════════════════════════════════"
  echo "Get key at: https://sendgrid.com"
  read -p "Enter SENDGRID_API_KEY (or press Enter to skip): " SENDGRID
  if [ -n "$SENDGRID" ]; then
    sed -i '' "s|SENDGRID_API_KEY=.*|SENDGRID_API_KEY=$SENDGRID|" .env
  fi
  
  read -p "Enter REPORTER_EMAIL_FROM (or press Enter to skip): " REPORTER_EMAIL
  if [ -n "$REPORTER_EMAIL" ]; then
    sed -i '' "s|REPORTER_EMAIL_FROM=.*|REPORTER_EMAIL_FROM=$REPORTER_EMAIL|" .env
  fi
  
  print_success "Credentials updated!"
  
  # Validate
  echo ""
  echo "Validating configuration..."
  if grep -q "^ANTHROPIC_API_KEY=sk-ant-" .env 2>/dev/null; then
    print_success "ANTHROPIC_API_KEY configured"
  else
    print_warning "ANTHROPIC_API_KEY not set"
  fi
  
  if grep -q "^SLACK_WEBHOOK_URL=https://" .env 2>/dev/null; then
    print_success "SLACK_WEBHOOK_URL configured"
  else
    print_warning "SLACK_WEBHOOK_URL not set"
  fi
  
  echo ""
  echo "Next steps:"
  echo "  1. Restart Docker: docker compose down && docker compose up --build"
  echo "  2. Test: curl http://localhost:8000/api/health | jq '.mock_mode'"
  echo "  3. Create incident: curl -X POST http://localhost:8000/api/incidents ..."
  echo "  4. Verify in real services (Trello, Slack, email)"
}

restore_from_backup() {
  if [ ! -f .env.real_backup ]; then
    print_error "No backup found (.env.real_backup)"
    exit 1
  fi
  
  print_header "Restoring Real Credentials"
  cp .env.real_backup .env
  print_success "Restored from .env.real_backup"
  echo ""
  echo "Next: docker compose restart backend"
}

show_menu() {
  echo ""
  show_current_status
  
  echo "What would you like to do?"
  echo ""
  echo "  1) Switch to MOCK mode (testing)"
  echo "  2) Switch to REAL mode (production)"
  echo "  3) Restore real credentials from backup"
  echo "  4) Show current configuration"
  echo "  5) Exit"
  echo ""
  read -p "Select option (1-5): " CHOICE
  
  case $CHOICE in
    1)
      switch_to_mock
      ;;
    2)
      switch_to_real
      ;;
    3)
      restore_from_backup
      ;;
    4)
      print_header "Current .env Configuration"
      grep -E "^(MOCK_|ANTHROPIC_|TRELLO_|SLACK_|SENDGRID_|REPORTER_)" .env | head -20
      ;;
    5)
      print_success "Goodbye!"
      exit 0
      ;;
    *)
      print_error "Invalid option"
      exit 1
      ;;
  esac
}

# Main
main() {
  print_header "🔐 Integration Mode Switcher"
  
  check_env
  
  if [ "$#" -eq 0 ]; then
    show_menu
  else
    case "$1" in
      mock)
        switch_to_mock
        ;;
      real)
        switch_to_real
        ;;
      status)
        show_current_status
        ;;
      backup)
        restore_from_backup
        ;;
      *)
        echo "Usage: $0 [mock|real|status|backup]"
        exit 1
        ;;
    esac
  fi
}

main "$@"
