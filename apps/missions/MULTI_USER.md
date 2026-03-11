# Multi-User Access — Implementation Plan

## Overview

Add multi-user support to Missions using Authentik (already in the homelab stack) via Caddy forward auth. Users are auto-provisioned on first login. Mission creators can share their missions with other users. All members have equal permissions.

**Approach: Caddy Forward Auth**

Caddy authenticates every request through Authentik before it reaches the backend. Authentik injects identity headers that the backend reads to identify the user. This means:

- No OAuth2/OIDC code in the React frontend
- No JWT validation in FastAPI
- No session management in the app
- Users are created automatically on first visit

---

## Phase 1 — Database Schema

### New tables

```sql
-- Stores users auto-provisioned from Authentik
CREATE TABLE users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    authentik_id TEXT UNIQUE NOT NULL,   -- Authentik 'sub' claim / user ID
    username     TEXT NOT NULL,
    email        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mission membership (many-to-many)
CREATE TABLE mission_members (
    mission_id  UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (mission_id, user_id)
);
```

### Modified tables

```sql
-- Add owner tracking to missions
ALTER TABLE missions ADD COLUMN owner_id UUID REFERENCES users(id);
```

### Migration notes

- Create an Alembic migration for the above
- Backfill: create a placeholder "system" user and set all existing missions' `owner_id` to it, then insert corresponding `mission_members` rows
- `owner_id` can be made `NOT NULL` after backfill

---

## Phase 2 — Backend

### 2.1 User model

New file: `app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authentik_id = Column(Text, unique=True, nullable=False)
    username     = Column(Text, nullable=False)
    email        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    missions     = relationship("Mission", secondary="mission_members", back_populates="members")
```

### 2.2 Auth dependency

New file: `app/auth.py`

Reads the headers injected by Authentik via Caddy:

| Header                              | Value                     |
|-------------------------------------|---------------------------|
| `X-Forwarded-Preferred-Username`    | username                  |
| `X-Forwarded-User`                  | Authentik sub (unique ID) |
| `X-Forwarded-Email`                 | email address             |

```python
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    authentik_id = request.headers.get("X-Forwarded-User")
    username     = request.headers.get("X-Forwarded-Preferred-Username", "unknown")
    email        = request.headers.get("X-Forwarded-Email")

    if not authentik_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.authentik_id == authentik_id).first()
    if not user:
        user = User(authentik_id=authentik_id, username=username, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
```

For local development (no Authentik), support a `DEV_USER` env var that bypasses the header check and returns a fixed user.

### 2.3 `/api/me` endpoint

```
GET /api/me
→ { id, username, email }
```

Used by the frontend on load to display the logged-in user.

### 2.4 Mission access control

Add a `require_mission_access` dependency that checks the requesting user is either the owner or a member of the mission. Apply to all `/api/missions/{id}/...` endpoints.

```python
def require_mission_access(
    mission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Mission:
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    is_member = db.query(MissionMember).filter(
        MissionMember.mission_id == mission_id,
        MissionMember.user_id == current_user.id,
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    return mission
```

### 2.5 Mission list filtering

`GET /api/missions/` filters to only missions where `current_user` is a member:

```python
missions = (
    db.query(Mission)
    .join(MissionMember, MissionMember.mission_id == Mission.id)
    .filter(MissionMember.user_id == current_user.id)
    .all()
)
```

### 2.6 Mission creation

On `POST /api/missions/`, set `owner_id = current_user.id` and insert a row into `mission_members` for the creator.

### 2.7 Membership endpoints

```
GET    /api/missions/{id}/members              → list members [{ id, username, email }]
POST   /api/missions/{id}/members              → add member by username { "username": "..." }
DELETE /api/missions/{id}/members/{user_id}    → remove member (owner only)
```

For `POST`, look up the user by `username` and insert into `mission_members`. Return 404 if username not found (must have logged in at least once to be added).

---

## Phase 3 — Frontend

### 3.1 Current user context

On app load, fetch `GET /api/me` and store the result in a React context (`UserContext`). This provides `{ id, username, email }` app-wide.

If the response is 401, the user is not authenticated — Caddy/Authentik will have already redirected them to the login page before reaching this point, so this case should not occur in practice.

### 3.2 Username display

Add a user info widget to the app header/nav bar (top right):

```
[avatar initial]  username  ↓
```

Keep it minimal — just the username with a small avatar showing the first letter. No dropdown needed unless logout is desired (Authentik handles logout via its own URL).

### 3.3 Mission sharing UI

Add a **Members** section to the Overview tab, below Context Files:

```
Members (2)
──────────────────────────────────────
👤 alice (owner)
👤 bob                         [Remove]

Add member:  [username input]  [Add]
```

- Fetch from `GET /api/missions/{id}/members`
- "Remove" button calls `DELETE /api/missions/{id}/members/{user_id}` — only shown to owner, and not for the owner themselves
- "Add" calls `POST /api/missions/{id}/members` with `{ username }`
- Show error inline if username not found

### 3.4 No other frontend changes needed

The mission list already only shows missions returned by the API — once the backend filters by membership, the list automatically shows only accessible missions.

---

## Phase 4 — Caddy + Authentik Wiring

### 4.1 Authentik setup

1. In Authentik admin, create a new **Proxy Provider** for `missions.home`:
   - Mode: Forward auth (single application)
   - External host: `http://missions.home`
   - Token validity: as desired
2. Create an **Application** linked to that provider
3. Set access policy so permitted users/groups can access it

### 4.2 Caddy config

Add forward auth to the `missions.home` site block:

```caddy
missions.home {
    forward_auth authentik-outpost:9000 {
        uri /outpost.goauthentik.io/auth/caddy
        copy_headers X-Forwarded-User X-Forwarded-Preferred-Username X-Forwarded-Email
    }

    reverse_proxy missions-frontend:5173
}
```

The outpost container (`authentik-outpost`) must be on `caddy-net`.

---

## Phase 5 — Local Development

Add a `DEV_USER` environment variable to the backend:

```env
DEV_USER=localdev
DEV_USER_ID=00000000-0000-0000-0000-000000000001
DEV_USER_EMAIL=dev@local
```

When set, `get_current_user` returns a fixed user without checking headers. This allows running the app locally without Authentik.

The `compose.yml` dev override can set these vars; the production `compose.yml` leaves them unset so real auth is enforced.

---

## Implementation Order

1. **Alembic migration** — `users`, `mission_members`, `owner_id` on missions
2. **Backfill migration** — seed system user, assign existing missions
3. **`app/models/user.py`** + update `Mission` model relationships
4. **`app/auth.py`** — `get_current_user` dependency with dev bypass
5. **`GET /api/me`** endpoint
6. **Update mission endpoints** — filter by membership, set owner on create
7. **Membership endpoints** — list, add, remove
8. **Frontend `UserContext`** + `/api/me` fetch
9. **Username display** in app header
10. **Members section** in Overview tab
11. **Caddy + Authentik** wiring in production

---

## What Is Out of Scope

- Per-mission roles (owner vs member — all members have equal access)
- Audit log of who performed which actions
- Invitation emails or invite links
- Public/private mission toggle
- Transferring mission ownership
