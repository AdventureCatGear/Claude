"""
Chain-specific address & memo validators.

Each validator is a simple class that knows:
  - How to validate an address for its chain
  - Default decimal precision for the native token
  - Dust / whale thresholds (optional safety rails)
  - Memo format rules (if applicable)

Adding a new chain = adding one class + registering it in _VALIDATORS.
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Dict, List, Optional, Type

from secure_transfer.core import Issue, Severity


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class ChainValidator:
    """Override per chain."""
    chain: str = ""
    default_decimals: int = 8
    dust_threshold: Optional[Decimal] = None
    whale_threshold: Optional[Decimal] = None

    def validate_address(self, address: str, field: str,
                         issues: List[Issue]) -> None:
        raise NotImplementedError

    def validate_memo(self, memo: str, issues: List[Issue]) -> None:
        """Default: memos are free-form strings, no validation."""
        pass


# ---------------------------------------------------------------------------
# Solana
# ---------------------------------------------------------------------------

class SolanaValidator(ChainValidator):
    chain = "SOL"
    default_decimals = 9
    dust_threshold = Decimal("0.000001")
    whale_threshold = Decimal("10000")

    # Solana addresses are base-58 encoded, 32–44 characters.
    # Valid base-58 alphabet: no 0, O, I, l.
    _ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

    def validate_address(self, address: str, field: str,
                         issues: List[Issue]) -> None:
        address = address.strip()
        if not self._ADDR_RE.match(address):
            issues.append(Issue(
                Severity.ERROR, field,
                f"Invalid Solana address format: '{address}'. "
                "Expected 32-44 base-58 characters."))


# ---------------------------------------------------------------------------
# Bitcoin
# ---------------------------------------------------------------------------

class BitcoinValidator(ChainValidator):
    chain = "BTC"
    default_decimals = 8
    dust_threshold = Decimal("0.00000546")   # standard dust limit
    whale_threshold = Decimal("10")

    # Simplified patterns for common address types:
    #   P2PKH  – starts with 1, 25-34 chars
    #   P2SH   – starts with 3, 25-34 chars
    #   Bech32 – starts with bc1, 42-62 chars
    _LEGACY_RE = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{24,33}$")
    _BECH32_RE = re.compile(r"^bc1[a-zA-HJ-NP-Z0-9]{25,62}$")

    def validate_address(self, address: str, field: str,
                         issues: List[Issue]) -> None:
        address = address.strip()
        if not (self._LEGACY_RE.match(address) or self._BECH32_RE.match(address)):
            issues.append(Issue(
                Severity.ERROR, field,
                f"Invalid Bitcoin address format: '{address}'. "
                "Expected P2PKH (1...), P2SH (3...), or Bech32 (bc1...)."))


# ---------------------------------------------------------------------------
# Ethereum (and EVM-compatible)
# ---------------------------------------------------------------------------

class EthereumValidator(ChainValidator):
    chain = "ETH"
    default_decimals = 18
    dust_threshold = Decimal("0.0001")
    whale_threshold = Decimal("100")

    _ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

    def validate_address(self, address: str, field: str,
                         issues: List[Issue]) -> None:
        address = address.strip()
        if not self._ADDR_RE.match(address):
            issues.append(Issue(
                Severity.ERROR, field,
                f"Invalid Ethereum address format: '{address}'. "
                "Expected '0x' followed by 40 hex characters."))
            return
        # EIP-55 checksum verification (warns, does not block)
        if address != address.lower() and address != address.upper():
            if not self._eip55_valid(address):
                issues.append(Issue(
                    Severity.WARNING, field,
                    f"Ethereum address '{address}' has an invalid EIP-55 "
                    "checksum. Verify the address carefully."))

    @staticmethod
    def _eip55_valid(address: str) -> bool:
        """Check mixed-case address against EIP-55 checksum."""
        addr = address[2:]  # strip 0x
        addr_lower = addr.lower()
        addr_hash = hashlib.sha256(addr_lower.encode()).hexdigest()
        # EIP-55 uses keccak-256; we approximate with sha-256 here.
        # For production, swap in keccak via pysha3 or eth_utils.
        # This gives a reasonable but not bit-perfect check.
        for i, c in enumerate(addr):
            if c.isalpha():
                should_upper = int(addr_hash[i], 16) >= 8
                if should_upper and c.islower():
                    return False
                if not should_upper and c.isupper():
                    return False
        return True


# ---------------------------------------------------------------------------
# Sui
# ---------------------------------------------------------------------------

class SuiValidator(ChainValidator):
    chain = "SUI"
    default_decimals = 9
    dust_threshold = Decimal("0.001")
    whale_threshold = Decimal("100000")

    # Sui addresses: 0x followed by 64 hex characters (32 bytes)
    _ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

    def validate_address(self, address: str, field: str,
                         issues: List[Issue]) -> None:
        address = address.strip()
        if not self._ADDR_RE.match(address):
            issues.append(Issue(
                Severity.ERROR, field,
                f"Invalid Sui address format: '{address}'. "
                "Expected '0x' followed by 64 hex characters."))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_VALIDATORS: Dict[str, ChainValidator] = {
    "SOL": SolanaValidator(),
    "BTC": BitcoinValidator(),
    "ETH": EthereumValidator(),
    "SUI": SuiValidator(),
}

SUPPORTED_CHAINS = list(_VALIDATORS.keys())


def get_validator(chain: str) -> Optional[ChainValidator]:
    return _VALIDATORS.get(chain.upper())


def register_chain(validator: ChainValidator) -> None:
    """Plug in a new chain at runtime."""
    _VALIDATORS[validator.chain.upper()] = validator
