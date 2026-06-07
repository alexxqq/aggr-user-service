# add-db-migration

Add a database schema change safely.

## Steps

1. Inspect existing models (`app/models/`) and migrations (`alembic/versions/`)
2. Make the smallest required model change
3. Generate or write Alembic migration: `alembic revision --autogenerate -m "<description>"`
4. Verify upgrade works: `alembic upgrade head`
5. Update tests if needed
6. Document the schema change in `docs/architecture.md`

## Rules

- Avoid destructive changes unless required
- Keep migration names descriptive
- Ensure models and migrations stay aligned
