# audit-existing-service

Audit the existing User Service implementation before changing it.

## Steps

1. Read `spec/service_scope.md`
2. Inspect project structure and existing code (`app/`, `alembic/`, `tests/`)
3. Identify implemented parts, incomplete parts, and architecture mismatches
4. Write findings to `docs/plan.md`
5. Propose the smallest next step that moves the service toward the target architecture

## Rules

- Prefer reuse over rewrite
- Preserve working code
- Explicitly mark risky refactors
- Focus on domain boundaries and MVP scope
