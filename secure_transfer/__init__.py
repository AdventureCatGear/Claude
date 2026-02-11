"""
Secure Token Transfer Verification Tool

A chain-agnostic verification layer that validates every field of a token
transfer before it is broadcast.  Designed so two parties (sender + receiver)
can independently confirm the transfer details match expectations.

Supported chains: SOL, BTC, ETH, SUI (extensible).
"""

from secure_transfer.core import TransferRequest, verify_transfer
from secure_transfer.chains import SUPPORTED_CHAINS

__all__ = ["TransferRequest", "verify_transfer", "SUPPORTED_CHAINS"]
