# update-docs

Update project documentation based only on actual implementation status.

## Steps

1. Read current code in `app/` to determine what is actually implemented
2. Update `docs/architecture.md` to reflect actual structure
3. Update `docs/api_contract.md` to match actual endpoints
4. Update `docs/test_report.md` with latest test results
5. Update `spec/acceptance_checklist.md` — mark items done only if verified

## Rules

- Do not document features that do not exist
- Prefer short factual notes
- Include what was tested and what remains incomplete
