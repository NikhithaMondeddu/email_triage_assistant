"""
Email Assistant dashboard. Responsive and deployment-ready.
  Dev:   python app.py  |  Prod:  PORT=8080 python app.py
"""
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
app.config["JSONIFY_PRETTY_PRINT_REGULAR"] = True

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#0f0f12">
  <title>Email Assistant – Tame your inbox</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 680px;
      margin: 0 auto;
      padding: clamp(1rem, 4vw, 2rem);
      padding-left: max(clamp(1rem, 4vw, 2rem), env(safe-area-inset-left));
      padding-right: max(clamp(1rem, 4vw, 2rem), env(safe-area-inset-right));
      padding-bottom: max(clamp(1rem, 4vw, 2rem), env(safe-area-inset-bottom));
      background: #0f0f12;
      color: #e4e4e7;
      min-height: 100vh;
      line-height: 1.5;
    }
    @media (max-width: 480px) { body { padding-top: max(1rem, env(safe-area-inset-top)); } }

    .hero {
      margin-bottom: 2rem;
    }
    .hero h1 {
      color: #fafafa;
      font-weight: 700;
      font-size: clamp(1.5rem, 5vw, 1.875rem);
      margin: 0 0 0.35rem 0;
      letter-spacing: -0.02em;
    }
    .hero p {
      color: #a1a1aa;
      font-size: clamp(0.9375rem, 2.5vw, 1rem);
      margin: 0 0 0.75rem 0;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.8125rem;
      color: #22c55e;
    }
    .status::before {
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    .section-title {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #71717a;
      margin: 0 0 0.75rem 0;
    }
    .card {
      background: #18181b;
      border-radius: 10px;
      padding: clamp(1rem, 3vw, 1.25rem);
      margin-bottom: 0.75rem;
    }
    .card h3 {
      font-size: 1rem;
      font-weight: 600;
      color: #fafafa;
      margin: 0 0 0.25rem 0;
    }
    .card p {
      font-size: 0.875rem;
      color: #a1a1aa;
      margin: 0 0 0.75rem 0;
    }
    .card p:last-of-type { margin-bottom: 0; }
    .cmd-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }
    .cmd-row code {
      flex: 1 1 200px;
      min-width: 0;
      background: #27272a;
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      font-size: 0.8125rem;
      overflow-x: auto;
      white-space: nowrap;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.5rem 0.875rem;
      font-size: 0.8125rem;
      font-weight: 500;
      color: #18181b;
      background: #fafafa;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.15s, transform 0.1s;
    }
    .btn:hover { background: #e4e4e7; }
    .btn:active { transform: scale(0.98); }
    .btn.copy-btn { min-width: 5rem; justify-content: center; }
    .btn.copied { background: #22c55e; color: #fff; }
    .btn svg { width: 1em; height: 1em; flex-shrink: 0; }

    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1rem;
    }
    .stat {
      background: #18181b;
      border-radius: 10px;
      padding: 1rem;
      text-align: center;
    }
    .stat-num {
      font-size: 1.5rem;
      font-weight: 700;
      color: #fafafa;
      line-height: 1.2;
    }
    .stat-label {
      font-size: 0.75rem;
      color: #71717a;
      margin-top: 0.25rem;
    }
    .empty-state {
      background: #18181b;
      border-radius: 10px;
      padding: 1.25rem;
      color: #a1a1aa;
      font-size: 0.9375rem;
      text-align: center;
    }
    .empty-state strong { color: #e4e4e7; }

    .steps {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .steps li {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1rem;
      font-size: 0.9375rem;
      color: #a1a1aa;
    }
    .steps li:last-child { margin-bottom: 0; }
    .step-num {
      flex-shrink: 0;
      width: 1.5rem;
      height: 1.5rem;
      line-height: 1.5rem;
      text-align: center;
      background: #27272a;
      color: #a1a1aa;
      border-radius: 50%;
      font-weight: 600;
      font-size: 0.8125rem;
    }
    .help-link {
      color: #3b82f6;
      text-decoration: none;
    }
    .help-link:hover { text-decoration: underline; }
    .raw-toggle {
      font-size: 0.75rem;
      color: #71717a;
      background: none;
      border: none;
      cursor: pointer;
      padding: 0.25rem 0;
      margin-top: 0.5rem;
    }
    .raw-toggle:hover { color: #a1a1aa; }
    .raw-json {
      background: #27272a;
      padding: 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      margin-top: 0.5rem;
      display: none;
    }
    .raw-json.show { display: block; }
    .demo-badge {
      display: inline-block;
      font-size: 0.6875rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #3b82f6;
      background: rgba(59, 130, 246, 0.15);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      margin-bottom: 0.5rem;
    }
    .inbox-folder {
      margin-bottom: 1.25rem;
    }
    .inbox-folder-title {
      font-size: 0.8125rem;
      font-weight: 600;
      color: #a1a1aa;
      margin: 0 0 0.5rem 0;
      padding-bottom: 0.25rem;
    }
    .email-row {
      background: #18181b;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      margin-bottom: 0.5rem;
      border-left: 3px solid #27272a;
    }
    .email-row.urgent { border-left-color: #ef4444; }
    .email-row.follow_up { border-left-color: #3b82f6; }
    .email-row.meeting { border-left-color: #22c55e; }
    .email-row.newsletter { border-left-color: #71717a; }
    .email-row.promotion { border-left-color: #a855f7; }
    .email-row .email-subject { font-weight: 500; color: #fafafa; margin: 0 0 0.25rem 0; }
    .email-row .email-meta { font-size: 0.75rem; color: #71717a; margin-bottom: 0.25rem; }
    .email-row .email-snippet { font-size: 0.8125rem; color: #a1a1aa; margin: 0; }
    .folder-tag {
      display: inline-block;
      font-size: 0.6875rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      padding: 0.2rem 0.45rem;
      border-radius: 4px;
      margin-right: 0.35rem;
    }
    .folder-tag.urgent { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .folder-tag.follow_up { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .folder-tag.meeting { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
    .folder-tag.newsletter { background: rgba(113, 113, 122, 0.3); color: #a1a1aa; }
    .folder-tag.promotion { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
    .folder-tag.other { background: #27272a; color: #71717a; }
    .priority-badge { font-size: 0.6875rem; color: #71717a; margin-left: 0.35rem; }
  </style>
</head>
<body>
  <header class="hero">
    <h1>Email Assistant</h1>
    <p>Triage your inbox, find what’s urgent, and get to inbox zero. Run simple commands from your terminal—this page helps you get started and see your progress.</p>
    <div class="status" aria-live="polite">Ready</div>
    <p style="margin-top: 1rem; font-size: 0.8125rem;">
      <a href="#demo-inbox" class="help-link">Try demo inbox</a> – see sample emails categorized by the assistant. &nbsp;
      <a href="?demo=1" class="help-link">View with demo stats</a>.
    </p>
  </header>

  <p class="section-title" id="demo-inbox">Demo inbox</p>
  <div class="demo-badge">Sample emails (no account needed)</div>
  <div id="demo-inbox-container"><p class="empty-state">Loading demo emails…</p></div>

  <p class="section-title" style="margin-top: 1.5rem;">What you can do</p>
  <div class="card">
    <h3>Scan your inbox (triage)</h3>
    <p>Sort emails by priority and category. Run this in your project folder:</p>
    <div class="cmd-row">
      <code id="cmd-triage">python plugin_cli.py triage --provider gmail --max 20</code>
      <button type="button" class="btn copy-btn" data-copy="cmd-triage" aria-label="Copy command">Copy</button>
    </div>
  </div>
  <div class="card">
    <h3>View by folder (smart folders)</h3>
    <p>See emails grouped as Urgent, Needs Reply, Meetings, etc.</p>
    <div class="cmd-row">
      <code id="cmd-folders">python plugin_cli.py folders --provider gmail --max 20</code>
      <button type="button" class="btn copy-btn" data-copy="cmd-folders" aria-label="Copy command">Copy</button>
    </div>
  </div>
  <div class="card">
    <h3>Find urgent emails</h3>
    <p>List only threads marked urgent.</p>
    <div class="cmd-row">
      <code id="cmd-urgent">python plugin_cli.py urgent --provider gmail</code>
      <button type="button" class="btn copy-btn" data-copy="cmd-urgent" aria-label="Copy command">Copy</button>
    </div>
  </div>
  <div class="card">
    <h3>See your stats</h3>
    <p>Threads processed, drafts created, and estimated time saved.</p>
    <div class="cmd-row">
      <code id="cmd-metrics">python plugin_cli.py metrics</code>
      <button type="button" class="btn copy-btn" data-copy="cmd-metrics" aria-label="Copy command">Copy</button>
    </div>
  </div>

  <p class="section-title" style="margin-top: 1.5rem;">Your stats</p>
  <div id="stats-box">
    <div class="demo-badge" id="demo-badge" style="display: none;">Demo data</div>
    <div class="stats" id="stats-cards" style="display: none;"></div>
    <div class="empty-state" id="stats-empty">No data yet. Copy one of the commands above, run it in your terminal from the project folder, then refresh this page. Or <a href="?demo=1" class="help-link">view with demo data</a> to see how it looks.</div>
    <button type="button" class="raw-toggle" id="raw-toggle" style="display: none;">Show raw data</button>
    <pre class="raw-json" id="raw-json" aria-live="polite"></pre>
  </div>

  <p class="section-title" style="margin-top: 1.5rem;">First time here?</p>
  <div class="card">
    <ol class="steps" role="list">
      <li>
        <span class="step-num" aria-hidden="true">1</span>
        <span>Open a terminal in the project folder (<code>email_pro</code>).</span>
      </li>
      <li>
        <span class="step-num" aria-hidden="true">2</span>
        <span>Use <strong>Gmail</strong>: put your OAuth file at <code>data/credentials.json</code>. Use <strong>Outlook</strong>: set <code>AZURE_CLIENT_ID</code>, <code>AZURE_CLIENT_SECRET</code>, and <code>AZURE_TENANT_ID</code> in a <code>.env</code> file.</span>
      </li>
      <li>
        <span class="step-num" aria-hidden="true">3</span>
        <span>Click <strong>Copy</strong> next to “Scan your inbox”, paste in the terminal, and press Enter. Come back here and refresh to see your stats.</span>
      </li>
    </ol>
  </div>

  <p class="section-title" style="margin-top: 1.5rem;">Need help?</p>
  <div class="card">
    <p style="margin-bottom: 0;">Read the full guide in <code>README.md</code> in the project folder. For ScaleDown (faster triage on long threads), add <code>SCALEDOWN_API_KEY</code> to your <code>.env</code>.</p>
  </div>

  <script>
    (function() {
      // Load demo inbox
      (function loadDemoInbox() {
        var container = document.getElementById('demo-inbox-container');
        if (!container) return;
        fetch('/api/demo/inbox')
          .then(function(r) { return r.json(); })
          .then(function(data) {
            var threads = (data && data.threads) ? data.threads : [];
            if (threads.length === 0) {
              container.innerHTML = '<p class="empty-state">No demo emails.</p>';
              return;
            }
            var byFolder = {};
            threads.forEach(function(t) {
              var f = t.folder || 'Other';
              if (!byFolder[f]) byFolder[f] = [];
              byFolder[f].push(t);
            });
            var order = ['Urgent', 'Needs Reply', 'Meetings', 'Newsletters', 'Promotions', 'Other'];
            var html = '';
            order.forEach(function(folder) {
              if (!byFolder[folder]) return;
              html += '<div class="inbox-folder"><div class="inbox-folder-title">' + folder + '</div>';
              byFolder[folder].forEach(function(t) {
                var cat = (t.category || 'other').replace(' ', '_');
                html += '<div class="email-row ' + cat + '">';
                html += '<div class="email-subject">' + (t.subject || '').replace(/</g, '&lt;') + '</div>';
                html += '<div class="email-meta">From: ' + (t.sender || '').replace(/</g, '&lt;') + ' <span class="priority-badge">Priority ' + (t.priority || 0) + '</span></div>';
                if (t.snippet) { var sn = (t.snippet || '').replace(/</g, '&lt;'); html += '<div class="email-snippet">' + sn.substring(0, 120) + (sn.length > 120 ? '…' : '') + '</div>'; }
                html += '<div style="margin-top:0.35rem;"><span class="folder-tag ' + cat + '">' + (t.folder || 'Other') + '</span>' + (t.is_urgent ? ' <span class="folder-tag urgent">Urgent</span>' : '') + '</div>';
                html += '</div>';
              });
              html += '</div>';
            });
            container.innerHTML = html;
          })
          .catch(function() {
            container.innerHTML = '<p class="empty-state">Could not load demo inbox.</p>';
          });
      })();

      function copyText(id) {
        var el = document.getElementById(id);
        if (!el) return '';
        var text = el.textContent || '';
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text);
        } else {
          var ta = document.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly', '');
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        return text;
      }
      document.querySelectorAll('.copy-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
          var id = this.getAttribute('data-copy');
          copyText(id);
          this.textContent = 'Copied!';
          this.classList.add('copied');
          var t = setTimeout(function() {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
            clearTimeout(t);
          }, 2000);
        });
      });

      function showStats(data) {
        var totals = data && data.totals ? data.totals : (data && !data.message && !data.error ? data : null);
        var emptyEl = document.getElementById('stats-empty');
        var cardsEl = document.getElementById('stats-cards');
        var rawEl = document.getElementById('raw-json');
        var toggleEl = document.getElementById('raw-toggle');
        rawEl.textContent = JSON.stringify(data, null, 2);

        if (totals && (totals.threads_processed || totals.drafts_created || totals.triage_count || totals.scaledown_calls || totals.demo)) {
          var demo = totals.demo === true;
          document.getElementById('demo-badge').style.display = demo ? 'inline-block' : 'none';
          emptyEl.style.display = 'none';
          cardsEl.style.display = 'grid';
          cardsEl.innerHTML = '';
          var items = [
            [totals.threads_processed || 0, 'Threads processed'],
            [totals.drafts_created || 0, 'Drafts created'],
            [totals.triage_count || 0, 'Triage runs'],
            [totals.time_saved_estimate_min != null ? Math.round(totals.time_saved_estimate_min) + ' min' : (totals.tokens_saved || 0), totals.time_saved_estimate_min != null ? 'Time saved (est.)' : 'Tokens saved']
          ];
          items.forEach(function(item) {
            var div = document.createElement('div');
            div.className = 'stat';
            div.innerHTML = '<div class="stat-num">' + item[0] + '</div><div class="stat-label">' + item[1] + '</div>';
            cardsEl.appendChild(div);
          });
          toggleEl.style.display = 'block';
        } else {
          emptyEl.style.display = 'block';
          cardsEl.style.display = 'none';
          if (data && (data.message || data.error)) toggleEl.style.display = 'block';
        }
      }
      document.getElementById('raw-toggle').addEventListener('click', function() {
        var pre = document.getElementById('raw-json');
        pre.classList.toggle('show');
        this.textContent = pre.classList.contains('show') ? 'Hide raw data' : 'Show raw data';
      });
      var demo = (window.location.search || '').indexOf('demo=1') !== -1;
      fetch('/api/metrics' + (demo ? '?demo=1' : ''))
        .then(function(r) { return r.json(); })
        .then(showStats)
        .catch(function() { showStats({ message: 'Could not load metrics. Run a command from this page first.' }); });
    })();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


# Demo inbox: sample emails with pre-assigned categories (no real account needed).
DEMO_INBOX = [
    {"id": "d1", "subject": "URGENT: Server down – need fix by 5 PM", "sender": "ops@company.com", "snippet": "The production server is not responding. Please look into this as soon as possible. We have a deadline today.", "folder": "Urgent", "category": "urgent", "priority": 92, "is_urgent": True},
    {"id": "d2", "subject": "Re: Q4 budget review", "sender": "sarah@company.com", "snippet": "Thanks for sending the numbers. Could you confirm the marketing line item by tomorrow? I have a few questions.", "folder": "Needs Reply", "category": "follow_up", "priority": 78, "is_urgent": False},
    {"id": "d3", "subject": "Meeting: Product sync – Thu 3 PM", "sender": "calendar@company.com", "snippet": "You have been invited to Product sync. When: Thu 3:00 PM. Join Zoom: https://zoom.us/j/123456789", "folder": "Meetings", "category": "meeting", "priority": 65, "is_urgent": False},
    {"id": "d4", "subject": "Weekly digest: Product updates", "sender": "newsletter@product.com", "snippet": "View in browser | Unsubscribe | Manage preferences. This week we shipped new filters and improved search.", "folder": "Newsletters", "category": "newsletter", "priority": 25, "is_urgent": False},
    {"id": "d5", "subject": "50% off this weekend only", "sender": "deals@store.com", "snippet": "Limited time: 50% off everything. Use code SAVE50 at checkout. Shop now!", "folder": "Promotions", "category": "promotion", "priority": 20, "is_urgent": False},
    {"id": "d6", "subject": "Action required: Approve contract by EOD", "sender": "legal@company.com", "snippet": "The vendor contract is pending your approval. Please sign before 6 PM today to avoid delays.", "folder": "Urgent", "category": "urgent", "priority": 88, "is_urgent": True},
    {"id": "d7", "subject": "Re: Project timeline", "sender": "mike@agency.com", "snippet": "Following up – did you get a chance to review the timeline? Let me know if we need to move the launch date.", "folder": "Needs Reply", "category": "follow_up", "priority": 72, "is_urgent": False},
    {"id": "d8", "subject": "Invitation: All-hands – Fri 10 AM", "sender": "events@company.com", "snippet": "When: Friday 10:00 AM. Where: Main conference room & Zoom. Accept | Decline", "folder": "Meetings", "category": "meeting", "priority": 60, "is_urgent": False},
    {"id": "d9", "subject": "Your daily tech news", "sender": "news@techdaily.com", "snippet": "Unsubscribe | Privacy. Top stories: AI trends, cloud updates, and security tips.", "folder": "Newsletters", "category": "newsletter", "priority": 22, "is_urgent": False},
    {"id": "d10", "subject": "Free shipping on orders over $50", "sender": "promo@shop.com", "snippet": "Free shipping when you spend $50 or more. No code needed. Offer ends Sunday.", "folder": "Promotions", "category": "promotion", "priority": 18, "is_urgent": False},
    {"id": "d11", "subject": "Lunch tomorrow?", "sender": "jane@company.com", "snippet": "Want to grab lunch tomorrow around 12:30? Let me know!", "folder": "Other", "category": "other", "priority": 55, "is_urgent": False},
    {"id": "d12", "subject": "Deadline reminder: Report due Monday", "sender": "manager@company.com", "snippet": "Friendly reminder: the quarterly report is due Monday 9 AM. Please submit via the portal.", "folder": "Urgent", "category": "urgent", "priority": 85, "is_urgent": True},
]

# Demo stats for verifying the dashboard without real credentials or CLI runs.
DEMO_METRICS = {
    "totals": {
        "threads_processed": 42,
        "drafts_created": 8,
        "triage_count": 42,
        "scaledown_calls": 3,
        "tokens_saved": 1250,
        "time_saved_estimate_min": 50.4,
        "demo": True,
    }
}


@app.route("/api/metrics")
def api_metrics():
    if request.args.get("demo") in ("1", "true", "yes"):
        return jsonify(DEMO_METRICS)
    try:
        import config
        if config.METRICS_FILE.exists():
            data = json.loads(config.METRICS_FILE.read_text(encoding="utf-8"))
            totals = data.get("totals") or {}
            if totals:
                from src.deliverables.productivity_metrics import ProductivityMetrics
                pm = ProductivityMetrics()
                totals = dict(totals)
                totals["time_saved_estimate_min"] = round(pm.estimate_time_saved_minutes(), 1)
            return jsonify({"totals": totals} if totals else {"message": "No metrics yet. Run the CLI to triage inbox."})
        return jsonify({"message": "No metrics yet. Run: python plugin_cli.py triage --provider gmail"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/demo/inbox")
def api_demo_inbox():
    """Return demo emails with categories for the demo inbox UI."""
    return jsonify({"threads": DEMO_INBOX, "demo": True})


@app.route("/health")
@app.route("/api/health")
def health():
    """For load balancers and deployment platforms."""
    return jsonify({"status": "ok"})


def _run_dev(host: str, port: int):
    """Development: Flask dev server + optional browser open."""
    if os.environ.get("FLASK_ENV") != "production" and "PORT" not in os.environ:
        def _open():
            import time
            time.sleep(1.2)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=_open, daemon=True).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)


def _run_production(host: str, port: int):
    """Production: Waitress WSGI server."""
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=4, url_scheme="https" if os.environ.get("HTTPS") == "1" else "http")
    except ImportError:
        app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    use_waitress = os.environ.get("PORT") or os.environ.get("USE_WAITRESS", "").lower() in ("1", "true", "yes")
    if use_waitress:
        _run_production(host, port)
    else:
        _run_dev(host, port)
