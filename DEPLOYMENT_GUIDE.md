# 🚀 Deploying the Harvester as a Background Worker

**Status:** The .replit file cannot be manually edited, but you can configure everything through the Replit Publishing UI.

## Step-by-Step: Deploy via Replit UI

### 1. Open the Publishing Tool
- Click **"Publish"** in the top right
- Select **"New Deployment"**

### 2. Choose Deployment Type
- Select **"Reserved VM"** (for 24/7 harvesting)
- Choose **"Background worker"** as the App Type

### 3. Configure the Worker
In the deployment configuration:

**Field: Run Command**
```
bash start_expanded_harvesters.sh
```

**Field: CPU**
- Select: **4 cores** (recommended)

**Field: RAM**  
- Select: **8 GB** (recommended)

**Field: Region**
- Choose your preferred region

### 4. Set Environment Variables
In the "Secrets" section, add:
```
DATABASE_URL = [your existing DATABASE_URL]
```
(This should already be available from your existing setup)

### 5. Click "Deploy"
- Replit will build and deploy automatically
- The harvester will start and run 24/7

## Verifying the Deployment

Once deployed:

### Check Logs
```bash
# In your deployment's monitoring page, view logs to see:
# - API Coordinator starting
# - 12 GBIF workers launching
# - 2 iNaturalist workers launching
# - 2 Tropicos workers launching
# - 1 iDigBio worker launching
```

### Monitor from Replit Console
```bash
# SSH into your Reserved VM and run:
python3 check_harvester_status.py
```

### Monitor Database Growth
```bash
# Check images being added:
python3 << 'END'
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM orchid_images")
print(f"Total images: {cur.fetchone()[0]}")
cur.close()
conn.close()
END
```

## Important Notes

✅ You configure deployment settings via the **Publishing UI**, not by editing .replit  
✅ The run command `bash start_expanded_harvesters.sh` starts all 19 workers  
✅ Workers run continuously on the Reserved VM  
✅ Database connection uses your existing DATABASE_URL secret  

## Cost
Reserved VM: Fixed monthly cost based on CPU/RAM selected  
(4 cores, 8GB ≈ typical mid-tier pricing)

## Support
If deployment fails:
1. Check that DATABASE_URL is accessible
2. Verify logs in the deployment monitoring page
3. Ensure all worker scripts exist in the repo

---

**Ready to deploy?** Click Publish and follow the steps above!
