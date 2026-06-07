"""Unit tests for wallet_service business logic."""

import uuid
from decimal import Decimal

import pytest

from app.schemas.wallet import WalletCreate, WalletUpdate


def test_wallet_create_schema():
    """WalletCreate requires chain and address."""
    w = WalletCreate(chain="ethereum", address="0xABC123", label="main", is_default=True)
    assert w.chain == "ethereum"
    assert w.address == "0xABC123"
    assert w.is_default is True


def test_wallet_update_schema_optional_fields():
    """WalletUpdate all fields are optional."""
    u = WalletUpdate()
    assert u.label is None
    assert u.is_default is None

    u2 = WalletUpdate(label="renamed")
    assert u2.label == "renamed"
    assert u2.is_default is None

    u3 = WalletUpdate(is_default=True)
    assert u3.is_default is True
    assert u3.label is None


def test_wallet_update_label_max_length():
    """WalletUpdate enforces max_length on label."""
    with pytest.raises(Exception):
        WalletUpdate(label="x" * 256)
