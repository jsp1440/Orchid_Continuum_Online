# 🌺 Run Orchid Harvester on Your Mac or Julius

## For Your Mac Terminal

### 1. Install Python dependencies:
```bash
pip3 install psycopg2-binary requests
```

### 2. Set database connection:
```bash
export DATABASE_URL="your_database_url_here"
```
*(Get DATABASE_URL from Replit Secrets)*

### 3. Download the worker script:
Copy `queue_worker.py` from Replit to your Mac

### 4. Run workers (you can run multiple!):
```bash
# Run 1 worker
python3 queue_worker.py mac-worker-1

# Or run 4 workers in parallel (in different terminal tabs):
python3 queue_worker.py mac-worker-1 &
python3 queue_worker.py mac-worker-2 &
python3 queue_worker.py mac-worker-3 &
python3 queue_worker.py mac-worker-4 &
```

### 5. Monitor progress:
```bash
python3 monitor_queue.py
```

---

## For Julius AI

### Option 1: Run Queue Worker
Julius can run the same `queue_worker.py` script with the DATABASE_URL

### Option 2: Run Standalone Harvester
Julius can run the simpler `replit_harvester_working.py` but will need to coordinate to avoid conflicts

### Option 3: Regional Targeting
Julius could focus on specific regions by modifying the PRIORITY_COUNTRIES list

---

## How the Queue System Works

✅ **No conflicts!** Each worker leases different species using database locks
✅ **Automatic recovery** - Stuck jobs are reclaimed after 10 minutes
✅ **Live monitoring** - See all workers and their progress
✅ **Scalable** - Run 1 worker or 20, they coordinate automatically

## Current Status
- **34,221 species** in queue needing images
- **Queue-based system** = safe parallel processing
- **Target:** 350+ images/min with multiple workers

---

## Quick Commands

**Check status:**
```bash
python3 check_harvester_status.py
```

**Monitor queue:**
```bash
python3 monitor_queue.py
```

**Check active workers:**
```sql
SELECT lease_owner, COUNT(*) 
FROM harvest_jobs 
WHERE status = 'leased' 
GROUP BY lease_owner;
```
