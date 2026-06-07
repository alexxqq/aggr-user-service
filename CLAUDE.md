# User Service Development Rules

## Project context

This repository contains only the User Service of the thesis system.

The User Service is the source of truth for:
- merchant profile
- merchant status
- merchant capabilities
- payout wallets
- webhook configuration
- anti-abuse / limits
- feature flags

The User Service must store:
- internal merchant_id
- firebase_uid link
- merchant status
- allowed chains
- allowed assets
- default chain
- payout wallets
- webhook endpoint + webhook secret metadata
- limits
- optional feature flags

The User Service must NOT store:
- products
- prices
- invoices
- payment intents
- payment analytics
- blockchain transactions
- private keys

## Architecture constraints

- Use FastAPI
- Use PostgreSQL
- Use SQLAlchemy + Alembic
- Keep modules simple and explicit
- Prefer service + repository separation
- Each change must preserve clear domain boundaries
- Do not add logic that belongs to Payment Service or Blockchain Core

## Authentication assumptions for MVP

- External requests come from API Gateway
- Gateway verifies Firebase token
- Gateway passes auth context downstream
- Internal service-to-service auth for MVP may use X-Internal-Secret
- Do not implement direct Firebase auth inside this service unless explicitly required
- Do not make this service depend on frontend behavior

## Required domain objects

Implement and maintain support for:
- Merchant
- MerchantSettings
- Wallet
- WebhookConfig
- MerchantLimits
- MerchantFeatures

## Expected responsibilities

This service should provide merchant identity/configuration APIs for:
- merchant profile retrieval
- merchant settings retrieval/update
- payout wallet management
- webhook config management
- merchant limits retrieval/update
- merchant feature flags retrieval/update
- merchant status/capabilities lookup for internal services

## Workflow rules

For every task:
1. Read spec/service_scope.md and spec/acceptance_checklist.md
2. Inspect existing code before changing anything
3. Write a short implementation plan to docs/plan.md
4. Reuse existing code where possible
5. Implement the smallest correct change
6. Add or update tests
7. Run formatting, linting, and tests
8. Update docs/test_report.md with what was run and the result
9. Update spec/acceptance_checklist.md

## Safety rules

- Do not rewrite the whole service unless absolutely necessary
- Do not delete working code without strong justification
- Do not invent new architecture layers unless needed
- Do not claim a feature is complete without tests or manual verification evidence
- If something is ambiguous, record it in docs/open_questions.md and proceed with the safest MVP assumption

## Definition of done

A task is done only if:
- code is implemented
- migrations are created if schema changed
- tests pass
- service starts in docker-compose
- docs are updated
- acceptance checklist is updated