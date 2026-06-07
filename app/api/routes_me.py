"""Authenticated /v1/me endpoints.

Auth: API Gateway verifies Firebase token and forwards X-Merchant-Id (merchant UUID).
This service trusts that header — it does not call Firebase directly.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_merchant_id_from_header
from app.models import User
from app.schemas.features import MerchantFeatureFlagsResponse, MerchantFeatureFlagsUpdate
from app.schemas.limits import MerchantLimitsResponse, MerchantLimitsUpdate
from app.schemas.me import MeResponse
from app.schemas.settings import MerchantSettingsResponse, MerchantSettingsUpdate
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.schemas.wallet import WalletCreate, WalletResponse, WalletUpdate
from app.schemas.webhook import WebhookConfigResponse, WebhookConfigUpsert, WebhookRotateResponse
from app.services import features_service, limits_service, user_service, wallet_service

router = APIRouter(prefix="/v1/me", tags=["me"])


async def get_current_user(
    merchant_id: UUID = Depends(get_merchant_id_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Load merchant by UUID from X-Merchant-Id header. 404 if not found."""
    user = await user_service.get_user_by_id(db, merchant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found",
        )
    return user


def _me_response(user: User) -> MeResponse:
    """Build full MeResponse from a loaded User with relations."""
    profile = UserProfileResponse.model_validate(user)
    merchant_settings = (
        MerchantSettingsResponse.model_validate(user.merchant_settings)
        if user.merchant_settings
        else None
    )
    wallets = [WalletResponse.model_validate(w) for w in user.wallets]
    webhook_config = None
    if user.webhook_config:
        webhook_config = WebhookConfigResponse(
            id=user.webhook_config.id,
            user_id=user.webhook_config.user_id,
            webhook_url=user.webhook_config.webhook_url,
            is_enabled=user.webhook_config.is_enabled,
            created_at=user.webhook_config.created_at,
            updated_at=user.webhook_config.updated_at,
            secret=None,
        )
    limits = (
        MerchantLimitsResponse.model_validate(user.merchant_limits)
        if user.merchant_limits
        else None
    )
    feature_flags = (
        MerchantFeatureFlagsResponse.model_validate(user.merchant_feature_flags)
        if user.merchant_feature_flags
        else None
    )
    return MeResponse(
        profile=profile,
        merchant_settings=merchant_settings,
        wallets=wallets,
        webhook_config=webhook_config,
        limits=limits,
        feature_flags=feature_flags,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


@router.get("", response_model=MeResponse)
async def me_get(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """Return full merchant config (profile, settings, wallets, webhook, limits, features)."""
    return _me_response(current_user)


@router.patch("", response_model=UserProfileResponse)
async def me_patch(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update merchant profile (display_name)."""
    user = await user_service.update_profile(db, current_user.id, payload)
    await db.refresh(user)
    return UserProfileResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=MerchantSettingsResponse)
async def me_get_settings(
    current_user: User = Depends(get_current_user),
) -> MerchantSettingsResponse:
    """Return merchant settings."""
    if not current_user.merchant_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant settings not found",
        )
    return MerchantSettingsResponse.model_validate(current_user.merchant_settings)


@router.patch("/settings", response_model=MerchantSettingsResponse)
async def me_patch_settings(
    payload: MerchantSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MerchantSettingsResponse:
    """Update allowed_chains, allowed_assets, default_chain, timezone."""
    settings = await user_service.update_merchant_settings(db, current_user.id, payload)
    await db.refresh(settings)
    return MerchantSettingsResponse.model_validate(settings)


# ---------------------------------------------------------------------------
# Wallets
# ---------------------------------------------------------------------------


@router.get("/wallets", response_model=list[WalletResponse])
async def me_get_wallets(
    current_user: User = Depends(get_current_user),
) -> list[WalletResponse]:
    """Return list of payout wallets."""
    return [WalletResponse.model_validate(w) for w in current_user.wallets]


@router.post("/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def me_add_wallet(
    payload: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Add a payout wallet."""
    try:
        wallet = await wallet_service.add_wallet(
            db,
            current_user.id,
            chain=payload.chain,
            address=payload.address,
            label=payload.label,
            is_default=payload.is_default,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wallet with this chain and address already exists",
        )
    await db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


@router.patch("/wallets/{wallet_id}", response_model=WalletResponse)
async def me_patch_wallet(
    wallet_id: UUID,
    payload: WalletUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Update wallet label or default flag."""
    wallet = await wallet_service.update_wallet(db, wallet_id, current_user.id, payload)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )
    await db.refresh(wallet)
    return WalletResponse.model_validate(wallet)


@router.delete("/wallets/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def me_delete_wallet(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a payout wallet."""
    deleted = await wallet_service.delete_wallet(db, wallet_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------


@router.get("/webhook", response_model=WebhookConfigResponse)
async def me_get_webhook(
    current_user: User = Depends(get_current_user),
) -> WebhookConfigResponse:
    """Get webhook config (URL, enabled). Secret is never returned in GET."""
    if not current_user.webhook_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No webhook config. Use PUT /v1/me/webhook to create.",
        )
    w = current_user.webhook_config
    return WebhookConfigResponse(
        id=w.id,
        user_id=w.user_id,
        webhook_url=w.webhook_url,
        is_enabled=w.is_enabled,
        created_at=w.created_at,
        updated_at=w.updated_at,
        secret=None,
    )


@router.put("/webhook", response_model=WebhookConfigResponse)
async def me_put_webhook(
    payload: WebhookConfigUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookConfigResponse:
    """Create or update webhook config. Secret returned only on creation."""
    config, plain_secret = await user_service.upsert_webhook(
        db,
        current_user.id,
        webhook_url=payload.webhook_url,
        is_enabled=payload.is_enabled,
    )
    await db.refresh(config)
    return WebhookConfigResponse(
        id=config.id,
        user_id=config.user_id,
        webhook_url=config.webhook_url,
        is_enabled=config.is_enabled,
        created_at=config.created_at,
        updated_at=config.updated_at,
        secret=plain_secret,
    )


@router.post("/webhook/rotate", response_model=WebhookRotateResponse)
async def me_rotate_webhook(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookRotateResponse:
    """Rotate webhook secret. New secret returned once; store it for signing."""
    try:
        config, plain = await user_service.rotate_webhook_secret(db, current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No webhook config to rotate.",
        )
    return WebhookRotateResponse(
        secret=plain,
        webhook_url=config.webhook_url,
        is_enabled=config.is_enabled,
    )


# ---------------------------------------------------------------------------
# Limits (anti-abuse)
# ---------------------------------------------------------------------------


@router.get("/limits", response_model=MerchantLimitsResponse)
async def me_get_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MerchantLimitsResponse:
    """Get merchant limits."""
    limits = await limits_service.get_or_create_limits(db, current_user.id)
    return MerchantLimitsResponse.model_validate(limits)


@router.patch("/limits", response_model=MerchantLimitsResponse)
async def me_patch_limits(
    payload: MerchantLimitsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MerchantLimitsResponse:
    """Update merchant limits."""
    limits = await limits_service.update_limits(db, current_user.id, payload)
    await db.refresh(limits)
    return MerchantLimitsResponse.model_validate(limits)


# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------


@router.get("/features", response_model=MerchantFeatureFlagsResponse)
async def me_get_features(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MerchantFeatureFlagsResponse:
    """Get feature flags."""
    flags_row = await features_service.get_or_create_feature_flags(db, current_user.id)
    return MerchantFeatureFlagsResponse.model_validate(flags_row)


@router.patch("/features", response_model=MerchantFeatureFlagsResponse)
async def me_patch_features(
    payload: MerchantFeatureFlagsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MerchantFeatureFlagsResponse:
    """Update feature flags."""
    flags_row = await features_service.update_feature_flags(db, current_user.id, payload)
    await db.refresh(flags_row)
    return MerchantFeatureFlagsResponse.model_validate(flags_row)
