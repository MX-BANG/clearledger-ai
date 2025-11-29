# 📋 Complete Setup Instructions

## File Structure - Create These Folders & Files

```
ai-bookkeeping-engine/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   ├── ai_structuring.py
│   │   ├── confidence_scorer.py
│   │   ├── duplicate_detector.py
│   │   ├── categorizer.py
│   │   └── exporter.py
│   │
│   └── utils/
│       └── __init__.py
│
├── frontend/
│   ├── app.py
│   ├── pages/
│   │   ├── 1_📤_Upload.py
│   │   ├── 2_✏️_Review.py
│   │   ├── 3_📊_Dashboard.py
│   │   └── 4_💾_Export.py
│   │
│   └── components/
│       └── __init__.py
│
├── data/
│   ├── uploads/
│   ├── processed/
│   └── exports/
│
├── database/
│
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── start.py
├── README.md
├── QUICKSTART.md
└── SETUP_INSTRUCTIONS.md (this file)
```

---

## 🔨 Step-by-Step Setup in VS Code

### Step 1: Create Project Folder

```bash
mkdir ai-bookkeeping-engine
cd ai-bookkeeping-engine
```

### Step 2: Create All Directories

```bash
# Backend
mkdir -p backend/services backend/utils

# Frontend
mkdir -p frontend/pages frontend/components

# Data directories
mkdir -p data/uploads data/processed data/exports

# Database directory
mkdir database
```

### Step 3: Create All Python Files

#### In VS Code:
1. Right-click on `backend/` → New File
2. Create each file listed above
3. Copy code from provided artifacts
4. Save each file

**Files to create:**

**Backend:**
- `backend/__init__.py` (empty or with comment)
- `backend/main.py`
- `backend/config.py`
- `backend/database.py`
- `backend/models.py`

**Backend Services:**
- `backend/services/__init__.py`
- `backend/services/ocr_service.py`
- `backend/services/ai_structuring.py`
- `backend/services/confidence_scorer.py`
- `backend/services/duplicate_detector.py`
- `backend/services/categorizer.py`
- `backend/services/exporter.py`

**Backend Utils:**
- `backend/utils/__init__.py`

**Frontend:**
- `frontend/app.py`
- `frontend/pages/1_📤_Upload.py`
- `frontend/pages/2_✏️_Review.py`
- `frontend/pages/3_📊_Dashboard.py`
- `frontend/pages/4_💾_Export.py`
- `frontend/components/__init__.py`

**Root files:**
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `start.py`
- `README.md`
- `QUICKSTART.md`

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First installation may take 5-10 minutes as it downloads OCR models and AI libraries.

### Step 5: Get Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### Step 6: Configure Environment

Create `.env` file in root directory:

```bash
GEMINI_API_KEY=your_actual_api_key_here
DATABASE_URL=sqlite:///./database/bookkeeping.db
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=data/uploads
PROCESSED_DIR=data/processed
EXPORT_DIR=data/exports
CONFIDENCE_THRESHOLD=0.70
DEFAULT_CURRENCY=PKR
```

**Replace `your_actual_api_key_here` with your actual Gemini API key!**

### Step 7: Test Installation

```bash
# Test backend imports
python -c "from backend.config import GEMINI_API_KEY; print('✅ Config OK')"

# Test OCR
python -c "import easyocr; print('✅ EasyOCR OK')"

# Test Streamlit
python -c "import streamlit; print('✅ Streamlit OK')"

# Test FastAPI
python -c "import fastapi; print('✅ FastAPI OK')"
```

All should print "✅ ... OK"

---

## 🚀 Running the Application

### Method 1: Easy Startup (Recommended)

```bash
python start.py
```

This will:
- Start backend on port 8000
- Start frontend on port 8501
- Open browser automatically

### Method 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload
```

Wait until you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m streamlit run app.py
```

Browser opens at `http://localhost:8501`

---

## ✅ Verification Checklist

### 1. Check Backend is Running
- Open: http://localhost:8000
- Should see: `{"status":"running",...}`

### 2. Check API Documentation
- Open: http://localhost:8000/docs
- Should see: Interactive API documentation (Swagger UI)

### 3. Check Frontend is Running
- Open: http://localhost:8501
- Should see: Dashboard with "Backend API is running" message

### 4. Test Upload
- Go to Upload page
- Upload a test image
- Should process without errors

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "GEMINI_API_KEY not found"
**Solution:**
Check `.env` file exists and has correct format:
```
GEMINI_API_KEY=AIza...your_key_here
```

### Problem: "Port 8000 already in use"
**Solution:**
```bash
# Kill process on port 8000
# Mac/Linux:
lsof -ti:8000 | xargs kill -9

# Windows (run as admin):
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

### Problem: "Backend API is not running" in frontend
**Solution:**
1. Check Terminal 1 - backend should be running
2. Visit http://localhost:8000 - should respond
3. Restart backend if needed

### Problem: OCR not working
**Solution:**
First run downloads models (500MB+), wait for completion:
```bash
python -c "import easyocr; reader = easyocr.Reader(['en'])"
```

### Problem: Database errors
**Solution:**
Delete and recreate database:
```bash
rm -rf database/bookkeeping.db
# Restart backend - database recreates automatically
```

---

## 📦 Package Versions (If Issues Occur)

If you encounter version conflicts, use these exact versions:

```txt
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
google-generativeai==0.3.1
easyocr==1.7.0
torch==2.1.0
Pillow==10.1.0
pandas==2.1.3
sqlalchemy==2.0.23
python-dotenv==1.0.0
```

---

## 🎯 Testing the Complete Flow

### Test 1: Simple Receipt

Create `test_receipt.png` with:
```
Receipt #123
Date: 11/29/2025
Total: 500 PKR
Test Restaurant
```

Upload → Should extract all fields

### Test 2: Multiple Files

Upload 3-5 receipt images at once
→ Should process all successfully

### Test 3: Edit Entry

1. Go to Review page
2. Switch to Edit Mode
3. Change amount
4. Save
→ Should update successfully

### Test 4: Export

1. Go to Export page
2. Select CSV
3. Click Export
→ Should download file

---

## 💾 Backup & Recovery

### Backup Database
```bash
cp database/bookkeeping.db database/bookkeeping_backup.db
```

### Restore Database
```bash
cp database/bookkeeping_backup.db database/bookkeeping.db
```

### Export All Data Before Major Changes
Always export to CSV before:
- Updating code
- Changing database schema
- Testing new features

---

## 🔒 Security Notes

1. **Never commit `.env` file** - it contains your API key
2. **Never share API key publicly**
3. **Add `.env` to `.gitignore`** (already done)
4. **For production:** Use proper authentication

---

## 📈 Performance Optimization

### For Faster Processing:
1. Use smaller images (< 2MB)
2. Process 5-10 files at a time
3. Use clear, high-contrast images
4. Close other applications

### For Better Accuracy:
1. Good lighting in photos
2. Flat, unwrinkled receipts
3. Clear text (not blurry)
4. Avoid shadows

---

## 🎓 Project Structure Explanation

```
backend/
├── main.py              # API endpoints & routes
├── config.py            # Configuration & settings
├── database.py          # Database models & connection
├── models.py            # Pydantic models for validation
└── services/            # Core business logic
    ├── ocr_service.py   # MVP 1: Text extraction
    ├── ai_structuring.py # MVP 2: AI processing
    ├── confidence_scorer.py # MVP 3: Quality checks
    ├── duplicate_detector.py # MVP 4: Duplicate detection
    ├── categorizer.py   # MVP 5: Auto categorization
    └── exporter.py      # MVP 7: Export functionality

frontend/
├── app.py               # Main dashboard (MVP 8)
└── pages/
    ├── 1_📤_Upload.py   # File upload interface
    ├── 2_✏️_Review.py   # MVP 6: Human review
    ├── 3_📊_Dashboard.py # Analytics & stats
    └── 4_💾_Export.py   # Data export interface
```

---

## ✨ You're All Set!

If you've completed all steps above, your application should be fully functional! 🎉

**Next Steps:**
1. Read `QUICKSTART.md` for usage guide
2. Upload your first receipt
3. Explore all features
4. Customize for your needs

---

**Need more help?** Check:
- `README.md` - Detailed documentation
- `QUICKSTART.md` - Quick usage guide
- `http://localhost:8000/docs` - API documentation

**Good luck with your project! 🚀**