"""
Comprehensive tests for the secure token transfer verification tool.

Run:  python -m pytest tests/ -v
"""

import pytest

from secure_transfer.core import (
    Issue,
    Severity,
    TransferRequest,
    VerificationResult,
    verify_transfer,
)
from secure_transfer.confirm import dual_confirm
from secure_transfer.chains import SUPPORTED_CHAINS, get_validator, register_chain, ChainValidator


# ---------------------------------------------------------------------------
# Helpers — realistic test addresses
# ---------------------------------------------------------------------------

# Solana: 44-char base-58 (no 0, O, I, l)
SOL_ADDR_A = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
SOL_ADDR_B = "6Hfz5ausGMBCWE8UqGFcBY1QXBV9JHKJMtxGA9ko2irg"

# Bitcoin: Bech32 (native segwit)
BTC_ADDR_A = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
BTC_ADDR_B = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"

# Ethereum: 0x + 40 hex
ETH_ADDR_A = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
ETH_ADDR_B = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

# Sui: 0x + 64 hex (32 bytes)
SUI_ADDR_A = "0x" + "a1" * 32  # 0x + 64 hex chars
SUI_ADDR_B = "0x" + "b2" * 32


# ---------------------------------------------------------------------------
# Test: supported chains
# ---------------------------------------------------------------------------

class TestSupportedChains:
    def test_expected_chains_present(self):
        for chain in ("SOL", "BTC", "ETH", "SUI"):
            assert chain in SUPPORTED_CHAINS

    def test_get_validator_returns_instance(self):
        for chain in SUPPORTED_CHAINS:
            assert get_validator(chain) is not None

    def test_unknown_chain_returns_none(self):
        assert get_validator("DOGE") is None


# ---------------------------------------------------------------------------
# Test: Solana validation
# ---------------------------------------------------------------------------

class TestSolana:
    def _make(self, **overrides):
        defaults = dict(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="1.5",
        )
        defaults.update(overrides)
        return TransferRequest(**defaults)

    def test_valid_transfer(self):
        r = verify_transfer(self._make())
        assert r.valid
        assert len(r.errors) == 0

    def test_invalid_sender_address(self):
        r = verify_transfer(self._make(sender_address="0xinvalid"))
        assert not r.valid
        assert any("sender_address" in i.field_name for i in r.errors)

    def test_invalid_recipient_address(self):
        r = verify_transfer(self._make(recipient_address="bad!!!"))
        assert not r.valid

    def test_self_send_blocked(self):
        r = verify_transfer(self._make(recipient_address=SOL_ADDR_A))
        assert not r.valid
        assert any("identical" in i.message for i in r.errors)

    def test_dust_warning(self):
        r = verify_transfer(self._make(amount="0.0000001"))
        assert r.valid  # warning, not error
        assert len(r.warnings) > 0
        assert any("dust" in w.message for w in r.warnings)

    def test_whale_warning(self):
        r = verify_transfer(self._make(amount="50000"))
        assert r.valid
        assert any("Large" in w.message for w in r.warnings)

    def test_excessive_decimals(self):
        r = verify_transfer(self._make(amount="1.1234567890"))  # >9 decimals
        assert not r.valid
        assert any("decimal" in i.message for i in r.errors)


# ---------------------------------------------------------------------------
# Test: Bitcoin validation
# ---------------------------------------------------------------------------

class TestBitcoin:
    def _make(self, **overrides):
        defaults = dict(
            chain="BTC", token="BTC",
            sender_address=BTC_ADDR_A, recipient_address=BTC_ADDR_B,
            amount="0.005",
        )
        defaults.update(overrides)
        return TransferRequest(**defaults)

    def test_valid_bech32(self):
        r = verify_transfer(self._make())
        assert r.valid

    def test_valid_legacy_p2pkh(self):
        # Starts with 1, 25-34 chars
        addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        r = verify_transfer(self._make(sender_address=addr))
        assert r.valid

    def test_valid_p2sh(self):
        addr = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        r = verify_transfer(self._make(sender_address=addr))
        assert r.valid

    def test_invalid_btc_address(self):
        r = verify_transfer(self._make(sender_address="notabitcoinaddress"))
        assert not r.valid

    def test_dust_warning_btc(self):
        r = verify_transfer(self._make(amount="0.00000100"))
        assert r.valid
        assert any("dust" in w.message for w in r.warnings)


# ---------------------------------------------------------------------------
# Test: Ethereum validation
# ---------------------------------------------------------------------------

class TestEthereum:
    def _make(self, **overrides):
        defaults = dict(
            chain="ETH", token="ETH",
            sender_address=ETH_ADDR_A, recipient_address=ETH_ADDR_B,
            amount="0.5",
        )
        defaults.update(overrides)
        return TransferRequest(**defaults)

    def test_valid_transfer(self):
        r = verify_transfer(self._make())
        assert r.valid

    def test_lowercase_address_valid(self):
        r = verify_transfer(self._make(
            sender_address="0x32be343b94f860124dc4fee278fdcbd38c102d88"))
        assert r.valid

    def test_invalid_eth_address(self):
        r = verify_transfer(self._make(sender_address="0xZZZZ"))
        assert not r.valid

    def test_too_many_decimals(self):
        # ETH has 18 decimals — 19 should fail
        r = verify_transfer(self._make(amount="0." + "1" * 19))
        assert not r.valid


# ---------------------------------------------------------------------------
# Test: Sui validation
# ---------------------------------------------------------------------------

class TestSui:
    def _make(self, **overrides):
        defaults = dict(
            chain="SUI", token="SUI",
            sender_address=SUI_ADDR_A, recipient_address=SUI_ADDR_B,
            amount="10",
        )
        defaults.update(overrides)
        return TransferRequest(**defaults)

    def test_valid_transfer(self):
        r = verify_transfer(self._make())
        assert r.valid

    def test_short_address(self):
        r = verify_transfer(self._make(sender_address="0xabc"))
        assert not r.valid

    def test_invalid_hex(self):
        r = verify_transfer(self._make(sender_address="0x" + "g" * 64))
        assert not r.valid


# ---------------------------------------------------------------------------
# Test: Amount edge cases
# ---------------------------------------------------------------------------

class TestAmountValidation:
    def test_zero_amount(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="0",
        )
        r = verify_transfer(req)
        assert not r.valid
        assert any("greater than zero" in i.message for i in r.errors)

    def test_negative_amount(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="-5",
        )
        r = verify_transfer(req)
        assert not r.valid

    def test_non_numeric_amount(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="abc",
        )
        r = verify_transfer(req)
        assert not r.valid
        assert any("Invalid amount" in i.message for i in r.errors)

    def test_decimal_override(self):
        req = TransferRequest(
            chain="SOL", token="USDC",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="10.123456",  # 6 decimals
            decimals=6,
        )
        r = verify_transfer(req)
        assert r.valid

    def test_decimal_override_exceeded(self):
        req = TransferRequest(
            chain="SOL", token="USDC",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="10.1234567",  # 7 decimals, limit is 6
            decimals=6,
        )
        r = verify_transfer(req)
        assert not r.valid


# ---------------------------------------------------------------------------
# Test: Required fields
# ---------------------------------------------------------------------------

class TestRequiredFields:
    def test_missing_chain(self):
        req = TransferRequest(
            chain="", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="1",
        )
        r = verify_transfer(req)
        assert not r.valid

    def test_missing_amount(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="",
        )
        r = verify_transfer(req)
        assert not r.valid

    def test_missing_recipient(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address="",
            amount="1",
        )
        r = verify_transfer(req)
        assert not r.valid


# ---------------------------------------------------------------------------
# Test: Unsupported chain
# ---------------------------------------------------------------------------

class TestUnsupportedChain:
    def test_unsupported_chain_error(self):
        req = TransferRequest(
            chain="DOGE", token="DOGE",
            sender_address="DFake", recipient_address="DFake2",
            amount="100",
        )
        r = verify_transfer(req)
        assert not r.valid
        assert any("Unsupported chain" in i.message for i in r.errors)


# ---------------------------------------------------------------------------
# Test: Fingerprint determinism
# ---------------------------------------------------------------------------

class TestFingerprint:
    def test_same_request_same_fingerprint(self):
        req1 = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="1.0",
        )
        req2 = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="1.0",
        )
        r1 = verify_transfer(req1)
        r2 = verify_transfer(req2)
        assert r1.fingerprint == r2.fingerprint

    def test_different_amount_different_fingerprint(self):
        req1 = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="1.0",
        )
        req2 = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="2.0",
        )
        r1 = verify_transfer(req1)
        r2 = verify_transfer(req2)
        assert r1.fingerprint != r2.fingerprint


# ---------------------------------------------------------------------------
# Test: Dual-party confirmation
# ---------------------------------------------------------------------------

class TestDualConfirm:
    def test_matching_requests_confirmed(self):
        req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="5",
        )
        # Both parties submit the same details
        result = dual_confirm(req, req)
        assert result.confirmed
        assert result.fingerprints_match

    def test_mismatched_amount_rejected(self):
        sender_req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="5",
        )
        receiver_req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address=SOL_ADDR_A, recipient_address=SOL_ADDR_B,
            amount="50",  # disagreement
        )
        result = dual_confirm(sender_req, receiver_req)
        assert not result.confirmed
        assert not result.fingerprints_match

    def test_mismatched_recipient_rejected(self):
        sender_req = TransferRequest(
            chain="ETH", token="ETH",
            sender_address=ETH_ADDR_A, recipient_address=ETH_ADDR_B,
            amount="1",
        )
        receiver_req = TransferRequest(
            chain="ETH", token="ETH",
            sender_address=ETH_ADDR_A,
            recipient_address="0x0000000000000000000000000000000000000001",
            amount="1",
        )
        result = dual_confirm(sender_req, receiver_req)
        assert not result.confirmed

    def test_invalid_sender_still_rejects(self):
        bad_req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address="INVALID", recipient_address=SOL_ADDR_B,
            amount="1",
        )
        good_req = TransferRequest(
            chain="SOL", token="SOL",
            sender_address="INVALID", recipient_address=SOL_ADDR_B,
            amount="1",
        )
        result = dual_confirm(bad_req, good_req)
        # Fingerprints match but validation fails
        assert result.fingerprints_match
        assert not result.confirmed


# ---------------------------------------------------------------------------
# Test: Transfer summary output
# ---------------------------------------------------------------------------

class TestTransferSummary:
    def test_summary_contains_key_fields(self):
        req = TransferRequest(
            chain="BTC", token="BTC",
            sender_address=BTC_ADDR_A, recipient_address=BTC_ADDR_B,
            amount="0.01", memo="invoice-42",
        )
        r = verify_transfer(req)
        assert "BTC" in r.transfer_summary
        assert "0.01" in r.transfer_summary
        assert BTC_ADDR_A in r.transfer_summary
        assert BTC_ADDR_B in r.transfer_summary
        assert "invoice-42" in r.transfer_summary
        assert r.fingerprint in r.transfer_summary

    def test_blocked_summary_on_error(self):
        req = TransferRequest(
            chain="BTC", token="BTC",
            sender_address="bad", recipient_address=BTC_ADDR_B,
            amount="1",
        )
        r = verify_transfer(req)
        assert "BLOCKED" in r.transfer_summary


# ---------------------------------------------------------------------------
# Test: Custom chain registration
# ---------------------------------------------------------------------------

class TestCustomChain:
    def test_register_and_use_custom_chain(self):
        from decimal import Decimal

        class DogeValidator(ChainValidator):
            chain = "DOGE"
            default_decimals = 8
            dust_threshold = Decimal("1")
            whale_threshold = None

            def validate_address(self, address, field, issues):
                if not address.startswith("D"):
                    issues.append(Issue(
                        Severity.ERROR, field,
                        "Dogecoin address must start with 'D'"))

        register_chain(DogeValidator())

        req = TransferRequest(
            chain="DOGE", token="DOGE",
            sender_address="DFakeSenderAddr12345678901234",
            recipient_address="DFakeRecipAddr12345678901234x",
            amount="1000",
        )
        r = verify_transfer(req)
        assert r.valid
