#!/usr/bin/env bats

load test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

@test "app-up prints usage when no app argument is provided" {
  run scripts/app-up
  [ "$status" -eq 1 ]
  [[ "$output" == *"Usage: app-up <app-name>"* ]]
}

@test "app-up fails when app path cannot be resolved" {
  run scripts/app-up missing-app
  [ "$status" -eq 1 ]
  [[ "$output" == *"not found"* ]]
}

@test "app-up starts app and checks container status" {
  create_basic_compose_app "apps" "demo"

  run scripts/app-up demo
  [ "$status" -eq 0 ]
  [[ "$output" == *"started successfully"* ]]

  run grep -c "docker compose -f $HOMELAB_DIR/apps/demo/compose.yml up -d" "$TEST_LOG"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]

  run grep -c "docker compose -f $HOMELAB_DIR/apps/demo/compose.yml ps" "$TEST_LOG"
  [ "$status" -eq 0 ]
  [ "$output" -eq 1 ]
}
