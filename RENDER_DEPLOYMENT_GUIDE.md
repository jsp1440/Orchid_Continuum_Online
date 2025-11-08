# Render.com Deployment Guide - The Orchid Continuum
## Complete Step-by-Step Instructions for Deploying to Render.com

**Created:** October 12, 2025  
**For:** Five Cities Orchid Society - Neon One Integration

---

## 🎯 Overview

This guide will help you deploy The Orchid Continuum to Render.com in **30-45 minutes**, making all 19 widgets available for Neon One integration.

**What You'll Get:**
- ✅ Production URL: `https://orchid-continuum.onrender.com`
- ✅ All 19 widgets accessible via iframes
- ✅ 5,915 orchids with enriched metadata
- ✅ Secure PostgreSQL database
- ✅ Google Drive image hosting
- ✅ AI-powered features

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **GitHub Account** - Free account at github.com
2. **Render.com Account** - Free account at render.com
3. **Environment Variables** - Listed below (most already configured)
4. **Google Drive API Credentials** - For image hosting
5. **Optional API Keys** - OpenAI, YouTube (for AI features, optional)

---

## 🔐 Required Environment Variables

### ✅ Already Configured (In Replit):
```bash
DATABASE_URL          # PostgreSQL connection (Neon database)
ADMIN_EMAIL          # Admin account email
ADMIN_PASSWORD       # Admin account password
SESSION_SECRET       # Auto-generated session key
```

### 🔑 You Need to Provide (For Full Features):
```bash
# Google Drive (REQUIRED for images)
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON    # Service account credentials
GOOGLE_DRIVE_FOLDER_ID              # Target folder ID

# AI Features (OPTIONAL)
OPENAI_API_KEY                      # For AI identification and enrichment
ANTHROPIC_API_KEY                   # Alternative AI provider
GOOGLE_API_KEY                      # For Gemini AI

# Media (OPTIONAL)
YOUTUBE_API_KEY                     # For YouTube widget

# Email (OPTIONAL)
SENDGRID_API_KEY                    # For email notifications
```

### 🎯 Minimal Deployment (Start with these):
For basic functionality with all widgets working:
```bash
DATABASE_URL                        # ✅ Already set
SESSION_SECRET                      # ✅ Already set
ADMIN_EMAIL                         # ✅ Already set
ADMIN_PASSWORD                      # ✅ Already set
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON   # ⚠️ Need this for images
GOOGLE_DRIVE_FOLDER_ID             # ⚠️ Need this for images
```

---

## 📦 Step 1: Prepare Your Code for Deployment

### 1.1 Create `.gitignore` File (if not exists)
```bash
# Create .gitignore to exclude sensitive files
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.env
.env.local
*.log
instance/
.webassets-cache
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.DS_Store
node_modules/
*.sqlite
*.db
logs/*.log
attached_assets/
simple_migration/
migration_package/
orchid-continuum-scaffold/
EOF
```

### 1.2 Create `requirements.txt`
```bash
# Generate requirements.txt from current environment
pip freeze > requirements.txt
```

### 1.3 Create `runtime.txt` (Specify Python version)
```bash
echo "python-3.11.9" > runtime.txt
```

### 1.4 Create Render-specific start command file
```bash
# Create render-build.sh for Render deployment
cat > render-build.sh << 'EOF'
#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating necessary directories..."
mkdir -p logs
mkdir -p static/images
mkdir -p attached_assets

echo "Build complete!"
EOF

chmod +x render-build.sh
```

---

## 🚀 Step 2: Deploy to Render.com

### Option A: Direct GitHub Integration (Recommended)

#### 2.1 Push to GitHub

**Create new GitHub repository:**
```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment for Render.com"

# Create GitHub repo (via GitHub website or CLI)
# Then add remote
git remote add origin https://github.com/YOUR_USERNAME/orchid-continuum.git

# Push to GitHub
git push -u origin main
```

#### 2.2 Connect to Render.com

1. **Go to:** https://render.com
2. **Click:** "New +" → "Web Service"
3. **Connect GitHub:**
   - Click "Connect GitHub"
   - Authorize Render
   - Select your `orchid-continuum` repository

#### 2.3 Configure Web Service

**Basic Settings:**
```yaml
Name: orchid-continuum
Region: Oregon (US West) - or closest to you
Branch: main
Root Directory: (leave blank)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --reuse-port main:app
```

**Advanced Settings:**
```yaml
Instance Type: Free (or Starter $7/month for better performance)
Auto-Deploy: Yes (recommended)
```

#### 2.4 Add Environment Variables

In Render dashboard, go to "Environment" tab and add:

**Required:**
```bash
DATABASE_URL = [Your Neon PostgreSQL URL from Replit]
SESSION_SECRET = [Generate: openssl rand -base64 32]
ADMIN_EMAIL = [Your admin email]
ADMIN_PASSWORD = [Your admin password]

# Google Drive (CRITICAL for images)
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON = [Your service account JSON]
GOOGLE_DRIVE_FOLDER_ID = [Your Google Drive folder ID]
```

**Optional (Add later for full features):**
```bash
OPENAI_API_KEY = sk-...
YOUTUBE_API_KEY = AIza...
ANTHROPIC_API_KEY = sk-ant-...
SENDGRID_API_KEY = SG...
```

#### 2.5 Deploy!
- Click "Create Web Service"
- Wait 5-10 minutes for deployment
- Your app will be live at: `https://orchid-continuum.onrender.com`

---

### Option B: Manual Docker Deployment

If you prefer Docker, create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs static/images attached_assets

# Expose port
EXPOSE 5000

# Start command
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --reuse-port main:app
```

Then in Render:
1. Select "Docker" as runtime
2. Let Render auto-detect Dockerfile
3. Add environment variables as above

---

## 🗄️ Step 3: Database Migration

### Option A: Use Existing Neon Database (Recommended)

**Your current Neon database has:**
- ✅ 5,915 orchids with enriched data
- ✅ All schemas and relationships
- ✅ GBIF/EOL enrichment data
- ✅ Optimized indexes

**Just copy the DATABASE_URL to Render:**
```bash
DATABASE_URL=postgresql://username:password@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/database_name
```

### Option B: Create New Render PostgreSQL

If you want a separate production database:

1. In Render Dashboard: "New +" → "PostgreSQL"
2. Name: `orchid-continuum-db`
3. Region: Same as web service
4. Plan: Free (or Starter for production)
5. Copy the **Internal Database URL**
6. Add to web service environment variables

**Then migrate data:**
```bash
# Export from Neon
pg_dump $OLD_DATABASE_URL > orchid_backup.sql

# Import to Render
psql $NEW_DATABASE_URL < orchid_backup.sql
```

---

## 🔗 Step 4: Configure Neon One Integration

### 4.1 Update Widget URLs

After deployment, your widgets are available at:
```
Base URL: https://orchid-continuum.onrender.com
```

### 4.2 Add to Neon One CMS

**Example - Homepage:**
```html
<h2>Featured Orchid of the Day</h2>
<iframe src="https://orchid-continuum.onrender.com/widget/orchid-of-the-day" 
        width="100%" height="600" frameborder="0" 
        style="border:1px solid #ddd; border-radius:8px;">
</iframe>
```

**See:** `NEON_ONE_IFRAME_CODES.html` for all 19 widget codes

### 4.3 Test Widgets

Visit each widget to confirm:
1. ✅ `/widget/orchid-of-the-day` - Orchid of the Day
2. ✅ `/gallery-hub` - Gallery Hub
3. ✅ `/youtube/` - YouTube Channel
4. ✅ `/newsletters` - Newsletter Archive
5. ✅ (See complete list in iframe codes file)

---

## 🔧 Step 5: Post-Deployment Configuration

### 5.1 Enable HTTPS (Automatic)
Render automatically provides free SSL certificates. All widgets will work with `https://`

### 5.2 Configure Custom Domain (Optional)

If you want `orchids.fivecitiesorchidsociety.org`:

1. In Render: Settings → Custom Domains
2. Add: `orchids.fivecitiesorchidsociety.org`
3. Update DNS records at your domain registrar:
   ```
   Type: CNAME
   Name: orchids
   Value: orchid-continuum.onrender.com
   ```
4. Wait for DNS propagation (5-60 minutes)

### 5.3 Set Up Monitoring (Optional)

**Render built-in monitoring:**
- Go to Metrics tab
- View: Response times, error rates, memory usage

**External monitoring (optional):**
- UptimeRobot (free)
- Pingdom
- StatusCake

---

## 🎯 Step 6: Verify Deployment

### Checklist:
- [ ] Application loads at Render URL
- [ ] Homepage displays without errors
- [ ] Database connection working (5,915 orchids visible)
- [ ] Images loading from Google Drive
- [ ] All 19 widgets accessible
- [ ] Admin dashboard accessible (if needed)
- [ ] YouTube widget shows videos
- [ ] Newsletter archive displays
- [ ] No console errors in browser

### Test URLs:
```bash
# Main app
https://orchid-continuum.onrender.com/

# Sample widgets
https://orchid-continuum.onrender.com/widget/orchid-of-the-day
https://orchid-continuum.onrender.com/gallery-hub
https://orchid-continuum.onrender.com/youtube/
https://orchid-continuum.onrender.com/newsletters

# Health check
https://orchid-continuum.onrender.com/api/health
```

---

## ⚙️ Troubleshooting

### Problem: Application won't start

**Check:**
1. Build logs in Render dashboard
2. Ensure `requirements.txt` is complete
3. Verify Python version in `runtime.txt`
4. Check start command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 main:app`

**Solution:**
```bash
# Rebuild with specific Python version
echo "python-3.11.9" > runtime.txt
git commit -am "Fix Python version"
git push
```

### Problem: Database connection errors

**Check:**
1. DATABASE_URL environment variable is set
2. URL format: `postgresql://user:pass@host/db`
3. Database is accessible from Render IPs

**Solution:**
```bash
# Test connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM orchid_record;"
```

### Problem: Images not loading

**Check:**
1. `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` is set correctly
2. `GOOGLE_DRIVE_FOLDER_ID` is correct
3. Service account has access to Drive folder

**Solution:**
```bash
# Verify Drive credentials format
echo $GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON | jq .
```

### Problem: Widgets not displaying in Neon One

**Check:**
1. Iframe `src` URL is correct (with https://)
2. No mixed content warnings (http in https page)
3. CORS headers allow iframe embedding

**Solution:**
```python
# Add to app.py if needed
from flask import make_response

@app.after_request
def add_cors_headers(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response
```

### Problem: Slow performance

**Upgrade instance type:**
1. Render Dashboard → Settings
2. Change from "Free" to "Starter" ($7/month)
3. Increases memory and CPU

**Optimize database:**
```bash
# Already optimized with 12 indexes!
# See performance_optimization_system.py
```

---

## 💰 Cost Breakdown

### Free Tier (Good for testing):
- **Render Web Service:** Free (spins down after 15 min inactivity)
- **Render PostgreSQL:** Free (90 days, then $7/month)
- **Neon PostgreSQL:** Free tier (3GB storage)
- **Total:** $0-7/month

### Production Tier (Recommended):
- **Render Web Service Starter:** $7/month (always on)
- **Render PostgreSQL Starter:** $7/month (1GB RAM)
- **Or use Neon Pro:** $19/month (10GB storage)
- **Total:** $14-26/month

### With All Features:
- **Render Starter:** $7/month
- **Database:** $7/month
- **OpenAI API:** ~$5/month (usage-based)
- **YouTube API:** Free (quota-based)
- **Total:** ~$19/month

---

## 📊 Performance Expectations

### With Free Tier:
- **Response Time:** 200-500ms (after spin-up)
- **Spin-up Time:** 30-60 seconds (after idle)
- **Concurrent Users:** 10-20

### With Starter Tier:
- **Response Time:** 100-200ms
- **Spin-up Time:** Always on
- **Concurrent Users:** 100-200

### Database:
- **Current Records:** 5,915 orchids
- **Index Performance:** Optimized for 100K+ records
- **Query Speed:** <100ms for most queries

---

## 🚀 Quick Start Commands

**Complete deployment in 5 steps:**

```bash
# 1. Create runtime.txt
echo "python-3.11.9" > runtime.txt

# 2. Create requirements.txt
pip freeze > requirements.txt

# 3. Commit everything
git add .
git commit -m "Ready for Render deployment"

# 4. Push to GitHub
git push origin main

# 5. Deploy on Render (via web UI)
# - Connect GitHub repo
# - Add environment variables
# - Click Deploy
```

**After deployment:**
1. Visit: `https://orchid-continuum.onrender.com`
2. Copy widget iframes from `NEON_ONE_IFRAME_CODES.html`
3. Paste into Neon One CMS
4. Publish your site!

---

## ✅ Final Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Database connected and populated (5,915 orchids)
- [ ] Google Drive images loading
- [ ] All 19 widgets tested and working
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active (automatic)
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Neon One iframes tested in CMS
- [ ] Tuesday deadline confirmed achievable ✅

---

## 📞 Support Resources

**Render Documentation:**
- https://render.com/docs/web-services
- https://render.com/docs/deploy-flask

**Database Help:**
- Render PostgreSQL: https://render.com/docs/databases
- Neon Docs: https://neon.tech/docs

**Troubleshooting:**
- Render Community: https://community.render.com
- Render Status: https://status.render.com

---

## 🎯 Success Metrics

**You'll know deployment succeeded when:**

1. ✅ Application loads at Render URL
2. ✅ All 19 widgets work in iframes
3. ✅ Images display from Google Drive
4. ✅ Database shows 5,915 orchids
5. ✅ Neon One CMS displays widgets correctly
6. ✅ Tuesday deadline met

---

**🎉 Your Five Cities Orchid Society website will be LIVE with all features!**

**Estimated Total Time:** 30-45 minutes  
**Tuesday Deadline:** ACHIEVABLE ✅
