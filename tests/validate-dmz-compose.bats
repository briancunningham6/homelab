#!/usr/bin/env bats

load test_helper

setup() {
  setup_test_env
}

teardown() {
  teardown_test_env
}

create_dmz_compose() {
  local app="$1"
  local body="$2"

  mkdir -p "$HOMELAB_DIR/dmz/$app"
  cat > "$HOMELAB_DIR/dmz/$app/compose.yml" <<EOF
$body
EOF
}

@test "validate-dmz-compose succeeds for a compliant DMZ app" {
  create_dmz_compose "good-app" "services:
  web:
    image: nginx:1.27-alpine
    user: \"101:101\"
    ports:
      - \"127.0.0.1:6180:8080\"
    healthcheck:
      test: [\"CMD-SHELL\", \"exit 0\"]
    labels:
      - \"com.homelab.zone=dmz\"
"

  run scripts/validate-dmz-compose good-app
  [ "$status" -eq 0 ]
  [[ "$output" == *"DMZ compose validation passed."* ]]
}

@test "validate-dmz-compose fails when privileged mode is enabled" {
  create_dmz_compose "bad-privileged" "services:
  web:
    image: nginx:1.27-alpine
    user: \"101:101\"
    privileged: true
    ports:
      - \"127.0.0.1:6180:8080\"
    healthcheck:
      test: [\"CMD-SHELL\", \"exit 0\"]
    labels:
      - \"com.homelab.zone=dmz\"
"

  run scripts/validate-dmz-compose bad-privileged
  [ "$status" -ne 0 ]
  [[ "$output" == *"privileged containers are not allowed"* ]]
}

@test "validate-dmz-compose fails when ports are not loopback-bound" {
  create_dmz_compose "bad-ports" "services:
  web:
    image: nginx:1.27-alpine
    user: \"101:101\"
    ports:
      - \"8080:8080\"
    healthcheck:
      test: [\"CMD-SHELL\", \"exit 0\"]
    labels:
      - \"com.homelab.zone=dmz\"
"

  run scripts/validate-dmz-compose bad-ports
  [ "$status" -ne 0 ]
  [[ "$output" == *"non-loopback port mapping"* ]]
}
