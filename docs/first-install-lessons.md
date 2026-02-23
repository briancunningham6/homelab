# First Install Lessons (Mac mini, Feb 2026)

Use this as a preflight checklist before future installs.

## 1) Path and stack assumptions

- Set `HOMELAB_DIR` explicitly when running scripts from non-default location:
  - `HOMELAB_DIR=/Users/<username>/dev/homelab ./scripts/platform-up`
- `platform/dockge/.env` must point to the real repo path:
  - `DOCKGE_STACKS_DIR=/Users/<username>/dev/homelab`

## 2) Caddy routing for practical access

- During setup/testing, include all hostnames/IPs you actually use:
  - `immich.home`
  - `<LAN_IP>` (LAN)
  - `<TAILSCALE_IP>` (Tailscale)
- If Safari says server dropped connection on `https://immich.home`, test `http://...` first.
- Current setup is HTTP-only for internal experiment mode.

## 3) Authentik bootstrap/admin

- Default bootstrap username is `akadmin`.
- If bootstrap login flow is unclear, create/update an admin user directly from container shell.
- Ensure desired admin is in `authentik Admins` group.

## 4) Immich OIDC integration gotchas

The original automation script needed updates for Authentik 2024.12 API:

- `invalidation_flow` is required on OAuth provider create.
- `redirect_uris` must be a list of objects:
  - `[{"matching_mode":"strict","url":"..."}]`
- Provider must include OIDC scope mappings (`openid`, `profile`, `email`) via property mappings.

## 5) iPhone-specific OAuth callback

- Immich iOS app uses this redirect URI:
  - `app.immich:///oauth-callback`
- Add it to Authentik provider redirect URIs or iOS login will fail with Redirect URI Error.

## 6) Phone-compatible issuer URL

- `login.home` won’t resolve on iPhone without hosts overrides.
- For Tailscale-first mobile setup, use issuer reachable on phone:
  - `http://<TAILSCALE_IP>:9000/application/o/immich/`
- Expose Authentik server port for this mode:
  - `9000:9000` on `authentik-server`.

## 7) Recommended preflight before enabling OAuth

1. Confirm Immich web UI loads from laptop and phone.
2. Confirm Authentik endpoint is reachable from same devices.
3. Confirm redirect URIs include web + iOS callback URIs.
4. Confirm issuer URL matches reachable Authentik host.
5. Test login from browser first, then iOS app.

## 8) Authentik outpost + Caddy forward-auth gotcha (Backrest)

- `forward_auth` to `/outpost.goauthentik.io/auth/caddy` can return **404** until a matching proxy provider is fully configured and attached to the embedded outpost.
- Required components for protected app (`backup.home`):
  1. Proxy provider (`mode=forward_single`, `external_host=http://backup.home`)
  2. Application bound to that provider
  3. Policy binding/group access (`homelab-admin`)
  4. Provider attached to `authentik Embedded Outpost`
- Direct `curl` to outpost auth endpoint may return **500 configuration error** if Caddy forward-auth headers are missing; this is expected in manual tests.
- Correct end-to-end test is via Caddy route:
  - `curl -I -H 'Host: backup.home' http://127.0.0.1/`
  - expected: `302` redirect to Authentik authorize URL.

## 9) Follow-up improvements

- Add `scripts/setup-authentik-backrest` for idempotent setup of provider/app/group/outpost attachment.
- Update `scripts/setup-authentik-immich` to fully support Authentik 2024.12 and iOS callback by default.
- Add an automated OIDC/forward-auth validation script:
  - verify issuer reachability
  - verify provider redirect URIs
  - verify required scope mappings
  - verify outpost endpoint and 302 behavior through Caddy
- Optional: add HTTPS with a trusted hostname for better mobile UX.
