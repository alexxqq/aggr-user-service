"""Internal API (service-to-service, X-Internal-Secret required).

Spec endpoints:
  GET  /internal/merchant/{merchant_id}/config
  GET  /internal/merchant/{merchant_id}/capabilities
  POST /internal/merchant/init

Legacy (kept for backward compat):
  GET  /internal/merchants/{merchant_id}
  GET  /internal/merchants/{merchant_id}/limits
  GET  /internal/users/{firebase_uid}
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import verify_internal_secret
from app.models.user import UserStatus
from app.schemas.internal import (
    InternalLimitsItem,
    InternalMerchantCapabilitiesResponse,
    InternalMerchantConfigResponse,
    InternalMerchantLimitsResponse,
    InternalUserConfigResponse,
    InternalWalletItem,
    MerchantInitRequest,
    MerchantInitResponse,
)
from app.services import user_service

router = APIRouter(prefix="/internal", tags=["internal"])


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _internal_limits(user) -> InternalLimitsItem | None:
    if not user.merchant_limits:
        return None
    L = user.merchant_limits
    return InternalLimitsItem(
        max_txs_per_day=L.max_txs_per_day,
        max_pending_invoices=L.max_pending_invoices,
        max_single_tx_amount_usd=L.max_single_tx_amount_usd,
    )


def _build_config(user, merchant_id: UUID) -> InternalMerchantConfigResponse:
    settings = user.merchant_settings
    wallets = [
        InternalWalletItem(
            chain=w.chain,
            address=w.address,
            label=w.label,
            is_default=w.is_default,
        )
        for w in user.wallets
    ]
    webhook_url = None
    webhook_enabled = False
    webhook_secret = None
    if user.webhook_config:
        webhook_enabled = user.webhook_config.is_enabled
        if webhook_enabled:
            webhook_url = user.webhook_config.webhook_url
        webhook_secret = user.webhook_config.secret_plain
    return InternalMerchantConfigResponse(
        merchant_id=merchant_id,
        status=user.status,
        allowed_chains=settings.allowed_chains if settings else [],
        allowed_assets=settings.allowed_assets if settings else [],
        default_chain=settings.default_chain if settings else None,
        wallets=wallets,
        webhook_url=webhook_url,
        webhook_enabled=webhook_enabled,
        webhook_secret=webhook_secret,
        limits=_internal_limits(user),
    )


def _require_merchant(user, merchant_id: UUID):
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")


# ---------------------------------------------------------------------------
# Spec-compliant endpoints (singular /merchant/)
# ---------------------------------------------------------------------------


@router.post(
    "/merchant/init",
    response_model=MerchantInitResponse,
    status_code=status.HTTP_200_OK,
)
async def internal_merchant_init(
    payload: MerchantInitRequest,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> MerchantInitResponse:
    """
    Idempotent merchant bootstrap called by API Gateway after Firebase verification.
    Creates merchant + settings + limits + feature_flags if not exists.
    Returns merchant_id for use in X-Merchant-Id header.
    """
    existing = await user_service.get_user_by_firebase_uid(db, payload.firebase_uid)
    if existing:
        return MerchantInitResponse(
            merchant_id=existing.id,
            firebase_uid=existing.firebase_uid,
            status=existing.status,
            created=False,
        )

    user = await user_service.init_user(
        db,
        firebase_uid=payload.firebase_uid,
        email=payload.email,
        display_name=payload.display_name,
    )
    return MerchantInitResponse(
        merchant_id=user.id,
        firebase_uid=user.firebase_uid,
        status=user.status,
        created=True,
    )


@router.get(
    "/merchant/{merchant_id}/config",
    response_model=InternalMerchantConfigResponse,
)
async def internal_merchant_config(
    merchant_id: UUID,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> InternalMerchantConfigResponse:
    """Full merchant config (spec-compliant path)."""
    user = await user_service.get_user_by_id(db, merchant_id)
    _require_merchant(user, merchant_id)
    return _build_config(user, merchant_id)


@router.get(
    "/merchant/{merchant_id}/capabilities",
    response_model=InternalMerchantCapabilitiesResponse,
)
async def internal_merchant_capabilities(
    merchant_id: UUID,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> InternalMerchantCapabilitiesResponse:
    """Merchant capabilities: status, allowed chains and assets."""
    user = await user_service.get_user_by_id(db, merchant_id)
    _require_merchant(user, merchant_id)
    settings = user.merchant_settings
    return InternalMerchantCapabilitiesResponse(
        merchant_id=merchant_id,
        status=user.status,
        is_active=user.status == UserStatus.ACTIVE,
        allowed_chains=settings.allowed_chains if settings else [],
        allowed_assets=settings.allowed_assets if settings else [],
        default_chain=settings.default_chain if settings else None,
    )


# ---------------------------------------------------------------------------
# Legacy endpoints (plural /merchants/) — kept for backward compat
# ---------------------------------------------------------------------------


@router.get("/merchants/{merchant_id}", response_model=InternalMerchantConfigResponse)
async def internal_get_merchant_config(
    merchant_id: UUID,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> InternalMerchantConfigResponse:
    """Full config by merchant_id. Prefer GET /internal/merchant/{id}/config."""
    user = await user_service.get_user_by_id(db, merchant_id)
    _require_merchant(user, merchant_id)
    return _build_config(user, merchant_id)


@router.get("/merchants/{merchant_id}/limits", response_model=InternalMerchantLimitsResponse)
async def internal_get_merchant_limits(
    merchant_id: UUID,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> InternalMerchantLimitsResponse:
    """Limits only."""
    user = await user_service.get_user_by_id(db, merchant_id)
    _require_merchant(user, merchant_id)
    limits = user.merchant_limits
    if not limits:
        return InternalMerchantLimitsResponse(
            merchant_id=merchant_id,
            max_txs_per_day=None,
            max_pending_invoices=None,
            max_single_tx_amount_usd=None,
        )
    return InternalMerchantLimitsResponse(
        merchant_id=merchant_id,
        max_txs_per_day=limits.max_txs_per_day,
        max_pending_invoices=limits.max_pending_invoices,
        max_single_tx_amount_usd=limits.max_single_tx_amount_usd,
    )


@router.get("/users/{firebase_uid}", response_model=InternalUserConfigResponse)
async def internal_get_user_config(
    firebase_uid: str,
    _: None = Depends(verify_internal_secret),
    db: AsyncSession = Depends(get_db),
) -> InternalUserConfigResponse:
    """Resolve firebase_uid → merchant_id + config. Used by Gateway for bootstrap lookup."""
    user = await user_service.get_user_by_firebase_uid(db, firebase_uid)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    cfg = _build_config(user, user.id)
    return InternalUserConfigResponse(
        merchant_id=user.id,
        status=cfg.status,
        allowed_chains=cfg.allowed_chains,
        allowed_assets=cfg.allowed_assets,
        default_chain=cfg.default_chain,
        wallets=cfg.wallets,
        webhook_url=cfg.webhook_url,
        webhook_enabled=cfg.webhook_enabled,
        webhook_secret=cfg.webhook_secret,
        limits=cfg.limits,
    )
