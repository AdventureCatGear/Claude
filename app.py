#!/usr/bin/env python3
"""
Secure Token Transfer — CLI Tool

Usage:
  python app.py verify  --chain SOL --token SOL --from ADDR --to ADDR --amount 1.5 [--memo NOTE]
  python app.py dual    --chain SOL --token SOL --from ADDR --to ADDR --amount 1.5 \\
                        --r-chain SOL --r-token SOL --r-from ADDR --r-to ADDR --r-amount 1.5
  python app.py chains

Zero external dependencies.
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_transfer.core import TransferRequest, verify_transfer
from secure_transfer.confirm import dual_confirm
from secure_transfer.chains import SUPPORTED_CHAINS


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[38;5;203m"
    GREEN   = "\033[38;5;48m"
    YELLOW  = "\033[38;5;221m"
    PURPLE  = "\033[38;5;141m"
    CYAN    = "\033[38;5;80m"
    WHITE   = "\033[38;5;255m"
    GRAY    = "\033[38;5;243m"
    BG_RED  = "\033[48;5;52m"
    BG_GRN  = "\033[48;5;22m"
    BG_PUR  = "\033[48;5;54m"


def W():
    return min(shutil.get_terminal_size((80, 24)).columns, 90)


def hr(char="─"):
    print(f"{C.GRAY}{char * W()}{C.RESET}")


def center(text, raw_len=None):
    w = W()
    pad_len = raw_len if raw_len is not None else len(text)
    print(" " * max(0, (w - pad_len) // 2) + text)


def box(lines, border=C.PURPLE):
    w = W() - 4
    print(f"{border}  ┌{'─' * (w + 2)}┐{C.RESET}")
    for line, raw_len in lines:
        pad = w - raw_len
        print(f"{border}  │ {C.RESET}{line}{' ' * max(0, pad)}{border} │{C.RESET}")
    print(f"{border}  └{'─' * (w + 2)}┘{C.RESET}")


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def render_banner():
    w = W()
    print()
    hr("━")
    print()
    center(f"{C.BOLD}{C.PURPLE}  SECURE TOKEN TRANSFER  {C.RESET}", 24)
    center(f"{C.DIM}Verify every detail before you send{C.RESET}", 35)
    print()
    # Trust indicators
    trust = f"{C.GREEN}●{C.RESET} {C.DIM}Client-Side{C.RESET}    {C.GREEN}●{C.RESET} {C.DIM}No Data Stored{C.RESET}    {C.GREEN}●{C.RESET} {C.DIM}SHA-256{C.RESET}"
    center(trust, 50)
    print()
    hr("━")


def render_result(result, req):
    print()

    if result.valid:
        center(f"{C.BOLD}{C.GREEN}  READY TO SEND  {C.RESET}", 15)
    else:
        center(f"{C.BOLD}{C.RED}  BLOCKED  {C.RESET}", 9)
    print()

    fields = [
        ("Chain",  req.chain),
        ("Token",  req.token),
        ("Amount", req.amount),
        ("From",   req.sender_address),
        ("To",     req.recipient_address),
    ]
    if req.memo:
        fields.append(("Memo", req.memo))

    lines = []
    for label, value in fields:
        lbl = f"{C.GRAY}{label:>8}{C.RESET}"
        val = f"{C.WHITE}{value}{C.RESET}"
        lines.append((f"{lbl}  {C.DIM}:{C.RESET}  {val}", 8 + 5 + len(value)))
    box(lines)

    if result.issues:
        print()
        for issue in result.issues:
            if issue.severity.value == "ERROR":
                print(f"  {C.RED}  ✗ ERROR  {C.RESET}{C.RED}{issue.field_name}: {issue.message}{C.RESET}")
            else:
                print(f"  {C.YELLOW}  ⚠ WARN   {C.RESET}{C.YELLOW}{issue.field_name}: {issue.message}{C.RESET}")
    else:
        print(f"\n  {C.GREEN}  ✓ No issues found. Transfer looks good.{C.RESET}")

    print()
    fp = result.fingerprint
    hr("─")
    print()
    center(f"{C.DIM}Fingerprint{C.RESET}", 11)
    center(f"{C.BOLD}{C.PURPLE}{fp}{C.RESET}", len(fp))
    print()
    center(f"{C.DIM}Share with recipient to confirm details match{C.RESET}", 46)
    print()
    hr("━")
    print()


def render_dual(dual):
    print()

    if dual.confirmed:
        center(f"{C.BOLD}{C.GREEN}  CONFIRMED — SAFE TO EXECUTE  {C.RESET}", 29)
    else:
        center(f"{C.BOLD}{C.RED}  REJECTED — DO NOT SEND  {C.RESET}", 24)
    print()

    s_ok = f"{C.GREEN}VALID{C.RESET}" if dual.sender_result.valid else f"{C.RED}INVALID{C.RESET}"
    r_ok = f"{C.GREEN}VALID{C.RESET}" if dual.receiver_result.valid else f"{C.RED}INVALID{C.RESET}"
    fp_m = f"{C.GREEN}MATCH{C.RESET}" if dual.fingerprints_match else f"{C.RED}MISMATCH{C.RESET}"

    sfp = dual.sender_result.fingerprint
    rfp = dual.receiver_result.fingerprint

    lines = [
        (f"{C.GRAY}    Sender{C.RESET}  {C.DIM}:{C.RESET}  {s_ok}", 20),
        (f"{C.GRAY}  Receiver{C.RESET}  {C.DIM}:{C.RESET}  {r_ok}", 22),
        (f"{C.GRAY}        FP{C.RESET}  {C.DIM}:{C.RESET}  {fp_m}", 20),
        ("", 0),
        (f"{C.GRAY} Sender FP{C.RESET}  {C.DIM}:{C.RESET}  {C.PURPLE}{sfp}{C.RESET}", 16 + len(sfp)),
        (f"{C.GRAY}  Recvr FP{C.RESET}  {C.DIM}:{C.RESET}  {C.PURPLE}{rfp}{C.RESET}", 16 + len(rfp)),
    ]
    box(lines)

    all_issues = dual.sender_result.issues + dual.receiver_result.issues
    if all_issues:
        print()
        for issue in all_issues:
            sev = issue.severity.value
            if sev == "ERROR":
                print(f"  {C.RED}  ✗ ERROR  {issue.field_name}: {issue.message}{C.RESET}")
            else:
                print(f"  {C.YELLOW}  ⚠ WARN   {issue.field_name}: {issue.message}{C.RESET}")

    print()
    hr("━")
    print()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_verify(args):
    render_banner()
    req = TransferRequest(
        chain=args.chain.upper(),
        token=(args.token or args.chain).upper(),
        sender_address=args.sender,
        recipient_address=args.to,
        amount=args.amount,
        memo=args.memo,
    )
    result = verify_transfer(req)
    render_result(result, req)
    return 0 if result.valid else 1


def cmd_dual(args):
    render_banner()
    s_req = TransferRequest(
        chain=args.chain.upper(),
        token=(args.token or args.chain).upper(),
        sender_address=args.sender,
        recipient_address=args.to,
        amount=args.amount,
        memo=args.memo,
    )
    r_req = TransferRequest(
        chain=(args.r_chain or args.chain).upper(),
        token=(args.r_token or args.r_chain or args.chain).upper(),
        sender_address=args.r_from,
        recipient_address=args.r_to,
        amount=args.r_amount,
        memo=args.r_memo,
    )
    result = dual_confirm(s_req, r_req)
    render_dual(result)
    return 0 if result.confirmed else 1


def cmd_chains(args):
    render_banner()
    print()
    center(f"{C.CYAN}{C.BOLD}Supported Chains{C.RESET}", 16)
    print()
    for chain in SUPPORTED_CHAINS:
        center(f"{C.PURPLE}●{C.RESET}  {C.BOLD}{C.WHITE}{chain}{C.RESET}", 5 + len(chain))
    print()
    hr("━")
    print()
    return 0


# ---------------------------------------------------------------------------
# Arg parser
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="app.py",
        description="Secure Token Transfer — verify before you send",
    )
    sub = p.add_subparsers(dest="command")

    # verify
    v = sub.add_parser("verify", help="Verify a single transfer")
    v.add_argument("--chain", "-c", required=True, help="Blockchain (SOL, BTC, ETH, SUI)")
    v.add_argument("--token", "-t", help="Token symbol (defaults to chain)")
    v.add_argument("--from", dest="sender", required=True, help="Sender wallet address")
    v.add_argument("--to", required=True, help="Recipient wallet address")
    v.add_argument("--amount", "-a", required=True, help="Amount to send")
    v.add_argument("--memo", "-m", help="Optional memo / tag")

    # dual
    d = sub.add_parser("dual", help="Dual-party confirmation")
    d.add_argument("--chain", "-c", required=True)
    d.add_argument("--token", "-t")
    d.add_argument("--from", dest="sender", required=True)
    d.add_argument("--to", required=True)
    d.add_argument("--amount", "-a", required=True)
    d.add_argument("--memo", "-m")
    d.add_argument("--r-chain", help="Receiver's chain (defaults to sender's)")
    d.add_argument("--r-token")
    d.add_argument("--r-from", required=True, help="Receiver says sender is...")
    d.add_argument("--r-to", required=True, help="Receiver says recipient is...")
    d.add_argument("--r-amount", required=True)
    d.add_argument("--r-memo")

    # chains
    sub.add_parser("chains", help="List supported chains")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "dual":
        sys.exit(cmd_dual(args))
    elif args.command == "chains":
        sys.exit(cmd_chains(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
