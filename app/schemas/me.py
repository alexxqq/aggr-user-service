"""GET /me full response and related."""

from pydantic import BaseModel

from app.schemas.features import MerchantFeatureFlagsResponse
from app.schemas.limits import MerchantLimitsResponse
from app.schemas.settings import MerchantSettingsResponse
from app.schemas.user import UserProfileResponse
from app.schemas.wallet import WalletResponse
from app.schemas.webhook import WebhookConfigResponse


class MeResponse(BaseModel):
    """Full user profile with settings, wallets, webhook, limits, features (GET /me)."""

    profile: UserProfileResponse
    merchant_settings: MerchantSettingsResponse | None
    wallets: list[WalletResponse]
    webhook_config: WebhookConfigResponse | None
    limits: MerchantLimitsResponse | None = None
    feature_flags: MerchantFeatureFlagsResponse | None = None
