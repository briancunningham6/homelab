# Onboarding Guide

> Admin bootstrap and user management | Parent: [DESIGN.md](../DESIGN.md)

---

## Prerequisites

Before onboarding anyone, the following must be running (Phase 1 + Phase 2 of the [rollout plan](rollout-plan.md)):

- [ ] Docker Engine + Compose operational
- [ ] Caddy reverse proxy serving `*.home` hostnames
- [ ] Tailscale connected for remote access
- [ ] Uptime Kuma monitoring endpoints
- [ ] Authentik deployed and reachable at `login.home`

---

## Part 1: Admin Bootstrap (Day 1)

The first operator bootstraps the platform. This is a one-time process.

### 1.1 Deploy Authentik

Authentik is deployed via Compose like every other service:

```bash
cd ~/homelab/platform/authentik
# Set AUTHENTIK_BOOTSTRAP_PASSWORD in .env before first start
docker compose up -d
```

On first start, Authentik creates a default `akadmin` account using the password from `AUTHENTIK_BOOTSTRAP_PASSWORD`. This account is the **break-glass emergency admin** — it will not be used for daily operations.

### 1.2 First login and platform configuration

1. Open `login.home` and sign in as `akadmin`.
2. **Branding:** Admin → System → Tenants → Default — set platform name, logo, and colours so it looks like a family system.
3. **Authentication flow:** Configure the default login flow to require password + MFA for admin-tier users.
4. **Enrollment flow:** Create an invite-based enrollment flow (Admin → Flows → Create).
   - Type: Enrollment
   - Stages: invitation acceptance → user details → password setup → MFA setup (conditional on group)
   - **Do not enable self-registration** — all users are created by an admin.
5. **Disable or restrict the recovery flow** as needed for your security model.

### 1.3 Create baseline groups

Create the following groups in Admin → Directory → Groups:

| Group | Purpose | MFA required |
|-------|---------|-------------|
| `homelab-admin` | Full platform administration | Yes |
| `parents` | Parent-level app access | Yes |
| `kids` | Child-level access with restrictions | Optional |

App-specific groups are created as each app is deployed:

| Group | Created when |
|-------|-------------|
| `immich-admin` | Immich deployed (Phase 3) |
| `immich-user` | Immich deployed (Phase 3) |
| `ai-admin` | AI deployed (Phase 6) |
| `ai-user` | AI deployed (Phase 6) |
| `ai-kids` | AI deployed (Phase 6) |

### 1.4 Create the admin's personal account

The `akadmin` account is for emergencies only. Create a named account for daily use:

1. Admin → Directory → Users → Create.
2. Set username, real name, and email.
3. Assign to groups: `homelab-admin`, `parents`.
4. Set a strong password and configure MFA (TOTP or WebAuthn).
5. Log out of `akadmin` and log in with the new account.
6. Verify access to the Authentik admin panel and all deployed services.

> From this point forward, use the named admin account. The `akadmin` account is break-glass only.

### 1.5 Configure SSO for each app

For every deployed application:

1. **Create a Provider** in Authentik (Admin → Applications → Providers → Create):
   - Type: OAuth2/OpenID Connect (preferred)
   - Note the Client ID and Client Secret
   - Set the Redirect URI to the app's callback URL (e.g., `https://immich.home/auth/login`)

2. **Create an Application** (Admin → Applications → Applications → Create):
   - Link to the provider created above
   - Set the launch URL

3. **Map groups to app roles:**
   - Use Authentik's group-to-scope or group-to-claim mapping
   - Example: `immich-admin` group → Authentik scope → Immich admin role

4. **Configure the app** to use Authentik as its OIDC provider:
   - Set the OIDC issuer URL (e.g., `https://login.home/application/o/<app-slug>/`)
   - Set client ID, client secret, and redirect URI
   - Map claims/scopes to internal roles

5. **Test:** Log in as the admin and verify SSO works end-to-end.

6. **Document:** Update `docs/access-matrix.md` and `docs/inventory.md`.

### 1.6 Secure the break-glass account

| Item | Action |
|------|--------|
| `akadmin` password | Store in password manager |
| Offline copy | Print or write credentials and seal in envelope, store securely offsite |
| Access policy | Only used when the named admin account is locked out or Authentik flows are broken |
| Review | Verify break-glass access works during quarterly DR drills |

---

## Part 2: Adding Users

All user accounts are created by an admin. There is no self-registration.

### Step-by-step

**1. Create the user account**

Admin → Directory → Users → Create:
- Username (e.g., `sarah`, `alex`)
- Full name
- Email address
- Do **not** set a password manually — the enrollment flow handles this

**2. Assign groups**

Based on who the person is:

| Person type | Groups to assign |
|-------------|-----------------|
| Adult family member | `parents` + app groups (e.g., `immich-user`, `ai-user`) |
| Child | `kids` + restricted app groups (e.g., `immich-user`, `ai-kids`) |
| Additional admin (rare) | `homelab-admin` + `parents` + app groups |

**3. Send enrollment invitation**

1. Admin → Directory → Invitations → Create.
2. Select the enrollment flow configured in step 1.2.
3. Optionally set an expiry (e.g., 7 days).
4. Copy the enrollment link and send it to the user (text, email, in person).

**4. User completes enrollment**

The user:
1. Opens the enrollment link.
2. Confirms their details (name, email).
3. Sets their own password.
4. If required by group policy: sets up MFA (TOTP app or security key).
5. Is redirected to the dashboard or login page.

**5. User accesses apps**

- User visits any app (e.g., `immich.home`).
- Redirected to `login.home` for SSO.
- After authentication, redirected back to the app with appropriate role/permissions.
- User only sees and can access apps their groups permit.

**6. Admin verifies**

- Check Authentik's audit log (Admin → Events → Logs) for successful enrollment.
- Verify the user appears in each relevant app's user list with the correct role.
- Update `docs/access-matrix.md` if needed.

---

## Part 3: Managing Users

### Modifying access

- **Add app access:** Assign user to the app's group in Authentik. Takes effect immediately at next login.
- **Remove app access:** Remove user from the group. Takes effect immediately.
- **Promote to admin:** Add to `homelab-admin` group. Require MFA if not already set.

### Disabling a user

1. Admin → Directory → Users → select user → toggle Active to off.
2. All sessions are invalidated. The user cannot log in or access any app.
3. This is immediate — no waiting for token expiry.

### Removing a user

1. Disable the user first (above).
2. Review whether user-owned data in apps needs to be transferred or archived.
3. Delete the user in Authentik when ready.
4. Update `docs/access-matrix.md`.

---

## Quick Reference

| Task | Where |
|------|-------|
| Create a user | Authentik → Directory → Users → Create |
| Assign groups | Authentik → Directory → Users → select user → Groups tab |
| Send invite | Authentik → Directory → Invitations → Create |
| Disable a user | Authentik → Directory → Users → select user → toggle Active |
| View audit log | Authentik → Events → Logs |
| Check group membership | Authentik → Directory → Groups → select group → Users tab |
| Update access docs | `docs/access-matrix.md` |
