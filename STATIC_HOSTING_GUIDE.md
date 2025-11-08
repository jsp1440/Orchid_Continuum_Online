# STATIC IMAGE HOSTING GUIDE

## 🎯 What This Does

Downloads all 10,534 GBIF orchid images and hosts them **directly with your Flask app** on Render. No Google Drive needed!

---

## 🚀 HOW TO USE

### Step 1: Download Images to Static Folder
```bash
python3 download_to_static.py
```

**What happens:**
- Downloads 100 images at a time
- Saves to `static/images/orchid/`
- Updates database with static URLs
- Creates SHA256 hashes for verification
- Logs everything to `static_image_download.log`

**Time:** ~8-14 hours for all 10,534 images (run overnight!)

### Step 2: Test Locally
Your images are immediately available at:
```
http://localhost:5000/static/images/orchid/orchid_1.jpg
http://localhost:5000/static/images/orchid/orchid_2.jpg
...
```

### Step 3: Deploy to Render
When you deploy to Render:
1. Push code to GitHub (images go with it)
2. Render builds and deploys
3. Images available at:
   ```
   https://orchid-continuum.onrender.com/static/images/orchid/orchid_1.jpg
   ```

---

## 📁 DIRECTORY STRUCTURE

```
your-project/
├── static/
│   └── images/
│       └── orchid/
│           ├── orchid_1.jpg
│           ├── orchid_2.jpg
│           ├── orchid_3.jpg
│           └── ... (10,534 total)
├── templates/
├── app.py
└── download_to_static.py
```

---

## 💾 DATABASE UPDATES

Each image record gets updated with:
```python
local_path = "/static/images/orchid/orchid_123.jpg"
file_sha256 = "d404b8258d7301de..."
perceptual_hash = "8f7a3c..."
download_status = "static_hosted"
downloaded_at = "2025-11-01 07:30:00"
```

---

## ⏯️ STOP/RESUME

**Stop:** Press `Ctrl+C` (progress is saved)  
**Resume:** Just run `python3 download_to_static.py` again

The script automatically continues where it left off!

---

## 📊 MONITOR PROGRESS

### Watch Live:
```bash
tail -f static_image_download.log
```

### Check Database:
```sql
SELECT 
  COUNT(*) FILTER (WHERE download_status = 'static_hosted') as hosted,
  COUNT(*) FILTER (WHERE download_status IS NULL) as remaining,
  COUNT(*) as total
FROM orchid_images
WHERE image_source LIKE '%GBIF%';
```

---

## 🌐 USING IMAGES IN YOUR WEBSITE

### In Jinja2 Templates:
```html
<img src="{{ image.local_path }}" alt="Orchid">
```

### In Routes:
```python
@app.route('/orchid/<int:id>')
def show_orchid(id):
    orchid = OrchidImage.query.get(id)
    # orchid.local_path = "/static/images/orchid/orchid_123.jpg"
    return render_template('orchid.html', orchid=orchid)
```

Flask automatically serves files from `/static/` directory!

---

## 📦 STORAGE REQUIREMENTS

**Local (Replit):**
- ~10-20 GB for all images
- Replit provides enough space

**Render:**
- Free tier: 512MB RAM, limited disk
- **Upgrade to Starter ($7/mo)**: 512MB RAM, more disk space
- Images deploy with your app automatically

**Note:** If all images don't fit on Render free tier, download in batches and deploy the most important species first.

---

## ✅ BENEFITS

**Why This is Better:**
- ✅ **No Google setup needed** - works immediately
- ✅ **Hosted URLs** - your website can display images
- ✅ **You control hosting** - no external dependencies
- ✅ **Free** - included with Render hosting
- ✅ **Fast** - images served from same server as your app
- ✅ **Backup included** - code + images in GitHub
- ✅ **Version controlled** - images tracked in Git

---

## 🛡️ DATA PROTECTION

### SHA256 Hashes:
Every image verified with cryptographic hash to ensure integrity

### Perceptual Hashes:
Detect visual duplicates and verify image content

### Download Status Tracking:
Database knows which images are successfully hosted

### Auto-Resume:
Script continues from last successful image if interrupted

---

## 🔧 TROUBLESHOOTING

### "Disk space full"
- Download fewer images (reduce BATCH_SIZE)
- Deploy to Render in batches
- Upgrade Render plan

### "Download failed"
- Normal for some GBIF URLs
- Script retries 3 times automatically
- Failed URLs logged for manual review

### "Images not showing on Render"
- Make sure `/static/` folder is in GitHub
- Check Render deployment logs
- Verify Flask is configured to serve static files

---

## 🎉 SUCCESS!

Once complete:
- ✅ All images stored locally
- ✅ Database updated with static URLs
- ✅ Ready to deploy to Render
- ✅ Website can display all orchid images
- ✅ No external dependencies!

**Now you can test your widgets this weekend!** 🌺
