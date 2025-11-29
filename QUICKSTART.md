# 🚀 Quick Start Guide - AI Bookkeeping Engine

Get up and running in **5 minutes**!

## ⚡ Super Quick Setup

### Step 1: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

This will install everything you need.

### Step 2: Get Free API Key (1 minute)

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Step 3: Configure Environment (30 seconds)

```bash
# Create .env file
cp .env.example .env

# Edit .env and paste your API key
# Change: GEMINI_API_KEY=your_gemini_api_key_here
# To:     GEMINI_API_KEY=your_actual_key_here
```

Or manually create `.env` file with this content:
```
GEMINI_API_KEY=your_actual_api_key_here
DATABASE_URL=sqlite:///./database/bookkeeping.db
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=data/uploads
PROCESSED_DIR=data/processed
EXPORT_DIR=data/exports
CONFIDENCE_THRESHOLD=0.70
DEFAULT_CURRENCY=PKR
```

### Step 4: Run the App (1 minute)

**Option A: Easy Way (Recommended)**
```bash
python start.py
```
This starts both backend and frontend automatically!

**Option B: Manual Way**

Open TWO terminals:

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```

### Step 5: Use the App! ✨

Your browser will open automatically at `http://localhost:8501`

If not, manually open: http://localhost:8501

---

## 📝 First Time Usage

### 1. Upload a Receipt
- Go to "📤 Upload" page
- Click "Browse files"
- Select a receipt image (JPG/PNG)
- Click "🚀 Process Files"

### 2. Check Results
- View extracted data
- See confidence scores
- Note any flagged items

### 3. Review & Edit
- Go to "✏️ Review" page
- Switch to "Edit Mode"
- Fix any incorrect extractions
- Save changes

### 4. Export Data
- Go to "💾 Export" page
- Choose CSV or Excel
- Click "🚀 Export Data"
- Download your clean data

---

## 🎯 Test Files

Create a simple test receipt:

**Save this as `test_receipt.txt`:**
```
KFC Store #23
Date: 12/11/2025
Total: 1450 PKR
Zinger Combo Meal
```

Take a screenshot of it and upload!

---

## ⚠️ Common Issues & Fixes

### "Backend API is not running"
**Fix:** Make sure Terminal 1 is running with the backend
```bash
uvicorn backend.main:app --reload
```

### "GEMINI_API_KEY not found"
**Fix:** Check your `.env` file exists and has the key

### "Module not found"
**Fix:** Install requirements again
```bash
pip install -r requirements.txt
```

### "Port 8000 already in use"
**Fix:** Kill the process using port 8000
```bash
# On Mac/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 🎓 Understanding the Flow

```
1. Upload File → OCR Extraction
2. Raw Text → AI Structuring
3. Structured Data → Confidence Scoring
4. Check for Duplicates
5. Auto Categorization
6. Human Review (Optional)
7. Export Clean Data
```

---

## 💡 Pro Tips

1. **Start Small:** Upload 1-2 files first to test
2. **Check Confidence:** Review items with confidence < 70%
3. **Batch Upload:** Process 5-10 files at a time
4. **Regular Exports:** Export data frequently as backup

---

## 📊 What Each Page Does

| Page | Purpose |
|------|---------|
| 🏠 Home | Overview & statistics |
| 📤 Upload | Add new receipts/documents |
| ✏️ Review | Edit & verify extractions |
| 📊 Dashboard | View analytics |
| 💾 Export | Download clean data |

---

## 🔧 Advanced Usage

### Custom Categories
Edit `backend/config.py` and modify `CATEGORY_KEYWORDS`

### Change Currency
Edit `.env` and set `DEFAULT_CURRENCY=USD` (or any other)

### Adjust Confidence Threshold
Edit `.env` and set `CONFIDENCE_THRESHOLD=0.8` (higher = stricter)

---

## 🆘 Need Help?

1. Check `README.md` for detailed docs
2. Visit `http://localhost:8000/docs` for API documentation
3. Check terminal logs for error messages

---

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] `.env` file configured with API key
- [ ] Backend running on port 8000
- [ ] Frontend running on port 8501
- [ ] Browser opened at localhost:8501
- [ ] Test file uploaded successfully
- [ ] Data extracted and visible

If all checked ✅ - You're good to go! 🎉

---

**Happy Bookkeeping! 📚✨**