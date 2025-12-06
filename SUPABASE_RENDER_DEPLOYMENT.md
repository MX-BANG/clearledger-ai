# 🚀 Deploy with Supabase + Render.com

Complete step-by-step guide to deploy your AI Bookkeeping Engine using Supabase (free PostgreSQL) and Render.com (free hosting).

---

## 📋 What You'll Need

- ✅ GitHub account with your code pushed
- ✅ Supabase account (https://supabase.com)
- ✅ Render.com account (https://render.com)
- ✅ Gemini API key

---

## 🎯 Overview

1. **Supabase**: Provides free PostgreSQL database (500MB storage, unlimited API requests)
2. **Render.com**: Hosts backend (FastAPI) and frontend (Streamlit) for free

---

## 📝 PART 1: Update Your Code

### Step 1: Update Files

You need to update **2 files**:

#### 1.1 Update `backend/database_cloud.py`

Copy the updated `database_cloud.py` from the artifact above. Key changes:
- Added SSL requirement for Supabase
- Optimized connection pool for free tier
- Added connection timeout settings

#### 1.2 Update `render.yaml`

Copy the updated `render.yaml` from the artifact above. Key changes:
- Removed PostgreSQL service (using Supabase instead)
- DATABASE_URL will be added manually

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Update for Supabase + Render deployment"
git push origin main
```

---

## 🗄️ PART 2: Setup Supabase Database

### Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Click **"Start your project"** or **"New Project"**
3. Sign in with GitHub (recommended)

### Step 2: Create New Project

1. Click **"New Project"**
2. Fill in details:
   ```
   Name: bookkeeping-db
   Database Password: [Create a strong password - SAVE THIS!]
   Region: Choose closest to you (e.g., Singapore, US East)
   Plan: Free
   ```
3. Click **"Create new project"**
4. Wait 2-3 minutes for project to initialize

### Step 3: Get Database Connection String

1. Once project is ready, click **"Settings"** (gear icon in sidebar)
2. Click **"Database"** in the settings menu
3. Scroll to **"Connection string"** section
4. Select **"URI"** tab
5. Copy the connection string (looks like this):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```
6. **IMPORTANT:** Replace `[YOUR-PASSWORD]` with the actual password you created
7. **Save this connection string** - you'll need it soon!

**Example:**
```
postgresql://postgres:mySecurePass123@db.abcdefgh.supabase.co:5432/postgres
```

### Step 4: Enable Connection Pooling (Optional but Recommended)

1. In Supabase Dashboard → Settings → Database
2. Scroll to **"Connection pooling"**
3. Toggle **"Use connection pooling"** to ON
4. Copy the **"Connection pooler"** string (port 6543)
5. This is better for production, but the regular connection string works too

---

## 🌐 PART 3: Deploy to Render.com

### Step 1: Create Render Account

1. Go to https://render.com
2. Click **"Get Started"**
3. Sign up with **GitHub** (recommended)
4. Authorize Render to access your repositories

### Step 2: Deploy Backend (FastAPI)

#### 2.1 Create Web Service

1. In Render Dashboard, click **"New +"** (top right)
2. Select **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Click **"Next"**

#### 2.2 Connect Repository

1. Find your `ai-bookkeeping-engine` repository
2. Click **"Connect"**

#### 2.3 Configure Backend Service

Fill in these settings:

```
Name: bookkeeping-api
Region: [Same as Supabase - e.g., Singapore]
Branch: main
Root Directory: (leave empty)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

#### 2.4 Select Plan

- Choose **"Free"** plan
- Note: Free services sleep after 15 minutes of inactivity

#### 2.5 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these THREE variables:

**Variable 1:**
```
Key: DATABASE_URL
Value: [Paste your Supabase connection string from Part 2, Step 3]
Example: postgresql://postgres:mypass@db.abcd.supabase.co:5432/postgres
```

**Variable 2:**
```
Key: GEMINI_API_KEY
Value: [Your Gemini API key]
```

**Variable 3:**
```
Key: PYTHON_VERSION
Value: 3.10.9
```

#### 2.6 Deploy Backend

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. Watch the logs - look for:
   ```
   ✅ Using PostgreSQL (production mode - Supabase)
   INFO: Application startup complete.
   ```
4. **Copy the backend URL** (looks like: `https://bookkeeping-api-xxxx.onrender.com`)

### Step 3: Deploy Frontend (Streamlit)

#### 3.1 Create Another Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect the **same repository**

#### 3.2 Configure Frontend Service

```
Name: bookkeeping-frontend
Region: [Same as backend]
Branch: main
Build Command: pip install -r requirements.txt
Start Command: streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

#### 3.3 Add Environment Variables

Add these TWO variables:

**Variable 1:**
```
Key: API_URL
Value: [Your backend URL from Step 2.6]
Example: https://bookkeeping-api-xxxx.onrender.com
```

**Variable 2:**
```
Key: PYTHON_VERSION
Value: 3.10.9
```

#### 3.4 Deploy Frontend

1. Click **"Create Web Service"**
2. Wait 5-10 minutes
3. Look for: `You can now view your Streamlit app in your browser.`
4. Your frontend URL: `https://bookkeeping-frontend-xxxx.onrender.com`

---

## ✅ PART 4: Test Your Deployment

### Step 1: Test Backend

1. Visit: `https://bookkeeping-api-xxxx.onrender.com`
2. Should see:
   ```json
   {
     "status": "running",
     "message": "AI Bookkeeping Cleanup Engine API",
     "version": "1.0.0"
   }
   ```

3. Test API docs: `https://bookkeeping-api-xxxx.onrender.com/docs`
4. Should see Swagger UI

### Step 2: Test Frontend

1. Visit: `https://bookkeeping-frontend-xxxx.onrender.com`
2. Should see dashboard load
3. Check if "✅ Backend API is running" appears

### Step 3: Test Full Workflow

1. **Go to Balance page** → Set opening balance (e.g., 10,000)
2. **Go to Upload page** → Add manual transaction:
   - Amount: 5,000
   - Type: income
   - Category: Salary
3. **Check Balance page** → Should show 15,000
4. **Upload a receipt image**
5. **Go to Review page** → Should see extracted data
6. **Try Export** → Download should work

---

## 🔍 PART 5: Verify Database Connection

### Check Supabase Tables

1. Go to Supabase Dashboard
2. Click **"Table Editor"** in sidebar
3. You should see tables:
   - `transactions`
   - `balance`
4. Click on tables to see data

### Check Data

1. After adding transactions in your app
2. Refresh Supabase Table Editor
3. You should see your transactions stored in PostgreSQL!

---

## 🐛 Troubleshooting

### Backend Shows "Database Connection Error"

**Check:**
1. DATABASE_URL is correct in Render environment variables
2. No extra spaces in the connection string
3. Password in connection string is correct
4. SSL mode is included (should have `?sslmode=require`)

**Fix:**
```bash
# Correct format:
postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres?sslmode=require

# Common mistakes:
# ❌ Missing password
# ❌ Extra spaces
# ❌ Missing ?sslmode=require
```

### Frontend Can't Connect to Backend

**Check:**
1. API_URL in frontend environment variables
2. Backend is fully deployed (check logs)
3. Backend URL doesn't have trailing slash

**Fix:**
```bash
# Correct:
https://bookkeeping-api-xxxx.onrender.com

# Wrong:
https://bookkeeping-api-xxxx.onrender.com/
```

### "Service Unavailable" Error

**Cause:** Free tier services sleep after 15 minutes

**Fix:** 
- First request takes 30-60 seconds to wake up
- Be patient, it will load
- Consider upgrading to paid plan for always-on

### Deployment Failed

**Check Render Logs:**
1. Go to your service in Render
2. Click **"Logs"** tab
3. Look for error messages

**Common Issues:**
- Missing dependencies → Check `requirements.txt`
- Port issues → Make sure using `$PORT`
- Import errors → Check file paths

---

## 💰 Free Tier Limits

### Supabase Free Tier:
- ✅ 500MB database storage
- ✅ Unlimited API requests
- ✅ Up to 2GB bandwidth per month
- ✅ Auto-pauses after 1 week of inactivity (easy to restart)

### Render Free Tier (Per Service):
- ✅ 750 hours/month runtime
- ✅ Automatic HTTPS
- ✅ Continuous deployment from Git
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ Takes 30-60 sec to wake up

**Total Cost: $0/month** 🎉

---

## 🔒 Security Best Practices

### Environment Variables
- ✅ Never commit `.env` to Git
- ✅ Use Render's environment variables
- ✅ Rotate passwords regularly
- ✅ Use strong database passwords

### Database Security
- ✅ Enable Row Level Security (RLS) in Supabase (optional)
- ✅ Use connection pooling
- ✅ Monitor query performance

---

## 📊 Monitoring

### Supabase Dashboard
- Monitor database size
- Check active connections
- View query logs

### Render Dashboard
- Monitor service health
- Check logs for errors
- View deployment history

---

## 🎯 Quick Reference

| Item | URL/Value |
|------|-----------|
| **Supabase Dashboard** | https://app.supabase.com |
| **Render Dashboard** | https://dashboard.render.com |
| **Your Backend** | https://bookkeeping-api-xxxx.onrender.com |
| **Your Frontend** | https://bookkeeping-frontend-xxxx.onrender.com |
| **API Docs** | https://bookkeeping-api-xxxx.onrender.com/docs |
| **Database** | Supabase PostgreSQL |

---

## 📝 Deployment Checklist

### Before Deployment:
- [ ] Code pushed to GitHub
- [ ] `database_cloud.py` updated
- [ ] `render.yaml` updated
- [ ] Gemini API key ready

### Supabase Setup:
- [ ] Project created
- [ ] Database password saved
- [ ] Connection string copied

### Render Backend:
- [ ] Web service created
- [ ] DATABASE_URL added
- [ ] GEMINI_API_KEY added
- [ ] Backend deployed successfully
- [ ] Backend URL copied

### Render Frontend:
- [ ] Web service created
- [ ] API_URL added
- [ ] Frontend deployed successfully
- [ ] Can access frontend

### Testing:
- [ ] Backend health check works
- [ ] Frontend loads
- [ ] Can add manual transaction
- [ ] Balance tracking works
- [ ] File upload works
- [ ] Data appears in Supabase

---

## 🆘 Getting Help

**If stuck:**

1. **Check Render logs** (most important!)
   - Service → Logs tab
   - Look for error messages

2. **Check Supabase logs**
   - Dashboard → Logs
   - Look for connection errors

3. **Verify environment variables**
   - Render → Service → Environment
   - Check all values are correct

4. **Test database connection**
   - Backend logs should show: "✅ Using PostgreSQL"

---

## 🎉 Success!

Once everything is working:

✅ Your app is **live on the internet**  
✅ Anyone can access it via the frontend URL  
✅ Data is stored in **cloud PostgreSQL**  
✅ Automatic HTTPS included  
✅ **100% FREE**  

**Share your URL:**
```
Frontend: https://bookkeeping-frontend-xxxx.onrender.com
```

---

## 🚀 Next Steps

1. **Custom Domain (Optional)**
   - Buy domain from Namecheap/GoDaddy
   - Connect in Render settings

2. **Keep Services Awake (Optional)**
   - Use UptimeRobot or cron-job.org
   - Ping your app every 10 minutes

3. **Monitor Usage**
   - Check Supabase storage usage
   - Monitor Render bandwidth

4. **Upgrade if Needed**
   - Render paid plan: $7/month (no sleep)
   - Supabase Pro: $25/month (more storage)

---

**Congratulations! Your AI Bookkeeping Engine is now deployed! 🎊**

Total deployment time: ~30 minutes  
Total cost: **$0/month** 💰