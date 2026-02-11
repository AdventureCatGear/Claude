"""
Core transfer verification engine.

Validates a TransferRequest against chain-specific rules and returns a
structured VerificationResult that both parties can review.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Severity(Enum):
    ERROR = "ERROR"      # Transfer MUST NOT proceed
    WARNING = "WARNING"  # Transfer CAN proceed, but review recommended


@dataclass
class Issue:
    severity: Severity
    field_name: str
    message: str


@dataclass
class TransferRequest:
    """All fields the sender must provide before a transfer is verified."""
    chain: str                       # e.g. "SOL", "BTC", "ETH", "SUI"
    token: str                       # e.g. "SOL", "BTC", "USDC", "SUI"
    sender_address: str
    recipient_address: str
    amount: str                      # always passed as string to preserve precision
    memo: Optional[str] = None       # optional on-chain memo / tag
    decimals: Optional[int] = None   # override token decimals if known


@dataclass
class VerificationResult:
    """Returned by verify_transfer.  Both parties inspect this."""
    valid: bool
    issues: List[Issue] = field(default_factory=list)
    transfer_summary: str = ""
    fingerprint: str = ""            # deterministic hash of the request

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]


# ---------------------------------------------------------------------------
# Verification pipeline
# ---------------------------------------------------------------------------

def verify_transfer(req: TransferRequest) -> VerificationResult:
    """Run all verification checks and return a result."""
    from secure_transfer.chains import get_validator  # lazy to avoid circular

    issues: List[Issue] = []

    # 1. Basic field presence
    _check_required_fields(req, issues)
    if any(i.severity is Severity.ERROR for i in issues):
        return _build_result(req, issues)

    # 2. Normalise chain name
    req.chain = req.chain.strip().upper()
    req.token = req.token.strip().upper()

    # 3. Chain support check
    validator = get_validator(req.chain)
    if validator is None:
        issues.append(Issue(Severity.ERROR, "chain",
                            f"Unsupported chain: {req.chain}"))
        return _build_result(req, issues)

    # 4. Address validation (chain-specific)
    validator.validate_address(req.sender_address, "sender_address", issues)
    validator.validate_address(req.recipient_address, "recipient_address", issues)

    # 5. Self-send check
    if req.sender_address.strip() == req.recipient_address.strip():
        issues.append(Issue(Severity.ERROR, "recipient_address",
                            "Sender and recipient addresses are identical"))

    # 6. Amount validation
    _check_amount(req, validator, issues)

    # 7. Memo validation (chain-specific)
    if req.memo is not None:
        validator.validate_memo(req.memo, issues)

    return _build_result(req, issues)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_REQUIRED = ("chain", "token", "sender_address", "recipient_address", "amount")


def _check_required_fields(req: TransferRequest, issues: List[Issue]) -> None:
    for fname in _REQUIRED:
        val = getattr(req, fname, None)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            issues.append(Issue(Severity.ERROR, fname,
                                f"Required field '{fname}' is missing or empty"))


def _check_amount(req: TransferRequest, validator, issues: List[Issue]) -> None:
    try:
        amount = Decimal(req.amount)
    except (InvalidOperation, ValueError):
        issues.append(Issue(Severity.ERROR, "amount",
                            f"Invalid amount format: '{req.amount}'"))
        return

    if amount <= 0:
        issues.append(Issue(Severity.ERROR, "amount",
                            "Amount must be greater than zero"))
        return

    # Decimal precision check
    max_decimals = req.decimals if req.decimals is not None else validator.default_decimals
    _, _, exponent = amount.as_tuple()
    actual_decimals = -exponent if exponent < 0 else 0
    if actual_decimals > max_decimals:
        issues.append(Issue(Severity.ERROR, "amount",
                            f"Amount has {actual_decimals} decimal places; "
                            f"max for {req.token} on {req.chain} is {max_decimals}"))

    # Dust warning
    dust = validator.dust_threshold
    if dust is not None and amount < dust:
        issues.append(Issue(Severity.WARNING, "amount",
                            f"Amount {req.amount} is below the dust threshold "
                            f"({dust}) for {req.chain}"))

    # Large-transfer warning
    whale = validator.whale_threshold
    if whale is not None and amount >= whale:
        issues.append(Issue(Severity.WARNING, "amount",
                            f"Large transfer detected ({req.amount} {req.token}). "
                            f"Double-check recipient address."))


def _fingerprint(req: TransferRequest) -> str:
    """Deterministic SHA-256 fingerprint so both parties can compare."""
    payload = "|".join([
        req.chain, req.token,
        req.sender_address.strip(),
        req.recipient_address.strip(),
        req.amount.strip(),
        req.memo or "",
    ])
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _build_result(req: TransferRequest, issues: List[Issue]) -> VerificationResult:
    has_errors = any(i.severity is Severity.ERROR for i in issues)
    fp = _fingerprint(req)
    summary = _format_summary(req, issues, fp)
    return VerificationResult(
        valid=not has_errors,
        issues=issues,
        transfer_summary=summary,
        fingerprint=fp,
    )


def _format_summary(req: TransferRequest, issues: List[Issue], fp: str) -> str:
    """Human-readable transfer receipt."""
    status = "BLOCKED" if any(i.severity is Severity.ERROR for i in issues) else "READY"
    lines = [
        "=" * 56,
        f"  TRANSFER VERIFICATION — {status}",
        "=" * 56,
        f"  Chain       : {req.chain}",
        f"  Token       : {req.token}",
        f"  Amount      : {req.amount}",
        f"  From        : {req.sender_address}",
        f"  To          : {req.recipient_address}",
    ]
    if req.memo:
        lines.append(f"  Memo        : {req.memo}")
    lines.append(f"  Fingerprint : {fp}")
    lines.append("-" * 56)

    if issues:
        for issue in issues:
            tag = issue.severity.value
            lines.append(f"  [{tag}] {issue.field_name}: {issue.message}")
    else:
        lines.append("  No issues found.")
    lines.append("=" * 56)
    return "\n".join(lines)
