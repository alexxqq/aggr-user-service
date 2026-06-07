# implement-endpoint

Implement or fix one endpoint in the User Service.

## Steps

1. Read `spec/service_scope.md` and `spec/acceptance_checklist.md`
2. Inspect existing routers, schemas, services, repositories, and models
3. Implement only the requested endpoint or the minimum supporting code
4. Add or update tests
5. Run targeted validation: `bash .claude/hooks/run-targeted-tests.sh`
6. Update `docs/api_contract.md` and `spec/acceptance_checklist.md`

## Rules

- Keep endpoint contracts explicit
- Reuse existing models if reasonable
- Do not add unrelated features
