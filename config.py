"""Configuration for the email management agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ScaleDown - compress long threads (~85% reduction)
SCALEDOWN_API_URL = os.getenv("SCALEDOWN_API_URL", "https://api.scaledown.xyz/compress/raw/")
SCALEDOWN_API_KEY = os.getenv("SCALEDOWN_API_KEY", "")
SCALEDOWN_RATE = os.getenv("SCALEDOWN_RATE", "auto")

# Thread compression threshold (messages) - use ScaleDown above this
THREAD_SCALEDOWN_THRESHOLD = int(os.getenv("THREAD_SCALEDOWN_THRESHOLD", "10"))

# Urgent detection
URGENT_KEYWORDS = [
    "urgent", "asap", "as soon as possible", "critical", "emergency",
    "deadline", "immediate", "time-sensitive", "action required"
]
URGENT_SENDER_DOMAINS = []  # e.g. ["boss@company.com"]

# Smart folder names
FOLDER_URGENT = "Urgent"
FOLDER_FOLLOW_UP = "Needs Reply"
FOLDER_MEETINGS = "Meetings"
FOLDER_NEWSLETTER = "Newsletters"
FOLDER_PROMO = "Promotions"
FOLDER_OTHER = "Other"

# Metrics storage
METRICS_FILE = DATA_DIR / "productivity_metrics.json"
SURVEYS_FILE = DATA_DIR / "satisfaction_surveys.json"
INBOX_ZERO_FILE = DATA_DIR / "inbox_zero_history.json"
