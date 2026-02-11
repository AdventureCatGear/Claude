"""
CLI entry point:  python -m secure_transfer

Walks the user through building a TransferRequest, verifies it, and
prints the result.
"""

from __future__ import annotations

import sys

from secure_transfer.chains import SUPPORTED_CHAINS
from secure_transfer.core import TransferRequest, verify_transfer


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val or default


def main() -> None:
    print("=" * 56)
    print("  Secure Token Transfer — Verification Tool")
    print(f"  Supported chains: {', '.join(SUPPORTED_CHAINS)}")
    print("=" * 56)

    chain = _prompt("Chain (e.g. SOL, BTC, ETH, SUI)").upper()
    token = _prompt("Token symbol", default=chain)
    sender = _prompt("Sender address")
    recipient = _prompt("Recipient address")
    amount = _prompt("Amount")
    memo = _prompt("Memo (optional, press Enter to skip)")

    req = TransferRequest(
        chain=chain,
        token=token,
        sender_address=sender,
        recipient_address=recipient,
        amount=amount,
        memo=memo or None,
    )

    result = verify_transfer(req)
    print()
    print(result.transfer_summary)

    if result.valid:
        print("\n  Share the fingerprint with the recipient to confirm.")
        print(f"  Fingerprint: {result.fingerprint}")
    else:
        print(f"\n  {len(result.errors)} error(s) found. Fix before sending.")

    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
