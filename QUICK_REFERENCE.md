# 🚀 Quick Reference Guide

## ⚡ 3-Minute Setup

```powershell
# 1. Install new dependency
pip install PyPDF2==3.0.1

# 2. Delete old database
rm database/bookkeeping.db

# 3. Copy all updated artifact files to your project

# 4. Start backend
python -m uvicorn backend.main:app --reload

# 5. Start frontend (new terminal)
streamlit run frontend/app.py
```

---

## 📁 Files to Update

### Backend (Copy entire files):
1. `backend/main.py`
2. `backend/database.py`
3. `backend/models.py`
4. `backend/services/ai_structuring.py`
5. `backend/services/ocr_service.py`
6. `backend/services/exporter.py`

### Frontend (Copy entire files):
7. `frontend/pages/1_📤_Upload.py`
8. `frontend/pages/2_✏️_Review.py`
9. `frontend/pages/3_📊_Dashboard.py`

### New File (Create):
10. `frontend/pages/5_💰_Balance.py` ← **NEW FILE**

---

## 🎯 What Changed?

| Feature | What It Does | Where to Find |
|---------|--------------|---------------|
| 💰 Income/Expense | Split amounts, auto-detect type | All pages |
| 📄 PDF Fix | No more crashes | Upload page |
| 🗑️ Delete Fix | Works everywhere now | Review page |
| 📊 New Chart | Monthly income vs expense | Dashboard |
| ✍️ Manual Entry | Add without files | Upload page (expander) |
| 💰 Balance | Track finances | New Balance page |
| 🔄 Auto Update | Balance updates live | Everywhere |

---

## 🧪 Quick Test

1. **Delete database**: `rm database/bookkeeping.db`
2. **Restart backend**
3. **Go to Balance page** → Set opening balance: 10,000
4. **Go to Upload** → Manual entry → Add income: 5,000
5. **Check Balance page** → Should show 15,000
6. **Upload receipt** → Adds expense
7. **Check Balance** → Should decrease

---

## 🆘 Quick Fixes

### Error: "No column 'income'"
→ Delete database, restart backend

### Error: "Cannot import Balance"
→ Update `backend/database.py`

### Balance page not found
→ Create `frontend/pages/5_💰_Balance.py`

### Manual entry doesn't work
→ Update `backend/main.py` with new endpoints

---

## 📊 New API Endpoints

```
POST /transactions/manual - Add transaction manually
GET  /balance - Get current balance
POST /balance/set-opening - Set opening balance
```

---

## ✅ Success Indicators

When everything works:

- ✅ Backend starts without errors
- ✅ 5 pages in sidebar (including Balance)
- ✅ Manual entry form exists in Upload
- ✅ Income shows green 💰
- ✅ Expense shows red 💸
- ✅ Dashboard has monthly chart
- ✅ Balance page loads
- ✅ Delete works in Edit Mode

---

**All updates are in the artifacts. Just copy-paste and restart!** 🎉