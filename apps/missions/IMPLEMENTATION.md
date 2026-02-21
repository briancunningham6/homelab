# Missions — Implementation Plan

> **Status:** Planning
> **Type:** Custom homelab application
> **Author:** Homelab platform

---

## Overview

Missions is a persistent AI agent management system. Users create "Missions" — goal-oriented tasks with evolving context — that AI agents work on over time. Unlike stateless chat interfaces, Missions maintains persistent context (files, history, goals) and can proactively check for updates and notify users.

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│  Mission: "Car Manager"                                          │
│                                                                  │
│  Context:                                                        │
│  - Insurance PDF (parsed: renewal June 2026)                    │
│  - NCT certificate photo (parsed: expires Sept 2026)            │
│  - Service history document                                      │
│  - User notes and preferences                                    │
│                                                                  │
│  Goals:                                                          │
│  - Advise on all aspects of car ownership                       │
│  - Remind about upcoming deadlines                               │
│  - Research maintenance issues                                   │
│                                                                  │
│  Agent Actions:                                                   │
│  - Answers questions using context                               │
│  - Searches web for 2014 Citroen Picasso issues                 │
│  - Sends Ntfy notification 30 days before NCT                   │
│  - Logs all interactions for review                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Chat model** | Real-time streaming | Interactive feel, consistent with modern AI UIs |
| **Agent autonomy** | Make assumptions, report after | Faster progress, user reviews reasoning |
| **User model** | Single user | Simpler auth, aligns with homelab personal use |
| **Local LLM** | Not in MVP | Cloud APIs (Claude/OpenAI) sufficient initially |
| **Frontend** | React + TypeScript | Rich ecosystem, WebSocket support, type safety |
| **Notifications** | Ntfy (self-hosted) | Homelab-native, push to mobile |
| **Scheduling** | Configurable per mission | User controls check frequency |
| **Capabilities** | Full from start | Web search, doc parsing, APIs, code execution |
| **Database** | Shared PostgreSQL | Consistent with homelab, already backed up |
| **LLM providers** | Claude + OpenAI | Provider abstraction from day one |
| **History** | Full conversation stored | Complete audit trail, context replay |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React + TypeScript)                                    │
│  - Mission dashboard                                             │
│  - Mission detail with streaming chat                           │
│  - Settings (LLM providers, notifications)                      │
│  - File upload/management                                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket (streaming)
                           │ REST API (CRUD)
┌──────────────────────────▼──────────────────────────────────────┐
│  Backend (Python FastAPI)                                        │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  REST API       │  │  WebSocket      │  │  MCP Server     │  │
│  │  - Missions     │  │  - Chat stream  │  │  - External     │  │
│  │  - Files        │  │  - Events       │  │    agent access │  │
│  │  - Settings     │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Agent Orchestrator                                         ││
│  │  - Context assembly                                         ││
│  │  - Tool dispatch (search, code, APIs)                       ││
│  │  - Response streaming                                       ││
│  │  - Cost tracking                                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Scheduler (APScheduler / Celery Beat)                      ││
│  │  - Per-mission check intervals                              ││
│  │  - Deadline detection                                       ││
│  │  - Ntfy notifications                                       ││
│  └─────────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬────────────────┐
        │                  │                  │                │
        ▼                  ▼                  ▼                ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────┐
│  PostgreSQL   │  │  File Storage │  │  LLM APIs     │  │  Ntfy    │
│  (shared)     │  │  ./data/files │  │  - Anthropic  │  │  Server  │
│               │  │  /mission-id/ │  │  - OpenAI     │  │          │
└───────────────┘  └───────────────┘  └───────────────┘  └──────────┘
```

---

## Database Schema

```sql
-- LLM provider configurations
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,           -- "claude", "openai"
    display_name VARCHAR(100) NOT NULL,  -- "Anthropic Claude"
    api_key_encrypted TEXT,              -- encrypted API key
    default_model VARCHAR(100),          -- "claude-sonnet-4-20250514"
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mission categories
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,    -- "home", "work", "financial"
    display_name VARCHAR(100) NOT NULL,  -- "Home & Family"
    color VARCHAR(7),                    -- "#4A90D9"
    icon VARCHAR(50),                    -- "mdi-home"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Core missions table
CREATE TABLE missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category_id UUID REFERENCES categories(id),
    description TEXT NOT NULL,           -- problem context
    goals TEXT NOT NULL,                 -- desired outcomes

    -- Agent configuration
    llm_provider_id UUID REFERENCES llm_providers(id),
    model_override VARCHAR(100),         -- override default model
    autonomy_level VARCHAR(20) DEFAULT 'balanced',  -- for future use

    -- Scheduling
    check_interval VARCHAR(20) DEFAULT 'daily',  -- hourly, daily, weekly, manual
    last_checked_at TIMESTAMPTZ,
    next_check_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, archived

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mission files/context
CREATE TABLE mission_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    storage_path TEXT NOT NULL,          -- relative path in ./data/files/

    -- Parsed content (for search/context)
    extracted_text TEXT,                 -- OCR/PDF text extraction
    parsed_metadata JSONB,               -- structured data extracted by agent

    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL,           -- user, assistant, system, tool
    content TEXT NOT NULL,

    -- For tool calls
    tool_name VARCHAR(100),
    tool_input JSONB,
    tool_output JSONB,

    -- Token tracking
    input_tokens INTEGER,
    output_tokens INTEGER,

    -- Metadata
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled check logs
CREATE TABLE check_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,

    check_type VARCHAR(20) NOT NULL,     -- scheduled, manual, event
    status VARCHAR(20) NOT NULL,         -- completed, failed, skipped

    summary TEXT,                        -- what the agent found/did
    actions_taken JSONB,                 -- notifications sent, etc.

    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Notification history
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,

    channel VARCHAR(20) NOT NULL,        -- ntfy, email, homepage
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'default',

    sent_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_missions_status ON missions(status);
CREATE INDEX idx_missions_next_check ON missions(next_check_at) WHERE status = 'active';
CREATE INDEX idx_messages_mission ON messages(mission_id, created_at);
CREATE INDEX idx_files_mission ON mission_files(mission_id);
```

---

## Agent Tools

The agent has access to these tools, implemented as callable functions:

| Tool | Description | Implementation |
|------|-------------|----------------|
| `web_search` | Search the internet for information | Tavily API or SerpAPI |
| `fetch_url` | Retrieve and parse a web page | httpx + BeautifulSoup |
| `read_file` | Read content from mission file | Local filesystem |
| `parse_document` | Extract text/data from PDF/image | PyMuPDF + Claude Vision |
| `execute_code` | Run Python code in sandbox | Docker sandbox or Pyodide |
| `send_notification` | Send push notification to user | Ntfy API |
| `search_messages` | Search mission conversation history | PostgreSQL full-text |
| `get_current_date` | Get current date/time | datetime |
| `calculate` | Perform calculations | Python eval (sandboxed) |
| `call_api` | Call external REST API | httpx (user must configure) |

---

## Implementation Phases

### Phase 1: Foundation
**Goal:** Working app shell with mission CRUD and basic chat

**Tasks:**
- [ ] Create `apps/missions/` directory structure
- [ ] Set up Docker Compose (FastAPI + React dev containers)
- [ ] Create PostgreSQL schema (run migrations)
- [ ] Implement REST API: missions CRUD
- [ ] Implement REST API: file upload/download
- [ ] Create React app scaffold with routing
- [ ] Build mission list page
- [ ] Build mission create/edit form
- [ ] Build mission detail page (static, no chat yet)
- [ ] Integrate with Authentik (forward-auth via Caddy)
- [ ] Add to Homepage services.yaml

**Deliverable:** Can create missions, upload files, view mission list

---

### Phase 2: Chat Interface
**Goal:** Real-time streaming chat with LLM

**Tasks:**
- [ ] Implement WebSocket endpoint for chat
- [ ] Create LLM provider abstraction layer
- [ ] Integrate Anthropic Claude SDK with streaming
- [ ] Integrate OpenAI SDK with streaming
- [ ] Build settings page for API key management
- [ ] Implement API key encryption (Fernet)
- [ ] Build chat UI component with streaming display
- [ ] Implement message persistence
- [ ] Add token counting and cost tracking
- [ ] Display conversation history on mission detail

**Deliverable:** Can chat with agent, responses stream in real-time

---

### Phase 3: Context & Intelligence
**Goal:** Agent understands mission context and can use tools

**Tasks:**
- [ ] Implement context assembly (goals + files + recent history)
- [ ] Build tool framework (function calling)
- [ ] Implement `web_search` tool (Tavily integration)
- [ ] Implement `fetch_url` tool
- [ ] Implement `read_file` tool
- [ ] Implement `parse_document` tool (PDF + image OCR)
- [ ] Implement `execute_code` tool (sandboxed)
- [ ] Add tool call display in chat UI
- [ ] Implement file parsing on upload (extract text, dates, etc.)
- [ ] Build context preview in mission detail

**Deliverable:** Agent can search web, read files, extract information

---

### Phase 4: Scheduling & Notifications
**Goal:** Agent proactively checks missions and notifies user

**Tasks:**
- [ ] Set up APScheduler or Celery Beat
- [ ] Implement per-mission check scheduling
- [ ] Build scheduled check logic (what to check, when)
- [ ] Deploy Ntfy server (or use existing if available)
- [ ] Implement `send_notification` tool
- [ ] Add notification preferences to settings
- [ ] Build check log viewer in UI
- [ ] Implement deadline detection from context
- [ ] Add notification history view
- [ ] Create Homepage widget for pending notifications

**Deliverable:** Agent sends push notifications for deadlines/updates

---

### Phase 5: MCP & External Access
**Goal:** External LLM agents can interact with Missions

**Tasks:**
- [ ] Implement MCP server (Python MCP SDK)
- [ ] Expose tools: list_missions, get_mission, send_message, get_history
- [ ] Add MCP authentication (token-based)
- [ ] Document MCP interface
- [ ] Test with Claude Desktop / Claude Code

**Deliverable:** Can query and interact with missions from external agents

---

### Phase 6: Polish & Production
**Goal:** Production-ready homelab application

**Tasks:**
- [ ] Add mission categories management
- [ ] Implement mission archiving
- [ ] Add export functionality (JSON, PDF report)
- [ ] Build cost dashboard (tokens, USD by mission)
- [ ] Add rate limiting
- [ ] Implement proper error handling and recovery
- [ ] Add health check endpoint
- [ ] Create backup documentation (what to backup)
- [ ] Write app-contract.yaml
- [ ] Write README.md with operations guide
- [ ] Performance optimization (context summarization for long missions)
- [ ] Add mission templates (pre-built for common use cases)

**Deliverable:** Production-ready app with documentation

---

## File Structure

```
apps/missions/
├── compose.yml                 # Docker Compose for dev/prod
├── .env.example                # Environment template
├── app-contract.yaml           # Homelab app contract
├── README.md                   # Operations guide
├── IMPLEMENTATION.md           # This file
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml          # Python dependencies
│   ├── alembic/                # Database migrations
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Settings
│   │   ├── database.py         # PostgreSQL connection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── missions.py     # Mission CRUD
│   │   │   ├── files.py        # File upload/download
│   │   │   ├── chat.py         # WebSocket chat
│   │   │   ├── settings.py     # LLM provider config
│   │   │   └── health.py       # Health check
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── mission.py      # SQLAlchemy models
│   │   │   ├── message.py
│   │   │   └── provider.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── mission.py      # Pydantic schemas
│   │   │   ├── message.py
│   │   │   └── provider.py
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py # Main agent logic
│   │   │   ├── context.py      # Context assembly
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py     # Provider interface
│   │   │   │   ├── anthropic.py
│   │   │   │   └── openai.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── base.py     # Tool interface
│   │   │       ├── web_search.py
│   │   │       ├── fetch_url.py
│   │   │       ├── read_file.py
│   │   │       ├── parse_document.py
│   │   │       ├── execute_code.py
│   │   │       └── notifications.py
│   │   │
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py         # Scheduled tasks
│   │   │   └── checks.py       # Mission check logic
│   │   │
│   │   └── mcp/
│   │       ├── __init__.py
│   │       └── server.py       # MCP server
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_missions.py
│       └── test_agent.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts       # API client
│       │   └── websocket.ts    # WebSocket client
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── MissionCard.tsx
│       │   ├── MissionForm.tsx
│       │   ├── ChatInterface.tsx
│       │   ├── FileUpload.tsx
│       │   ├── StreamingMessage.tsx
│       │   └── ToolCallDisplay.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── MissionDetail.tsx
│       │   ├── MissionCreate.tsx
│       │   ├── Settings.tsx
│       │   └── NotFound.tsx
│       ├── hooks/
│       │   ├── useMissions.ts
│       │   ├── useChat.ts
│       │   └── useWebSocket.ts
│       ├── types/
│       │   └── index.ts
│       └── styles/
│           └── globals.css
│
└── data/                       # Gitignored, persistent storage
    └── files/                  # Mission files organized by mission ID
        └── {mission-id}/
            └── uploaded-file.pdf
```

---

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/missions` | List all missions |
| `POST` | `/api/missions` | Create mission |
| `GET` | `/api/missions/{id}` | Get mission details |
| `PUT` | `/api/missions/{id}` | Update mission |
| `DELETE` | `/api/missions/{id}` | Delete mission |
| `POST` | `/api/missions/{id}/files` | Upload file |
| `GET` | `/api/missions/{id}/files` | List mission files |
| `GET` | `/api/missions/{id}/files/{file_id}` | Download file |
| `DELETE` | `/api/missions/{id}/files/{file_id}` | Delete file |
| `GET` | `/api/missions/{id}/messages` | Get message history |
| `GET` | `/api/missions/{id}/checks` | Get check history |
| `POST` | `/api/missions/{id}/check` | Trigger manual check |
| `GET` | `/api/categories` | List categories |
| `GET` | `/api/providers` | List LLM providers |
| `PUT` | `/api/providers/{id}` | Update provider (API key) |
| `GET` | `/api/settings` | Get app settings |
| `PUT` | `/api/settings` | Update settings |
| `GET` | `/api/health` | Health check |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS /api/missions/{id}/chat` | Streaming chat connection |

### MCP Tools

| Tool | Description |
|------|-------------|
| `list_missions` | List all active missions |
| `get_mission` | Get mission details and recent history |
| `send_message` | Send message to mission agent |
| `get_history` | Get full conversation history |
| `trigger_check` | Trigger scheduled check |

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://missions:password@postgres:5432/missions

# Encryption key for API keys (generate with: openssl rand -base64 32)
ENCRYPTION_KEY=your-32-byte-base64-key

# Ntfy server
NTFY_URL=http://ntfy:80
NTFY_TOPIC=missions

# External APIs (optional, can be set in UI)
TAVILY_API_KEY=tvly-xxxxx

# Development
DEBUG=false
LOG_LEVEL=info
```

---

## Security Considerations

1. **API Key Storage** — LLM API keys encrypted at rest using Fernet symmetric encryption
2. **Code Execution** — `execute_code` tool runs in isolated Docker container with no network
3. **File Uploads** — Validate MIME types, scan for malware (ClamAV integration optional)
4. **Authentication** — All endpoints protected by Authentik forward-auth
5. **Rate Limiting** — Per-user rate limits on chat and scheduled checks
6. **Input Validation** — Pydantic schemas for all API inputs
7. **SQL Injection** — SQLAlchemy ORM with parameterized queries

---

## Cost Management

- Track tokens per message (input + output)
- Calculate cost per provider pricing
- Display running total on mission detail
- Optional: Set budget limits per mission
- Dashboard shows total spend across all missions

---

## Monitoring

- Health check endpoint for Uptime Kuma
- Structured logging (JSON format)
- Metrics: messages/day, tokens/day, check success rate
- Error tracking: failed checks, API errors

---

## Backup

**What to backup:**
- PostgreSQL database (missions, messages, settings)
- `./data/files/` directory (uploaded documents)

**Excluded from backup:**
- Nothing (all state is important)

**Recovery:**
- Restore PostgreSQL dump
- Restore files directory
- Restart containers

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Foundation | 2-3 days | 2-3 days |
| Phase 2: Chat Interface | 2-3 days | 4-6 days |
| Phase 3: Context & Intelligence | 3-4 days | 7-10 days |
| Phase 4: Scheduling & Notifications | 2-3 days | 9-13 days |
| Phase 5: MCP & External Access | 1-2 days | 10-15 days |
| Phase 6: Polish & Production | 2-3 days | 12-18 days |

**Total: 2-3 weeks** for experienced developer working part-time

---

## Getting Started

Phase 1 begins with:

```bash
# Create directory structure
mkdir -p apps/missions/{backend,frontend,data/files}

# Initialize backend
cd apps/missions/backend
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic asyncpg python-multipart

# Initialize frontend
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install

# Create Docker Compose for development
cd ..
# Create compose.yml with FastAPI + React + PostgreSQL
```

Ready to begin implementation when you are.
