# Missions — Persistent AI Agent Management

> **Status:** Phase 1 Complete (Foundation)
> **Type:** Custom homelab application

---

## Overview

Missions is a persistent AI agent management system. Create goal-oriented tasks ("Missions") with evolving context that AI agents work on over time. Unlike stateless chat interfaces, Missions maintains persistent context (files, chat history, goals) and can proactively check for updates and notify users.

### Example Use Case

**Mission:** Car Manager
**Category:** Home
**Description:** I have a blue Citroen Picasso diesel from 2014. My family car for daily use. I manage road tax, insurance, maintenance, NCT.
**Goals:** Advise on all aspects of car ownership, remind about deadlines, research issues.
**Context Files:** Insurance PDF, NCT certificate photo, service history
**Agent Actions:**
- Answers questions using uploaded documents
- Searches web for 2014 Citroen Picasso maintenance tips
- Sends Ntfy notification 30 days before NCT expiry
- Logs all interactions for review

---

## Quick Reference

| Item | Value |
|------|-------|
| Frontend | React + TypeScript (Vite) |
| Backend | Python FastAPI |
| Database | Shared PostgreSQL |
| LLM Providers | Claude, OpenAI (Phase 2) |
| Hostname | `missions.home` |
| Auth | Authentik (all authenticated users) |

---

## Commands

```bash
# Start (development mode)
docker compose -f apps/missions/compose.yml up -d

# Stop
docker compose -f apps/missions/compose.yml down

# Logs
docker compose -f apps/missions/compose.yml logs -f

# Restart
docker compose -f apps/missions/compose.yml restart

# Database migrations
docker exec missions-backend alembic upgrade head

# Reset database (WARNING: deletes all data)
docker exec missions-backend alembic downgrade base
docker exec missions-backend alembic upgrade head
```

---

## First-Run Setup

### Step 1: Copy Environment File

```bash
cd apps/missions
cp .env.example .env
```

### Step 2: Generate Encryption Key

```bash
# Generate a secure encryption key for API keys
openssl rand -base64 32
```

Edit `.env` and set:
```bash
ENCRYPTION_KEY=<paste-generated-key-here>
POSTGRES_PASSWORD=<your-postgres-password>
```

### Step 3: Start Services

```bash
docker compose up -d
```

The backend will automatically run database migrations on startup.

### Step 4: Access Web UI

Visit http://missions.home

- Requires Authentik login
- All authenticated users can create missions

---

## Phase Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Foundation: mission CRUD, file upload, basic UI scaffold |
| **Phase 2** | 🔨 Next | Chat interface with streaming, LLM provider integration |
| **Phase 3** | 📝 Planned | Agent tools: web search, document parsing, code execution |
| **Phase 4** | 📝 Planned | Scheduling, Ntfy notifications, proactive checks |
| **Phase 5** | 📝 Planned | MCP server for external agent access |
| **Phase 6** | 📝 Planned | Polish: categories, export, cost dashboard |

---

## Phase 1 Capabilities

### Backend

- ✅ Mission CRUD API (create, read, update, delete)
- ✅ File upload/download API
- ✅ PostgreSQL schema and migrations
- ✅ Health check endpoint
- ✅ Database models for missions, files, messages, providers, categories

### Frontend

- ✅ React + TypeScript scaffold
- ✅ Routing (Dashboard, Mission Detail, Create, Settings)
- ✅ Type definitions
- ⚠️ UI components (placeholders - need implementation)

### Integration

- ✅ Authentik forward-auth
- ✅ Homepage link
- ✅ Shared PostgreSQL database
- ✅ Docker Compose for development

### Not Yet Implemented (Future Phases)

- ❌ Chat interface (Phase 2)
- ❌ LLM integration (Phase 2)
- ❌ Agent tools (Phase 3)
- ❌ Scheduling (Phase 4)
- ❌ Notifications (Phase 4)
- ❌ MCP server (Phase 5)

---

## Development

### Backend Development

```bash
cd apps/missions/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd apps/missions/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Access at http://localhost:5173

### Database Migrations

```bash
# Create new migration
cd apps/missions/backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/missions` | List missions |
| `POST` | `/api/missions` | Create mission |
| `GET` | `/api/missions/{id}` | Get mission |
| `PUT` | `/api/missions/{id}` | Update mission |
| `DELETE` | `/api/missions/{id}` | Delete mission |
| `POST` | `/api/missions/{id}/files` | Upload file |
| `GET` | `/api/missions/{id}/files` | List files |
| `GET` | `/api/missions/{id}/files/{file_id}` | Download file |
| `DELETE` | `/api/missions/{id}/files/{file_id}` | Delete file |

---

## Database Schema

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for complete schema documentation.

**Tables:**
- `categories` — Mission categories (Home, Work, Financial, etc.)
- `llm_providers` — LLM provider configurations (Claude, OpenAI)
- `missions` — Core missions table
- `mission_files` — Uploaded files/context
- `messages` — Conversation history

---

## File Storage

Files are stored in `./data/files/{mission-id}/` organized by mission.

```
data/files/
└── {mission-uuid}/
    ├── {file-uuid}.pdf
    ├── {file-uuid}.jpg
    └── {file-uuid}.png
```

---

## Environment Variables

See [.env.example](.env.example) for all configuration options.

**Required:**
- `DATABASE_URL` — PostgreSQL connection
- `ENCRYPTION_KEY` — For encrypting LLM API keys
- `POSTGRES_PASSWORD` — Database password

**Optional:**
- `NTFY_URL` — Ntfy server (Phase 4)
- `TAVILY_API_KEY` — Web search (Phase 3)
- `DEBUG` — Enable debug mode

---

## Backup

### What to Backup

- PostgreSQL database (missions, messages, settings)
- `./data/files/` directory (uploaded documents)

### Backup Command

```bash
scripts/backup-all --service missions
```

### Restore

```bash
scripts/dr-restore --service missions
```

---

## Security

- **API Keys:** Encrypted at rest using Fernet (ENCRYPTION_KEY)
- **Authentication:** Authentik forward-auth (all authenticated users)
- **File Upload:** Stored with unique UUIDs, original names preserved
- **Code Execution:** Sandboxed Docker containers (Phase 3)

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose -f apps/missions/compose.yml logs backend

# Common issues:
# 1. Database migration failed
docker exec missions-backend alembic upgrade head

# 2. Database connection failed
# Check POSTGRES_PASSWORD in .env matches platform/postgres/.env
```

### Frontend won't build

```bash
# Reinstall dependencies
cd apps/missions/frontend
rm -rf node_modules package-lock.json
npm install
```

### Can't access missions.home

1. Check Caddy is routing correctly:
   ```bash
   docker exec caddy curl -s http://missions-frontend:5173
   ```

2. Check Authentik is running:
   ```bash
   docker ps | grep authentik
   ```

3. Try accessing directly via IP:
   ```
   http://<mac-mini-ip>:5173
   ```

---

## Next Steps: Phase 2

To continue development, see [IMPLEMENTATION.md](IMPLEMENTATION.md) Phase 2 tasks:

- [ ] WebSocket endpoint for streaming chat
- [ ] Anthropic Claude SDK integration
- [ ] OpenAI SDK integration
- [ ] API key encryption/decryption
- [ ] Chat UI component with streaming
- [ ] Message persistence
- [ ] Token counting and cost tracking

---

## Upstream

This is a custom homelab application developed specifically for this platform.

**Related:**
- Implementation plan: [IMPLEMENTATION.md](IMPLEMENTATION.MD)
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- OpenAI SDK: https://github.com/openai/openai-python
