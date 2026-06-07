"""Tests for limits schema."""

from decimal import Decimal

import pytest

from app.schemas.limits import MerchantLimitsUpdate


def test_limits_update_fields():
    """MerchantLimitsUpdate only updates provided fields."""
    payload = MerchantLimitsUpdate(max_txs_per_day=50)
    assert payload.max_txs_per_day == 50
    assert payload.max_pending_invoices is None
    assert payload.max_single_tx_amount_usd is None

    payload2 = MerchantLimitsUpdate(max_single_tx_amount_usd=Decimal("1000.00"))
    assert payload2.max_single_tx_amount_usd == Decimal("1000.00")
