# run-service-validation

Validate the current state of the User Service.

## Steps

1. Run formatting check: `black --check app tests`
2. Run linting: `ruff check app tests`
3. Run unit tests: `pytest tests/unit -q`
4. Run integration tests: `pytest tests/integration -q`
5. Verify docker startup: `docker compose config && docker compose up --build -d`
6. Summarize failures
7. Fix the smallest issues first
8. Update `docs/test_report.md`
