# 🚀 Colab Parallel Upload - Setup Instructions

**Upload 107K images in ~1-2 days instead of 46 days!**

---

## 📱 **From Your iPad:**

### **Step 1: Download token.json from Replit**
1. Open Replit in Safari
2. Find `token.json` in the file list
3. Right-click → Download
4. Save to Files app

### **Step 2: Open Colab Notebook**
1. Download `COLAB_PARALLEL_UPLOADER.ipynb` from Replit
2. Go to: https://colab.research.google.com
3. Click **File → Upload notebook**
4. Upload the `.ipynb` file

### **Step 3: Upload token.json to Colab**
1. In Colab, run Cell 1 (installs dependencies)
2. Run Cell 2 (uploads token.json)
3. Click the file upload button
4. Select `token.json` from Files app

### **Step 4: Copy DATABASE_URL**
1. In Replit: Open **Secrets** (padlock icon)
2. Find `DATABASE_URL`
3. Copy the entire value
4. In Colab: Run Cell 3, paste when prompted

### **Step 5: Start Upload!**
1. Run Cell 4
2. Watch 8 workers upload in parallel!
3. Keep Safari tab open (Colab needs browser connection)

---

## ⚡ **Performance Comparison:**

| Method | Workers | Speed | Time for 107K |
|--------|---------|-------|---------------|
| Original (Replit) | 1 | 2-5/min | 46 days ❌ |
| **Colab Parallel** | **8** | **60-100/min** | **1-2 days** ✅ |

**20x faster!** 🔥

---

## 📊 **Monitoring:**

The notebook shows live progress every 30 seconds:
```
📊 Uploaded: 5,234 | Failed: 12 | Remaining: 102,251
⚡ Speed: 87.2/min | Last 30s: 43 | ETA: 1.2 days
```

---

## 💡 **Tips:**

### **Keep Colab Running:**
- Don't close Safari tab
- Colab sessions timeout after 90 min idle
- Click anywhere in notebook every hour to keep alive
- Or use Colab Pro ($9.99/mo) for background execution

### **If Session Disconnects:**
- Just run Cell 4 again
- Script automatically skips already-uploaded images
- No data loss!

### **Speed Up Even More:**
- Colab Pro: 12 workers (120+ images/min!)
- Complete in ~12-18 hours instead of 1-2 days

---

## 🔧 **Troubleshooting:**

### **"Runtime disconnected"**
- Click **Reconnect**
- Re-run Cells 1, 2, 3, 4

### **"Token expired"**
- Download fresh `token.json` from Replit
- Upload to Colab again

### **Upload seems slow**
- Check that all 8 workers started
- Free tier might limit to 4-6 workers during peak hours

---

## 📞 **Questions?**

Monitor in real-time or check database:
```sql
SELECT COUNT(*) FROM orchid_images 
WHERE google_drive_url IS NOT NULL;
```

---

**Ready to go 20x faster? Upload the notebook to Colab and let's max out that upload speed!** 🚀
