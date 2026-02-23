#!/usr/bin/env bats

load test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

@test "validate-compose succeeds when all compose files are valid" {
  create_basic_compose_app "apps" "ok-one"
  create_basic_compose_app "platform" "ok-two"

  run scripts/validate-compose
  [ "$status" -eq 0 ]
  [[ "$output" == *"All compose files valid."* ]]
}

@test "validate-compose fails when one compose file is invalid" {
  create_basic_compose_app "apps" "ok-one"
  create_basic_compose_app "apps" "bad-one"
  export DOCKER_CONFIG_FAIL_DIR="/apps/bad-one"

  run scripts/validate-compose
  [ "$status" -ne 0 ]
  [[ "$output" == *"FAILED"* ]]
}
