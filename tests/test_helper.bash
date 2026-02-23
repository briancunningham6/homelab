#!/usr/bin/env bash

setup_test_env() {
  TEST_ROOT="$(mktemp -d)"
  export TEST_ROOT
  export HOMELAB_DIR="$TEST_ROOT/homelab"
  export LOCAL_BACKUP_DIR="$HOMELAB_DIR/backups/local"
  export TEST_BIN="$TEST_ROOT/bin"
  export TEST_LOG="$TEST_ROOT/commands.log"

  mkdir -p "$HOMELAB_DIR" "$LOCAL_BACKUP_DIR" "$TEST_BIN"
  : > "$TEST_LOG"

  export PATH="$TEST_BIN:$PATH"

  create_docker_stub
  create_sleep_stub
  create_curl_stub
  create_df_stub
}

teardown_test_env() {
  if [ -n "${TEST_ROOT:-}" ] && [ -d "$TEST_ROOT" ]; then
    rm -rf "$TEST_ROOT"
  fi
}

create_basic_compose_app() {
  local group="$1"
  local app="$2"

  mkdir -p "$HOMELAB_DIR/$group/$app"
  cat > "$HOMELAB_DIR/$group/$app/compose.yml" <<'EOF'
services:
  app:
    image: busybox:latest
    command: ["sh", "-c", "sleep 60"]
EOF
}

create_docker_stub() {
  cat > "$TEST_BIN/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "docker $*" >> "${TEST_LOG:?}"

if [ "${1:-}" = "compose" ]; then
  case "$*" in
    *" config --services"*)
      echo "app"
      exit 0
      ;;
    *" config"*)
      if [ -n "${DOCKER_CONFIG_FAIL_DIR:-}" ] && [[ "$PWD" == *"${DOCKER_CONFIG_FAIL_DIR}"* ]]; then
        echo "compose validation error" >&2
        exit 1
      fi
      exit 0
      ;;
    *" ps --status running --quiet"*)
      echo "container-id"
      exit 0
      ;;
    *" ps"*)
      echo "NAME STATUS"
      exit 0
      ;;
    *" up -d"*)
      exit 0
      ;;
    *" down"*)
      exit 0
      ;;
  esac
fi

if [ "${1:-}" = "inspect" ]; then
  exit 0
fi

if [ "${1:-}" = "exec" ]; then
  echo "200"
  exit 0
fi

exit 0
EOF
  chmod +x "$TEST_BIN/docker"
}

create_sleep_stub() {
  cat > "$TEST_BIN/sleep" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$TEST_BIN/sleep"
}

create_restic_stub() {
  cat > "$TEST_BIN/restic" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "restic $*" >> "${TEST_LOG:?}"

if [ "${1:-}" = "snapshots" ]; then
  echo '[{"time":"2026-02-23T00:00:00Z"}]'
  exit 0
fi

exit 0
EOF
  chmod +x "$TEST_BIN/restic"
}

create_curl_stub() {
  cat > "$TEST_BIN/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# dr-verify reads only the HTTP status code from curl's -w "%{http_code}".
status="${CURL_STATUS_CODE:-200}"
printf "%s" "$status"
EOF
  chmod +x "$TEST_BIN/curl"
}

create_df_stub() {
  cat > "$TEST_BIN/df" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Default to healthy usage unless overridden for tests.
pct="${DF_USAGE_PERCENT:-42}"
cat <<OUT
Filesystem      Size   Used  Avail Capacity Mounted on
/dev/disk1s5   500Gi  210Gi  290Gi    ${pct}% /
OUT
EOF
  chmod +x "$TEST_BIN/df"
}
