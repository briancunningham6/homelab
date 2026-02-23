#!/usr/bin/env bats

load test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

@test "app-backup exits cleanly when app has no data directory" {
  create_basic_compose_app "apps" "nodata"

  run scripts/app-backup nodata
  [ "$status" -eq 0 ]
  [[ "$output" == *"nothing to backup"* ]]
}

@test "app-backup creates local tar backup when restic is not configured" {
  create_basic_compose_app "apps" "photos"
  mkdir -p "$HOMELAB_DIR/apps/photos/data"
  echo "hello-world" > "$HOMELAB_DIR/apps/photos/data/file.txt"

  run scripts/app-backup photos
  [ "$status" -eq 0 ]
  [[ "$output" == *"Backup complete:"* ]]

  run find "$LOCAL_BACKUP_DIR" -name "photos-*.tar.gz"
  [ "$status" -eq 0 ]
  [ -n "$output" ]
}

@test "app-backup uses restic when configured" {
  create_basic_compose_app "apps" "vault"
  mkdir -p "$HOMELAB_DIR/apps/vault/data"
  cat > "$HOMELAB_DIR/apps/vault/.env" <<'EOF'
RESTIC_REPOSITORY=/tmp/restic-repo
RESTIC_PASSWORD=test-password
EOF
  create_restic_stub

  run scripts/app-backup vault
  [ "$status" -eq 0 ]
  [[ "$output" == *"Using Restic for backup"* ]]

  run grep -c "restic backup $HOMELAB_DIR/apps/vault/data --tag vault" "$TEST_LOG"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]
}
