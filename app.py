#!/usr/bin/env python3
"""
Secure Token Transfer — Interactive Web UI

Zero external dependencies. Uses Python's built-in http.server.
Run:  python app.py
Open: http://localhost:8080
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Ensure the package is importable when running from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secure_transfer.core import TransferRequest, verify_transfer
from secure_transfer.confirm import dual_confirm
from secure_transfer.chains import SUPPORTED_CHAINS

PORT = 8080

# ---------------------------------------------------------------------------
# HTML / CSS / JS — the entire frontend lives here
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Secure Token Transfer</title>
<style>
  :root {
    --bg: #0f1117;
    --card: #1a1d27;
    --border: #2a2d3a;
    --accent: #6c5ce7;
    --accent-light: #a29bfe;
    --green: #00b894;
    --red: #e17055;
    --orange: #fdcb6e;
    --text: #dfe6e9;
    --text-dim: #636e72;
    --radius: 12px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 20px;
  }
  .container { max-width: 720px; margin: 0 auto; }

  /* Header */
  .header {
    text-align: center;
    padding: 30px 0 20px;
  }
  .header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.5px;
  }
  .header h1 .lock { font-size: 1.3rem; margin-right: 8px; }
  .header p { color: var(--text-dim); font-size: 0.8rem; margin-top: 6px; }

  /* Chain pills */
  .chains {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin: 20px 0 30px;
    flex-wrap: wrap;
  }
  .chain-pill {
    padding: 8px 18px;
    border-radius: 20px;
    border: 2px solid var(--border);
    background: transparent;
    color: var(--text-dim);
    font-family: inherit;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .chain-pill:hover { border-color: var(--accent-light); color: var(--text); }
  .chain-pill.active {
    border-color: var(--accent);
    background: var(--accent);
    color: #fff;
  }

  /* Card */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    margin-bottom: 16px;
  }
  .card-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    margin-bottom: 16px;
  }

  /* Form fields */
  .field { margin-bottom: 14px; }
  .field label {
    display: block;
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-bottom: 5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .field input, .field select {
    width: 100%;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: inherit;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .field input:focus, .field select:focus {
    border-color: var(--accent);
  }
  .field input.error { border-color: var(--red); }
  .field input.valid { border-color: var(--green); }
  .field .hint {
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-top: 3px;
  }

  /* Two columns */
  .row { display: flex; gap: 12px; }
  .row .field { flex: 1; }

  /* Button */
  .btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .btn-verify {
    background: var(--accent);
    color: #fff;
  }
  .btn-verify:hover { background: var(--accent-light); }
  .btn-verify:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-reset {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-dim);
    margin-top: 8px;
    font-size: 0.8rem;
    padding: 10px;
  }
  .btn-reset:hover { border-color: var(--text-dim); color: var(--text); }

  /* Result panel */
  .result { display: none; }
  .result.show { display: block; }
  .result-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }
  .status-badge {
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .status-badge.ready { background: var(--green); color: #fff; }
  .status-badge.blocked { background: var(--red); color: #fff; }

  /* Summary table */
  .summary-table { width: 100%; }
  .summary-table tr { border-bottom: 1px solid var(--border); }
  .summary-table tr:last-child { border-bottom: none; }
  .summary-table td {
    padding: 8px 0;
    font-size: 0.85rem;
  }
  .summary-table td:first-child {
    color: var(--text-dim);
    width: 120px;
    white-space: nowrap;
  }
  .summary-table td:last-child {
    word-break: break-all;
    text-align: right;
  }

  /* Issues list */
  .issue {
    padding: 10px 14px;
    border-radius: 8px;
    margin-top: 8px;
    font-size: 0.82rem;
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }
  .issue.error-issue { background: rgba(225, 112, 85, 0.12); border: 1px solid rgba(225, 112, 85, 0.3); }
  .issue.warning-issue { background: rgba(253, 203, 110, 0.1); border: 1px solid rgba(253, 203, 110, 0.25); }
  .issue-tag {
    font-weight: 700;
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
  }
  .issue.error-issue .issue-tag { background: var(--red); color: #fff; }
  .issue.warning-issue .issue-tag { background: var(--orange); color: #000; }

  /* Fingerprint */
  .fingerprint-box {
    text-align: center;
    padding: 16px;
    margin-top: 12px;
    background: var(--bg);
    border-radius: 8px;
    border: 1px dashed var(--border);
  }
  .fingerprint-box .label {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .fingerprint-box .fp {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent-light);
    margin-top: 4px;
    letter-spacing: 2px;
    cursor: pointer;
  }
  .fingerprint-box .fp:hover { color: #fff; }
  .fingerprint-box .copy-hint {
    font-size: 0.65rem;
    color: var(--text-dim);
    margin-top: 4px;
  }

  /* Tabs for modes */
  .mode-tabs {
    display: flex;
    gap: 0;
    margin-bottom: 20px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
  }
  .mode-tab {
    flex: 1;
    padding: 10px;
    text-align: center;
    font-family: inherit;
    font-size: 0.8rem;
    font-weight: 600;
    background: transparent;
    color: var(--text-dim);
    border: none;
    cursor: pointer;
    transition: all 0.2s;
  }
  .mode-tab:first-child { border-right: 1px solid var(--border); }
  .mode-tab.active { background: var(--accent); color: #fff; }

  /* Dual confirm section */
  .dual-section { display: none; }
  .dual-section.show { display: block; }
  .dual-match { text-align: center; padding: 12px; font-weight: 700; }
  .dual-match.yes { color: var(--green); }
  .dual-match.no { color: var(--red); }
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1><span class="lock">&#x1f512;</span> Secure Token Transfer</h1>
    <p>Verify every detail before you send</p>
  </div>

  <!-- Mode tabs -->
  <div class="mode-tabs">
    <button class="mode-tab active" onclick="setMode('single')">Verify Transfer</button>
    <button class="mode-tab" onclick="setMode('dual')">Dual-Party Confirm</button>
  </div>

  <!-- Chain selector -->
  <div class="chains" id="chainSelector"></div>

  <!-- Single-party form -->
  <div id="singleMode">
    <div class="card">
      <div class="card-title">Transfer Details</div>
      <div class="row">
        <div class="field">
          <label>Chain</label>
          <input type="text" id="chain" readonly>
        </div>
        <div class="field">
          <label>Token</label>
          <input type="text" id="token" placeholder="e.g. SOL, USDC, BTC">
        </div>
      </div>
      <div class="field">
        <label>Sender Address</label>
        <input type="text" id="sender" placeholder="Your wallet address" spellcheck="false">
      </div>
      <div class="field">
        <label>Recipient Address</label>
        <input type="text" id="recipient" placeholder="Destination wallet address" spellcheck="false">
      </div>
      <div class="row">
        <div class="field">
          <label>Amount</label>
          <input type="text" id="amount" placeholder="0.00" inputmode="decimal">
        </div>
        <div class="field">
          <label>Memo <span style="opacity:0.5">(optional)</span></label>
          <input type="text" id="memo" placeholder="Tag, note, or reference">
        </div>
      </div>
      <button class="btn btn-verify" id="verifyBtn" onclick="doVerify()">
        Verify Transfer
      </button>
      <button class="btn btn-reset" onclick="resetForm()">Clear Form</button>
    </div>

    <div class="card result" id="resultCard">
      <div class="result-header">
        <div class="card-title" style="margin:0">Verification Result</div>
        <span class="status-badge" id="statusBadge"></span>
      </div>
      <table class="summary-table" id="summaryTable"></table>
      <div id="issuesList"></div>
      <div class="fingerprint-box" id="fpBox">
        <div class="label">Transfer Fingerprint</div>
        <div class="fp" id="fpValue" onclick="copyFP()" title="Click to copy"></div>
        <div class="copy-hint">Click to copy — share with recipient to confirm</div>
      </div>
    </div>
  </div>

  <!-- Dual-party form -->
  <div id="dualMode" class="dual-section">
    <div class="card">
      <div class="card-title">Sender's View</div>
      <div class="field">
        <label>Chain</label>
        <input type="text" id="d_s_chain" readonly>
      </div>
      <div class="field">
        <label>Token</label>
        <input type="text" id="d_s_token" placeholder="e.g. SOL">
      </div>
      <div class="field">
        <label>Sender Address</label>
        <input type="text" id="d_s_sender" spellcheck="false">
      </div>
      <div class="field">
        <label>Recipient Address</label>
        <input type="text" id="d_s_recipient" spellcheck="false">
      </div>
      <div class="row">
        <div class="field">
          <label>Amount</label>
          <input type="text" id="d_s_amount" inputmode="decimal">
        </div>
        <div class="field">
          <label>Memo</label>
          <input type="text" id="d_s_memo">
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Receiver's View</div>
      <div class="field">
        <label>Chain</label>
        <input type="text" id="d_r_chain" readonly>
      </div>
      <div class="field">
        <label>Token</label>
        <input type="text" id="d_r_token" placeholder="e.g. SOL">
      </div>
      <div class="field">
        <label>Sender Address</label>
        <input type="text" id="d_r_sender" spellcheck="false">
      </div>
      <div class="field">
        <label>Recipient Address</label>
        <input type="text" id="d_r_recipient" spellcheck="false">
      </div>
      <div class="row">
        <div class="field">
          <label>Amount</label>
          <input type="text" id="d_r_amount" inputmode="decimal">
        </div>
        <div class="field">
          <label>Memo</label>
          <input type="text" id="d_r_memo">
        </div>
      </div>
    </div>

    <button class="btn btn-verify" onclick="doDualConfirm()">
      Compare &amp; Confirm
    </button>
    <button class="btn btn-reset" onclick="resetDual()">Clear Both</button>

    <div class="card result" id="dualResultCard" style="margin-top:16px">
      <div class="result-header">
        <div class="card-title" style="margin:0">Dual Confirmation</div>
        <span class="status-badge" id="dualStatusBadge"></span>
      </div>
      <div id="dualSummary"></div>
    </div>
  </div>

</div>

<script>
const CHAINS = SUPPORTED_CHAINS_JSON;
let selectedChain = CHAINS[0];
let currentMode = 'single';

// --- Init ---
function init() {
  const sel = document.getElementById('chainSelector');
  CHAINS.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'chain-pill' + (c === selectedChain ? ' active' : '');
    btn.textContent = c;
    btn.onclick = () => pickChain(c);
    sel.appendChild(btn);
  });
  syncChainFields();
}

function pickChain(c) {
  selectedChain = c;
  document.querySelectorAll('.chain-pill').forEach(el => {
    el.classList.toggle('active', el.textContent === c);
  });
  syncChainFields();
}

function syncChainFields() {
  document.getElementById('chain').value = selectedChain;
  const tok = document.getElementById('token');
  if (!tok.value || CHAINS.includes(tok.value)) tok.value = selectedChain;
  // dual
  document.getElementById('d_s_chain').value = selectedChain;
  document.getElementById('d_r_chain').value = selectedChain;
  const dt1 = document.getElementById('d_s_token');
  const dt2 = document.getElementById('d_r_token');
  if (!dt1.value || CHAINS.includes(dt1.value)) dt1.value = selectedChain;
  if (!dt2.value || CHAINS.includes(dt2.value)) dt2.value = selectedChain;
}

function setMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-tab').forEach((t,i) => {
    t.classList.toggle('active', (i===0 && mode==='single') || (i===1 && mode==='dual'));
  });
  document.getElementById('singleMode').style.display = mode==='single' ? 'block' : 'none';
  document.getElementById('dualMode').classList.toggle('show', mode==='dual');
}

// --- Single verify ---
async function doVerify() {
  const body = {
    chain: document.getElementById('chain').value,
    token: document.getElementById('token').value,
    sender_address: document.getElementById('sender').value,
    recipient_address: document.getElementById('recipient').value,
    amount: document.getElementById('amount').value,
    memo: document.getElementById('memo').value || null,
  };
  const res = await fetch('/api/verify', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  showResult(data);
}

function showResult(data) {
  const card = document.getElementById('resultCard');
  card.classList.add('show');
  const badge = document.getElementById('statusBadge');
  badge.textContent = data.valid ? 'READY' : 'BLOCKED';
  badge.className = 'status-badge ' + (data.valid ? 'ready' : 'blocked');

  // Summary table
  const tbl = document.getElementById('summaryTable');
  const rows = [
    ['Chain', data.request.chain],
    ['Token', data.request.token],
    ['Amount', data.request.amount],
    ['From', data.request.sender_address],
    ['To', data.request.recipient_address],
  ];
  if (data.request.memo) rows.push(['Memo', data.request.memo]);
  tbl.innerHTML = rows.map(([k,v]) =>
    `<tr><td>${k}</td><td>${v}</td></tr>`
  ).join('');

  // Issues
  const il = document.getElementById('issuesList');
  if (data.issues.length === 0) {
    il.innerHTML = '<div class="issue" style="background:rgba(0,184,148,0.1);border:1px solid rgba(0,184,148,0.3)">No issues found. Transfer looks good.</div>';
  } else {
    il.innerHTML = data.issues.map(i => {
      const cls = i.severity === 'ERROR' ? 'error-issue' : 'warning-issue';
      return `<div class="issue ${cls}"><span class="issue-tag">${i.severity}</span><span>${i.field}: ${i.message}</span></div>`;
    }).join('');
  }

  // Fingerprint
  document.getElementById('fpValue').textContent = data.fingerprint;
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Highlight fields
  ['sender', 'recipient', 'amount'].forEach(id => {
    const el = document.getElementById(id);
    el.classList.remove('error', 'valid');
  });
  data.issues.forEach(i => {
    if (i.severity === 'ERROR') {
      const map = { sender_address: 'sender', recipient_address: 'recipient', amount: 'amount' };
      const el = document.getElementById(map[i.field]);
      if (el) el.classList.add('error');
    }
  });
  if (data.valid) {
    ['sender', 'recipient', 'amount'].forEach(id => {
      document.getElementById(id).classList.add('valid');
    });
  }
}

function copyFP() {
  const fp = document.getElementById('fpValue').textContent;
  navigator.clipboard.writeText(fp).then(() => {
    const hint = document.querySelector('.copy-hint');
    hint.textContent = 'Copied!';
    setTimeout(() => { hint.textContent = 'Click to copy — share with recipient to confirm'; }, 1500);
  });
}

function resetForm() {
  ['token','sender','recipient','amount','memo'].forEach(id => {
    const el = document.getElementById(id);
    el.value = '';
    el.classList.remove('error','valid');
  });
  syncChainFields();
  document.getElementById('resultCard').classList.remove('show');
}

// --- Dual confirm ---
async function doDualConfirm() {
  const body = {
    sender: {
      chain: document.getElementById('d_s_chain').value,
      token: document.getElementById('d_s_token').value,
      sender_address: document.getElementById('d_s_sender').value,
      recipient_address: document.getElementById('d_s_recipient').value,
      amount: document.getElementById('d_s_amount').value,
      memo: document.getElementById('d_s_memo').value || null,
    },
    receiver: {
      chain: document.getElementById('d_r_chain').value,
      token: document.getElementById('d_r_token').value,
      sender_address: document.getElementById('d_r_sender').value,
      recipient_address: document.getElementById('d_r_recipient').value,
      amount: document.getElementById('d_r_amount').value,
      memo: document.getElementById('d_r_memo').value || null,
    }
  };
  const res = await fetch('/api/dual-confirm', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  showDualResult(data);
}

function showDualResult(data) {
  const card = document.getElementById('dualResultCard');
  card.classList.add('show');
  const badge = document.getElementById('dualStatusBadge');
  badge.textContent = data.confirmed ? 'CONFIRMED' : 'REJECTED';
  badge.className = 'status-badge ' + (data.confirmed ? 'ready' : 'blocked');

  let html = '';
  html += `<table class="summary-table">`;
  html += `<tr><td>Sender valid</td><td>${data.sender_valid ? '&#x2705;' : '&#x274c;'}</td></tr>`;
  html += `<tr><td>Receiver valid</td><td>${data.receiver_valid ? '&#x2705;' : '&#x274c;'}</td></tr>`;
  html += `<tr><td>Fingerprints</td><td>${data.fingerprints_match ? '&#x2705; Match' : '&#x274c; MISMATCH'}</td></tr>`;
  html += `<tr><td>Sender FP</td><td style="color:var(--accent-light)">${data.sender_fingerprint}</td></tr>`;
  html += `<tr><td>Receiver FP</td><td style="color:var(--accent-light)">${data.receiver_fingerprint}</td></tr>`;
  html += `</table>`;

  if (data.issues.length > 0) {
    html += data.issues.map(i => {
      const cls = i.severity === 'ERROR' ? 'error-issue' : 'warning-issue';
      return `<div class="issue ${cls}"><span class="issue-tag">${i.severity}</span><span>${i.field}: ${i.message}</span></div>`;
    }).join('');
  }

  if (data.confirmed) {
    html += `<div class="dual-match yes" style="margin-top:12px">Both parties agree. Safe to execute.</div>`;
  } else if (!data.fingerprints_match) {
    html += `<div class="dual-match no" style="margin-top:12px">Details do NOT match. Reconcile before sending.</div>`;
  }

  document.getElementById('dualSummary').innerHTML = html;
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetDual() {
  ['d_s_token','d_s_sender','d_s_recipient','d_s_amount','d_s_memo',
   'd_r_token','d_r_sender','d_r_recipient','d_r_amount','d_r_memo'].forEach(id => {
    document.getElementById(id).value = '';
  });
  syncChainFields();
  document.getElementById('dualResultCard').classList.remove('show');
}

init();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class TransferHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Serve the single-page app."""
        page = HTML.replace(
            "SUPPORTED_CHAINS_JSON",
            json.dumps(SUPPORTED_CHAINS)
        )
        self._respond(200, "text/html", page.encode())

    def do_POST(self):
        """API endpoints."""
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            self._json_respond(400, {"error": "Invalid JSON"})
            return

        if self.path == "/api/verify":
            self._handle_verify(body)
        elif self.path == "/api/dual-confirm":
            self._handle_dual(body)
        else:
            self._json_respond(404, {"error": "Not found"})

    # --- API handlers ---

    def _handle_verify(self, body: dict):
        req = TransferRequest(
            chain=body.get("chain", ""),
            token=body.get("token", ""),
            sender_address=body.get("sender_address", ""),
            recipient_address=body.get("recipient_address", ""),
            amount=body.get("amount", ""),
            memo=body.get("memo"),
        )
        result = verify_transfer(req)
        self._json_respond(200, {
            "valid": result.valid,
            "fingerprint": result.fingerprint,
            "issues": [
                {"severity": i.severity.value, "field": i.field_name, "message": i.message}
                for i in result.issues
            ],
            "request": {
                "chain": req.chain,
                "token": req.token,
                "sender_address": req.sender_address,
                "recipient_address": req.recipient_address,
                "amount": req.amount,
                "memo": req.memo,
            },
        })

    def _handle_dual(self, body: dict):
        def _make_req(d: dict) -> TransferRequest:
            return TransferRequest(
                chain=d.get("chain", ""),
                token=d.get("token", ""),
                sender_address=d.get("sender_address", ""),
                recipient_address=d.get("recipient_address", ""),
                amount=d.get("amount", ""),
                memo=d.get("memo"),
            )

        s_req = _make_req(body.get("sender", {}))
        r_req = _make_req(body.get("receiver", {}))
        result = dual_confirm(s_req, r_req)

        all_issues = result.sender_result.issues + result.receiver_result.issues
        self._json_respond(200, {
            "confirmed": result.confirmed,
            "fingerprints_match": result.fingerprints_match,
            "sender_valid": result.sender_result.valid,
            "receiver_valid": result.receiver_result.valid,
            "sender_fingerprint": result.sender_result.fingerprint,
            "receiver_fingerprint": result.receiver_result.fingerprint,
            "issues": [
                {"severity": i.severity.value, "field": i.field_name, "message": i.message}
                for i in all_issues
            ],
        })

    # --- Response helpers ---

    def _respond(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_respond(self, code: int, data: dict):
        raw = json.dumps(data).encode()
        self._respond(code, "application/json", raw)

    def log_message(self, fmt, *args):
        # Quieter logging
        sys.stderr.write(f"  [{self.address_string()}] {fmt % args}\n")


def main():
    server = HTTPServer(("0.0.0.0", PORT), TransferHandler)
    print(f"\n  Secure Token Transfer UI")
    print(f"  Running on http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
