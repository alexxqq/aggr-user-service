"""Internal API response schemas (service-to-service, by merchant_id or firebase_uid)."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.user import UserStatus


class InternalWalletItem(BaseModel):
    """Minimal wallet for internal API."""

    chain: str
    address: str
    label: str | None
    is_default: bool


class InternalLimitsItem(BaseModel):
    """Limits for internal API."""

    max_txs_per_day: int | None
    max_pending_invoices: int | None
    max_single_tx_amount_usd: Decimal | None


class InternalUserConfigResponse(BaseModel):
    """Legacy: config by firebase_uid (GET /internal/users/{firebase_uid})."""

    merchant_id: UUID
    status: UserStatus
    allowed_chains: list[str]
    allowed_assets: list[str]
    default_chain: str | None
    wallets: list[InternalWalletItem]
    webhook_url: str | None
    webhook_enabled: bool = True
    webhook_secret: str | None = None
    limits: InternalLimitsItem | None = None


class InternalMerchantConfigResponse(BaseModel):
    """Full config by merchant_id (GET /internal/merchants/{merchant_id})."""

    merchant_id: UUID
    status: UserStatus
    allowed_chains: list[str]
    allowed_assets: list[str]
    default_chain: str | None
    wallets: list[InternalWalletItem]
    webhook_url: str | None
    webhook_enabled: bool = True
    webhook_secret: str | None = None
    limits: InternalLimitsItem | None = None


class InternalMerchantLimitsResponse(BaseModel):
    """Limits only (GET /internal/merchants/{merchant_id}/limits)."""

    merchant_id: UUID
    max_txs_per_day: int | None
    max_pending_invoices: int | None
    max_single_tx_amount_usd: Decimal | None


class InternalMerchantCapabilitiesResponse(BaseModel):
    """Capabilities for a merchant (GET /internal/merchant/{merchant_id}/capabilities)."""

    merchant_id: UUID
    status: UserStatus
    is_active: bool
    allowed_chains: list[str]
    allowed_assets: list[str]
    default_chain: str | None


class MerchantInitRequest(BaseModel):
    """Payload for POST /internal/merchant/init (called by API Gateway after Firebase verification)."""

    firebase_uid: str
    email: str | None = None
    display_name: str | None = None


class MerchantInitResponse(BaseModel):
    """Response for POST /internal/merchant/init."""

    merchant_id: UUID
    firebase_uid: str
    status: UserStatus
    created: bool  # True if newly created, False if already existed
