# Email Management Agent

Email assistant with **auto-categorization**, **template responses**, **ScaleDown thread compression**, and **inbox zero** tracking.

## Technical stack

- **Gmail API** and **Microsoft Graph (Outlook)** for mail
- **ScaleDown** ([docs.scaledown.ai](https://docs.scaledown.ai)) to compress long threads (~85%) so the whole inbox context can be processed at once
- **Triage agent** → categories (urgent, follow-up, meeting, newsletter, promotion, other)
- **Priority scorer** (0–100) for ordering
- **Draft generator** with templates
- **Follow-up tracker** (persisted)
- **Custom rules engine** (conditions → actions)
- **Smart folders**, **urgent detection**, **meeting extraction**, **unsubscribe suggestions**
- **Deliverables**: productivity metrics, satisfaction surveys, inbox zero achievement rate

## Setup

1. **Clone / open project**
   ```bash
   cd email_pro
   ```

2. **Create virtualenv and install**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Environment**
   - Copy `.env.example` to `.env`
   - Set `SCALEDOWN_API_KEY` for thread compression (get key from [ScaleDown](https://blog.scaledown.ai/blog/getting-started))

4. **Gmail**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com), enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app), download JSON
   - Save as `data/credentials.json`
   - On first run, browser will open for consent; token is stored in `data/gmail_token.json`

5. **Outlook** (optional)
   - Register an app in Azure AD, add Microsoft Graph mail permissions
   - Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` in `.env` or pass credentials to the provider

## Dashboard (responsive web UI)

The dashboard works on desktop, tablet, and mobile and is deployment-ready.

- **Local (dev):** `python app.py` — serves at http://127.0.0.1:8080 and opens the browser.
- **Production:** Set `PORT` (e.g. `8080`) in the environment; the app uses the Waitress WSGI server and binds to `0.0.0.0` so it can be reached by a reverse proxy or load balancer.

**Health check (for deploy platforms):** `GET /health` or `GET /api/health` → `{"status": "ok"}`.

### Deploying the dashboard

| Platform   | Notes |
|-----------|--------|
| **Railway / Render / Fly.io** | Set `PORT`; they inject it. Use `Procfile`: `web: python app.py`. |
| **Heroku** | Same; add `runtime.txt` with e.g. `python-3.11` if needed. |
| **VPS / Docker** | Run with `PORT=8080 python app.py` or `waitress-serve --port=8080 --host=0.0.0.0 app:app`. Put Nginx/Caddy in front for HTTPS. |
| **Windows server** | `set PORT=8080 && python app.py` or `set USE_WAITRESS=1 && python app.py`. |

Install deps: `pip install -r requirements.txt` (includes `waitress`).

## Usage

### CLI (plugin interface)

```bash
# Triage inbox (category, priority, folder)
python plugin_cli.py triage --provider gmail --max 20

# Smart folders view
python plugin_cli.py folders --provider gmail --max 20

# Urgent threads only
python plugin_cli.py urgent --provider gmail

# Suggest draft for a thread (optionally create draft in mailbox)
python plugin_cli.py draft <thread_id> [--template acknowledge|short_yes|follow_up|meeting_accept] [--create]

# Productivity metrics and satisfaction
python plugin_cli.py metrics
python plugin_cli.py survey --rating 5 --comment "Great" --feature triage

# Record inbox state for inbox zero rate
python plugin_cli.py inbox-zero --unread 0 --inbox 0
```

### From code

```python
from src.assistant import EmailAssistant

assistant = EmailAssistant(provider_name="gmail", use_scaledown=True)

# Triage one thread (ScaleDown used automatically for long threads)
thread = assistant.provider.get_thread("thread_id")
triage = assistant.run_triage(thread)
# triage.category, triage.priority_score, triage.is_urgent, triage.suggested_folder

# Smart folders (inbox grouped by category)
view = assistant.get_smart_folders_view(max_threads=50)

# Urgent detection
urgent_list = assistant.get_urgent(max_threads=50)

# Draft from template
draft = assistant.suggest_draft(thread, template_id="acknowledge")
assistant.create_draft(to=[sender], subject=f"Re: {thread.subject}", body=draft.body, thread_id=thread.id)

# Follow-up tracker
assistant.add_follow_up(thread)

# Meeting extraction
meeting = assistant.extract_meeting(thread)

# Unsubscribe suggestion (newsletters/marketing)
suggestion = assistant.suggest_unsubscribe(thread)

# Rules engine
for rule, params in assistant.apply_rules(thread):
    if rule.action == "apply_label" and params.get("action_param"):
        assistant.provider.apply_label(thread.messages[-1].id, params["action_param"])

# Metrics and inbox zero
assistant.record_inbox_check(unread_count=0, inbox_count=0)
metrics = assistant.get_metrics()  # productivity, time_saved_estimate_min, satisfaction_avg, inbox_zero_rate
```


