# Data folder

## Verifying the website (no real credentials needed)

1. **Run the dashboard:** From the project root run `python app.py` and open http://127.0.0.1:8080.
2. **Demo mode:** On the dashboard click **"View with demo data"** or open http://127.0.0.1:8080/?demo=1 to see sample stats (threads processed, drafts, time saved). This confirms the site works without running the CLI or connecting to Gmail/Outlook.

## Gmail credentials (for real use)

- **Sample file:** `credentials.sample.json` shows the required format. It uses placeholders and will **not** connect to Google.
- **Real credentials:** In [Google Cloud Console](https://console.cloud.google.com) create OAuth 2.0 credentials (Desktop app), download the JSON, and save it as **`credentials.json`** in this folder (not the `.sample` file).
- Do not commit `credentials.json` or `gmail_token.json` to version control.

## Other files

- `gmail_token.json` – Created automatically after you sign in with Gmail (OAuth token).
- `productivity_metrics.json`, `satisfaction_surveys.json`, `inbox_zero_history.json`, `follow_ups.json` – Created when you use the CLI.
