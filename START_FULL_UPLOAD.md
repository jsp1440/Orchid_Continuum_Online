# 🚀 Starting the Full 107K Image Upload

**Last Updated**: November 5, 2025  
**Ready to Upload**: 107,301 images  
**Estimated Time**: ~135 hours (5.6 days)  
**Upload Speed**: ~13 images/minute

---

## ✅ PRE-FLIGHT CHECKLIST

All systems are GO:
- ✅ OAuth authentication working (fcospresident@gmail.com)
- ✅ Database schema fixed (updated_at column added)
- ✅ JSON serialization fixed (Decimal → string conversion)
- ✅ **CRITICAL PAGINATION BUG FIXED** (100% dataset coverage guaranteed)
- ✅ Test uploads successful (184 images uploaded total)
- ✅ Google Drive folder ready (2TB storage available)
- ✅ Google Sheets catalog configured

---

## 🎯 STARTING THE UPLOAD

### **Option 1: Full Upload (Recommended)**
```bash
nohup python3 oauth_drive_uploader.py > full_upload.log 2>&1 &
echo $! > upload_pid.txt
```

### **Option 2: Limited Test (e.g., 1000 images)**
```bash
nohup python3 oauth_drive_uploader.py 1000 > upload_1000.log 2>&1 &
echo $! > upload_pid.txt
```

### **Option 3: Resume Upload (if interrupted)**
The script automatically skips already-uploaded images (checks for google_drive_url), so just run Option 1 again.

---

## 📊 MONITORING PROGRESS

### **Check Live Progress**
```bash
# Watch the log file
tail -f full_upload.log

# Check last 50 lines
tail -50 full_upload.log

# Search for progress updates
grep "Progress:" full_upload.log
```

### **Check Database Status**
```sql
SELECT 
    COUNT(*) as total_images,
    COUNT(google_drive_url) FILTER (WHERE google_drive_url IS NOT NULL) as uploaded,
    COUNT(*) FILTER (WHERE google_drive_url IS NULL) as remaining,
    ROUND(COUNT(google_drive_url) * 100.0 / COUNT(*), 2) as percent_complete
FROM orchid_images;
```

### **Check if Process is Running**
```bash
# Check process
ps aux | grep oauth_drive_uploader

# Get PID
cat upload_pid.txt

# Kill process if needed
kill $(cat upload_pid.txt)
```

---

## 📈 EXPECTED TIMELINE

| Time | Images Uploaded | % Complete | Remaining |
|------|----------------|------------|-----------|
| 1 hour | ~780 | 0.7% | 106,521 |
| 6 hours | ~4,680 | 4.4% | 102,621 |
| 24 hours | ~18,720 | 17.4% | 88,581 |
| 3 days | ~56,160 | 52.3% | 51,141 |
| 5.6 days | ~107,301 | 100% | 0 |

---

## 🎯 SUCCESS CRITERIA

### **After Upload Completes**

#### **1. Verify Upload Count**
```sql
SELECT COUNT(*) FROM orchid_images WHERE google_drive_url IS NOT NULL;
-- Expected: 107,301 (or close to total count)
```

#### **2. Verify Google Drive**
- Go to: https://drive.google.com/drive/folders/1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS
- Check file count matches uploaded count

#### **3. Verify Google Sheets**
- Open: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz
- Check row count matches uploaded count

#### **4. Check for Failures**
```bash
grep "failed" full_upload.log
grep "ERROR" full_upload.log
```

---

## 🔧 TROUBLESHOOTING

### **Upload Stopped/Crashed**
```bash
# Check what happened
tail -100 full_upload.log

# Restart (will skip already-uploaded images)
nohup python3 oauth_drive_uploader.py > full_upload_resume.log 2>&1 &
```

### **Rate Limiting**
The script has built-in retry logic with exponential backoff. If you see many 429 errors, the script will automatically slow down.

### **Out of Storage**
You have 2TB available. At ~3MB per image average:
- 107K images × 3MB = ~321 GB
- Still have 1.7TB remaining ✅

### **Token Expired**
```bash
# Delete token and restart (will prompt for re-authorization)
rm token.json
python3 oauth_drive_uploader.py
```

---

## 📞 JULIUS AI MONITORING

Julius can help monitor progress by:

### **1. Query Upload Progress**
```sql
SELECT 
    COUNT(*) FILTER (WHERE google_drive_url IS NOT NULL) as uploaded,
    COUNT(*) FILTER (WHERE google_drive_url IS NULL) as remaining,
    ROUND(COUNT(*) FILTER (WHERE google_drive_url IS NOT NULL) * 100.0 / COUNT(*), 2) as percent
FROM orchid_images;
```

### **2. Calculate ETA**
```python
# Based on 13 images/minute
remaining = 107301  # Update with current remaining
minutes_remaining = remaining / 13
hours_remaining = minutes_remaining / 60
days_remaining = hours_remaining / 24
print(f"ETA: {days_remaining:.1f} days")
```

### **3. Check for Issues**
```sql
-- Find images that failed to upload (if any retry logic added)
SELECT COUNT(*) 
FROM orchid_images 
WHERE image_url IS NOT NULL 
AND (google_drive_url IS NULL OR google_drive_url = '')
AND created_at < NOW() - INTERVAL '1 hour';
```

---

## ⚡ PERFORMANCE OPTIMIZATION (Future)

If you want to speed up the upload:

### **1. Parallel Workers**
Run multiple uploader instances with different ID ranges:
```bash
# Worker 1: IDs 1-35,000
python3 oauth_drive_uploader_parallel.py 1 35000 &

# Worker 2: IDs 35,001-70,000
python3 oauth_drive_uploader_parallel.py 35001 70000 &

# Worker 3: IDs 70,001-107,301
python3 oauth_drive_uploader_parallel.py 70001 107301 &
```

### **2. Increase Batch Size**
Edit `oauth_drive_uploader.py`:
```python
BATCH_SIZE = 200  # Change from 100 to 200
```

### **3. Reduce Logging**
Less console output = faster processing

---

## 🎉 WHEN UPLOAD COMPLETES

You'll see:
```
================================================================================
🎉 UPLOAD COMPLETE!
⏱️  Time: 135.2 hours
✅ Uploaded: 107,301
📋 Sheet rows: 107,301
❌ Failed: 0
🚀 Rate: 13.2 images/min
================================================================================
```

### **Next Steps After Upload**
1. ✅ Verify counts match (database, Drive, Sheets)
2. 📊 Run coverage analysis (species with <30 images)
3. 🎯 Plan next collection round for missing species
4. 🚀 Start BloomBuilder development with complete dataset

---

**Current Status**: Ready to start full 107K upload  
**Recommendation**: Start upload now and let it run for ~5.6 days  
**Monitoring**: Check logs daily, verify progress with database queries  

---

*Instructions created by Replit Agent on November 5, 2025*
