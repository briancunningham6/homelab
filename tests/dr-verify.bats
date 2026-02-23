#!/usr/bin/env bats

load test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

@test "dr-verify succeeds when core checks are healthy" {
  create_basic_compose_app "platform" "caddy"
  create_basic_compose_app "apps" "immich"

  run scripts/dr-verify
  [ "$status" -eq 0 ]
  [[ "$output" == *"PASSED WITH WARNINGS"* || "$output" == *"ALL CHECKS PASSED"* ]]
}

@test "dr-verify fails when health endpoint is unhealthy" {
  create_basic_compose_app "platform" "caddy"
  create_basic_compose_app "apps" "immich"
  export CURL_STATUS_CODE=500

  run scripts/dr-verify
  [ "$status" -ne 0 ]
  [[ "$output" == *"FAILED:"* ]]
}
