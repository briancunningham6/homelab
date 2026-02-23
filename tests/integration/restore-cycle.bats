#!/usr/bin/env bats

load ../test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

@test "backup restore cycle recovers original data" {
  create_basic_compose_app "apps" "restoreapp"
  mkdir -p "$HOMELAB_DIR/apps/restoreapp/data"
  echo "v1" > "$HOMELAB_DIR/apps/restoreapp/data/state.txt"

  run scripts/app-backup restoreapp
  [ "$status" -eq 0 ]

  echo "v2" > "$HOMELAB_DIR/apps/restoreapp/data/state.txt"

  run bash -c "printf 'y\n' | scripts/app-restore restoreapp latest"
  [ "$status" -eq 0 ]
  [[ "$output" == *"restored and restarted"* ]]

  run cat "$HOMELAB_DIR/apps/restoreapp/data/state.txt"
  [ "$status" -eq 0 ]
  [ "$output" = "v1" ]

  run grep -c "docker compose -f $HOMELAB_DIR/apps/restoreapp/compose.yml down" "$TEST_LOG"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]

  run grep -c "docker compose -f $HOMELAB_DIR/apps/restoreapp/compose.yml up -d" "$TEST_LOG"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]
}
