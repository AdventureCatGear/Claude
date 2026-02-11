"""
Dual-party confirmation flow.

Both sender and receiver independently verify the same TransferRequest.
If both sides produce the same fingerprint AND no errors exist, the
transfer is confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from secure_transfer.core import TransferRequest, VerificationResult, verify_transfer


@dataclass
class ConfirmationResult:
    sender_result: VerificationResult
    receiver_result: VerificationResult
    fingerprints_match: bool
    confirmed: bool
    summary: str


def dual_confirm(
    sender_req: TransferRequest,
    receiver_req: TransferRequest,
) -> ConfirmationResult:
    """
    Both parties submit their view of the transfer.

    The transfer is only confirmed when:
      1. Both pass validation (no ERRORs).
      2. Both produce the same fingerprint (details match exactly).
    """
    s_result = verify_transfer(sender_req)
    r_result = verify_transfer(receiver_req)

    fp_match = s_result.fingerprint == r_result.fingerprint
    confirmed = s_result.valid and r_result.valid and fp_match

    summary = _build_dual_summary(s_result, r_result, fp_match, confirmed)

    return ConfirmationResult(
        sender_result=s_result,
        receiver_result=r_result,
        fingerprints_match=fp_match,
        confirmed=confirmed,
        summary=summary,
    )


def _build_dual_summary(
    s: VerificationResult,
    r: VerificationResult,
    fp_match: bool,
    confirmed: bool,
) -> str:
    status = "CONFIRMED" if confirmed else "REJECTED"
    lines = [
        "=" * 56,
        f"  DUAL-PARTY CONFIRMATION — {status}",
        "=" * 56,
        f"  Sender   verification : {'PASS' if s.valid else 'FAIL'}",
        f"  Receiver verification : {'PASS' if r.valid else 'FAIL'}",
        f"  Fingerprint match     : {'YES' if fp_match else 'NO — MISMATCH'}",
        "-" * 56,
    ]

    if not fp_match:
        lines.append(f"  Sender   fingerprint  : {s.fingerprint}")
        lines.append(f"  Receiver fingerprint  : {r.fingerprint}")
        lines.append("  The two parties have DIFFERENT transfer details.")
        lines.append("  Reconcile before proceeding.")
    elif not confirmed:
        lines.append("  Fingerprints match but validation errors exist.")
        all_issues = s.issues + r.issues
        for issue in all_issues:
            tag = issue.severity.value
            lines.append(f"  [{tag}] {issue.field_name}: {issue.message}")
    else:
        lines.append(f"  Fingerprint           : {s.fingerprint}")
        lines.append("  Both parties agree. Transfer is safe to execute.")

    lines.append("=" * 56)
    return "\n".join(lines)
