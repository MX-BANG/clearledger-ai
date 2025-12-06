import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

# Create directories if they don't exist (only in local mode)
if not os.getenv("DATABASE_URL"):  # Local development
    for dir_path in [DATA_DIR, DATABASE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
else:  # Production
    # In production, use /tmp for temporary storage
    DATA_DIR = Path("/tmp/data")
    DATABASE_DIR = Path("/tmp/database")
    for dir_path in [DATA_DIR, DATABASE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/bookkeeping.db")

# File Upload Settings
UPLOAD_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"

for dir_path in [UPLOAD_DIR, PROCESSED_DIR, EXPORT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

# AI Settings
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "PKR")

# Supported file types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".csv", ".xlsx"}

# Category mapping for auto-categorization
CATEGORY_KEYWORDS = {
    "Food": [
        # English
        "kfc", "mcdonald", "restaurant", "cafe", "food", "burger", "pizza", "restaurant",
        # Urdu/Roman Urdu
        "khana", "khaane", "nashta", "dinner", "lunch", "biryani", "karahi"
    ],
    "Fuel": [
        # English
        "pso", "shell", "total", "attock", "petrol", "fuel", "gas",
        # Urdu/Roman Urdu
        "petrol", "diesel"
    ],
    "Transport": [
        # English
        "uber", "careem", "taxi", "transport", "bus", "metro", "rickshaw", "bykea", "indriver",
        # Urdu/Roman Urdu
        "sawari", "gaari"
    ],
    "Utilities": [
        # English
        "electricity", "gas", "water", "internet", "phone", "bill", "wifi", "ptcl", "nayatel",
        # Urdu/Roman Urdu
        "bijli", "pani", "bill"
    ],
    "Rent": [
        # English
        "rent", "lease", "housing",
        # Urdu/Roman Urdu
        "kiraya", "makaan"
    ],
    "Office": [
        # English
        "stationery", "office", "supplies", "printing",
        # Urdu/Roman Urdu
        "daftar", "kaam"
    ],
    "Other": []
}