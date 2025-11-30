import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

# Create directories if they don't exist
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
    "Food": ["kfc", "mcdonald", "restaurant", "cafe", "food", "burger", "pizza"],
    "Fuel": ["pso", "shell", "total", "petrol", "fuel", "gas"],
    "Transport": ["uber", "careem", "taxi", "transport", "bus", "metro"],
    "Utilities": ["electricity", "gas", "water", "internet", "phone", "bill"],
    "Rent": ["rent", "lease", "housing"],
    "Office": ["stationery", "office", "supplies"],
    "Other": []
}