# Test Suite

This directory contains Bats tests for critical operational scripts.

## Layout

- `test_helper.bash`: Shared fixture and command-stub helpers.
- `*.bats`: Script-level tests for core tooling.
- `integration/*.bats`: End-to-end style script workflows using isolated fixtures.

## Local Run

Install Bats and run:

```bash
bats -r tests
```

## Coverage Goals (Milestone D)

- Core script behavior (`app-up`, `app-backup`, `validate-compose`, `dr-verify`)
- Backup/restore verification workflow
- Regression-safe script behavior through deterministic stubs
