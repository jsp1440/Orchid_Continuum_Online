# OAuth Drive Uploader Setup - fcospresident@gmail.com

## 🎯 What This Does

Uploads all 107,000+ orchid images to YOUR 2TB Google Drive and populates your Google Sheet using your fcospresident@gmail.com account.

---

## ⚙️ **One-Time Setup (5 Minutes)**

### **Step 1: Create OAuth Credentials**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Make sure you're logged in as **fcospresident@gmail.com**
3. Click **"+ Create Credentials" → "OAuth client ID"**
4. Select **"Desktop app"**
5. Name it: "Orchid Continuum Uploader"
6. Click **"Create"**
7. Click **"Download JSON"** (downloads `client_secret_xxx.json`)

---

### **Step 2: Add to Replit Secrets**

1. Open the downloaded JSON file
2. Copy the **entire contents**
3. In Replit, click **"Secrets"** (lock icon)
4. Add new secret:
   - **Key**: `GOOGLE_OAUTH_CREDENTIALS`
   - **Value**: Paste the entire JSON
5. Click **"Add Secret"**

---

### **Step 3: Enable APIs (if not already done)**

1. Go to: https://console.cloud.google.com/apis/library
2. Search for "Google Drive API" → Click **Enable**
3. Search for "Google Sheets API" → Click **Enable**

---

## 🚀 **Running the Uploader**

### **Test Run (10 images)**

```bash
python3 oauth_drive_uploader.py 10
```

**What happens:**
1. Opens a URL in the terminal
2. Copy that URL and open in browser
3. Sign in with fcospresident@gmail.com
4. Click "Allow"
5. Copy the code shown
6. Paste back into Replit terminal
7. Uploads 10 test images

---

### **Full Run (All 107,000+ images)**

Once test works:

```bash
# Start in background (12-24 hours)
nohup python3 oauth_drive_uploader.py > oauth_upload_output.log 2>&1 &

# Save process ID
echo $! > oauth_upload.pid

# Monitor progress
tail -f oauth_upload.log

# Stop if needed
kill $(cat oauth_upload.pid)
```

---

## 📊 **What Gets Created**

### **In Your Google Drive Folder**
- **Location**: https://drive.google.com/drive/folders/1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS
- **Files**: 107,000+ images named like `Cattleya_labiata_5916.jpg`
- **Storage used**: ~50-100GB of your 2TB

### **In Your Google Sheet**
- **Location**: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz/edit
- **Columns**: ID, Scientific Name, Genus, Species, Country, Coordinates, Drive URL, etc.
- **Rows**: 107,000+ (one per image)

### **In Your Database**
- `google_drive_url` column gets populated with Drive links

---

## 🔧 **Troubleshooting**

### **"GOOGLE_OAUTH_CREDENTIALS not found"**
- Make sure you added the JSON to Replit Secrets
- Key must be exactly: `GOOGLE_OAUTH_CREDENTIALS`

### **"This app isn't verified"**
- Normal! Click "Advanced" → "Go to Orchid Continuum (unsafe)"
- It's YOUR app, totally safe

### **"Access denied"**
- Make sure you're signing in with fcospresident@gmail.com
- Check that you clicked "Allow" for all permissions

### **"Token expired"**
- Delete `token.json` file
- Run again to re-authenticate

---

## ✅ **Progress Monitoring**

While running, check:

```bash
# Live progress
tail -f oauth_upload.log

# Stats so far
grep "Progress:" oauth_upload.log | tail -5

# Check Drive folder
# Opens in browser: https://drive.google.com/drive/folders/1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS

# Check Sheet
# Opens in browser: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz/edit
```

---

## ⏱️ **Timeline**

- **First run**: 5 minutes (one-time OAuth setup)
- **Test run (10 images)**: ~2 minutes
- **Full run (107,000 images)**: 12-24 hours

**Rate**: ~100-200 images/minute = ~9-18 hours

---

## 🎯 **After Completion**

You'll have:
- ✅ All images in YOUR Google Drive
- ✅ Fully populated Google Sheet
- ✅ Database updated with Drive URLs
- ✅ Julius can access everything easily

---

**Ready to start? Run the test first:**
```bash
python3 oauth_drive_uploader.py 10
```
