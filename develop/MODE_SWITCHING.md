# 🔄 Quick Reference: MOCK ↔ REAL Mode Switching

## 📊 At a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    MOCK vs REAL Comparison                      │
├──────────────────┬───────────────────┬──────────────────────────┤
│ Feature          │ MOCK Mode         │ REAL Mode                │
├──────────────────┼───────────────────┼──────────────────────────┤
│ Status           │ ✅ Working Now    │ 🔧 Configure first       │
│ LLM              │ P2/backend mock    │ Real Claude Sonnet 4.6   │
│ Trello           │ Mock-XXXXX cards   │ Real board + cards       │
│ Slack            │ Logs only          │ Real #incidents channel  │
│ Email            │ Logs only          │ Real SendGrid emails     │
│ Speed            │ ⚡ Instant         │ ⏱ ~2-3 secs per request │
│ Cost             │ $0                 │ $$$ (pay-per-use)        │
│ Credentials      │ None needed        │ 4 API keys required      │
└──────────────────┴───────────────────┴──────────────────────────┘
```

---

## ⚡ Quick Commands

### Via Makefile (Recommended)

```bash
# Switch to MOCK
make mode-mock

# Switch to REAL
make mode-real

# Check current mode
make mode-status

# Test MOCK
make test-mock

# Test REAL
make test-real

# View all commands
make help
```

### Via Script

```bash
# Interactive mode selection
./switch-mode.sh

# Direct commands
./switch-mode.sh mock
./switch-mode.sh real
./switch-mode.sh status
```

### Manual (Advanced)

```bash
# MOCK: Edit .env
MOCK_INTEGRATIONS=true
MOCK_EMAIL=true

# REAL: Edit .env
MOCK_INTEGRATIONS=false
MOCK_EMAIL=false

# Add real credentials and restart
docker compose restart backend
```

---

## 🧪 Test Scenarios

### Scenario 1: Development (MOCK Mode)

```bash
# 1. Ensure MOCK mode
make mode-status
# Output: Current Mode: MOCK (testing)

# 2. Start system
make dev
# Starts backend + frontend + logs

# 3. Test in another terminal
make test-mock
# Creates dummy incident, returns mock severity P2

# 4. Check frontend
open http://localhost:3000
# File test incident, see status update in real-time

# 5. Done! No credentials needed, instant feedback
```

### Scenario 2: Staging (REAL Mode with Test Keys)

```bash
# 1. Get test credentials
# - Anthropic: https://console.anthropic.com (free trial)
# - Trello: https://trello.com/app-key
# - Slack: https://api.slack.com/apps (create test workspace first)
# - SendGrid: https://sendgrid.com (free tier)

# 2. Switch to real mode
make mode-real
# Prompts you for each credential

# 3. Restart system
docker compose down && docker compose up --build

# 4. Test real integrations
make test-real
# Creates real card in Trello, message in Slack, email sent

# 5. Verify manually
# - Check Trello board
# - Check Slack #incidents
# - Check email inbox
```

### Scenario 3: Production (REAL Mode with Prod Keys)

```bash
# 1. Pre-requisites
# - Real Anthropic account with billing
# - Real Trello board set up
# - Real Slack workspace configured
# - Real SendGrid account with domain verification

# 2. Switch to real mode with production keys
./switch-mode.sh real
# Enter production API keys carefully

# 3. Deploy with safety
docker compose down
docker compose up --build
# Monitor logs: docker logs qa-multiagent-backend -f

# 4. Run comprehensive tests
make validate
make test-real

# 5. Optional: Set up monitoring/alerting
# Add custom webhooks, setup error tracking, etc.
```

---

## 🔐 Credential Management

### Safe Workflow

```
1. Create .env.example (safe defaults, mock values)
   └─ Commit to git ✓

2. Create .env (real credentials)
   └─ Add to .gitignore ✓
   └─ Never commit ✓

3. Create .env.real_backup (when switching to real)
   └─ Automatic backup ✓
   └─ Recover if needed ✓

4. For each change:
   - Backup current .env
   - Update values
   - Test changes
   - Commit .env.example if needed
```

### Backup & Restore

```bash
# Automatic: switch-mode.sh creates backups

# Manual backup
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)

# Restore from backup (if using switch-mode.sh)
./switch-mode.sh backup
# Restores latest .env.real_backup

# Manual restore
cp .env.backup_20260408_123456 .env
docker compose restart backend
```

---

## 📋 Configuration Files

### .env Structure

```env
# ════════════════════════════════════════════════════════════
# TOGGLE: Which mode are we in?
# ════════════════════════════════════════════════════════════

MOCK_INTEGRATIONS=true   # ← Set to false for REAL mode
MOCK_EMAIL=true          # ← Independent email toggle

# ════════════════════════════════════════════════════════════
# LLM (Anthropic Claude)
# ════════════════════════════════════════════════════════════

ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE

# ════════════════════════════════════════════════════════════
# TICKETING (Trello)
# ════════════════════════════════════════════════════════════

TRELLO_API_KEY=your_key_here
TRELLO_API_TOKEN=your_token_here
TRELLO_BOARD_ID=your_board_id
TRELLO_LIST_ID=your_todo_list_id
TRELLO_DONE_LIST_ID=your_done_list_id

# ════════════════════════════════════════════════════════════
# NOTIFICATIONS (Slack)
# ════════════════════════════════════════════════════════════

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# ════════════════════════════════════════════════════════════
# EMAIL (SendGrid)
# ════════════════════════════════════════════════════════════

SENDGRID_API_KEY=SG.YOUR_KEY_HERE
REPORTER_EMAIL_FROM=sre-agent@company.com
```

### .gitignore (Protect Secrets)

```gitignore
# Credentials - NEVER commit
.env
.env.*.backup
.env.real_backup

# Build/runtime artifacts
data/
logs/
uploads/
.venv/
node_modules/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## ✅ Pre-Flight Checklist

### Before Testing with MOCK

- [ ] `MOCK_INTEGRATIONS=true` in .env
- [ ] `docker compose up --build` ran successfully
- [ ] Backend running: `curl http://localhost:8000/api/health`
- [ ] Mock mode confirmed: `curl http://localhost:8000/api/health | jq '.mock_mode'` → `true`

### Before Testing with REAL

- [ ] All 4 API keys obtained and valid
- [ ] `MOCK_INTEGRATIONS=false` in .env
- [ ] `MOCK_EMAIL=false` in .env
- [ ] Credentials NOT committed to git
- [ ] `.env` in `.gitignore`
- [ ] Real mode confirmed: `curl http://localhost:8000/api/health | jq '.mock_mode'` → `false`
- [ ] Trello board exists and is accessible
- [ ] Slack webhook configured and channel exists
- [ ] SendGrid account has verified sender domain

### Before Production Deploy

- [ ] Comprehensive E2E test passed
- [ ] All 5 agents confirmed working
- [ ] Logs reviewed for errors
- [ ] Database schema validated
- [ ] Monitoring/alerting in place
- [ ] Credentials rota policy defined
- [ ] Incident types documented
- [ ] Team trained on usage

---

## 🐛 Troubleshooting

| Issue | MOCK Mode | REAL Mode |
|-------|-----------|-----------|
| LLM fails | Check `MOCK_INTEGRATIONS=true` | Check API key is valid + has balance |
| Trello fails | Should not happen | Check API key, token, board ID, list IDs |
| Slack fails | Check logs | Check webhook URL, channel permissions |
| Email fails | Should log | Check API key, sender address verified |
| Configs not applied | Restart backend | `docker compose down && up` |

**Debug Command:**

```bash
# View current env in container
docker exec qa-multiagent-backend cat /app/.env | grep MOCK_INTEGRATIONS

# View logs with filtering
docker logs qa-multiagent-backend -f | grep -E "(ERROR|MOCK|Calling|Slack|Trello|Email)"

# Test endpoint directly
curl http://localhost:8000/api/health | jq .
```

---

## 📚 Full Documentation

For detailed setup, architecture, and deployment guides:

- **Credentials Guide**: `CREDENTIALS_GUIDE.md`
- **Setup Guide**: `SETUP_LOCAL.md`
- **Architecture**: `docs/architecture/`
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## 🚀 Quick Start (Copy-Paste)

### Fresh Start with MOCK

```bash
cd /Users/lilianestefaniamaradiagocorrea/Desktop/Hackathons/qa-multiagent

# Setup
make setup

# Start (includes build + logs)
make dev

# In another terminal:
make test-mock

# View frontend
make docs-open  # Opens API docs
# Or manually: http://localhost:3000
```

### Switch to REAL

```bash
# 1. Interactive mode switcher
make mode-real

# 2. Restart system
docker compose down && docker compose up --build

# 3. Test real integrations
make test-real

# 4. Verify manually
# - Check Trello board for new card
# - Check Slack #incidents channel
# - Check email inbox
```

---

**Last Updated**: 2026-04-08  
**Status**: ✅ Ready for both MOCK and REAL testing  
**Tested by**: AgentX Hackathon Team
