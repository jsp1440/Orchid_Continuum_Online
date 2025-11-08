# 🤖 Julius AI - Orchid Harvester Instructions

## Your Mission
Help harvest orchid images from GBIF using the queue-based system.

## What You Need

### 1. Database Connection
```python
DATABASE_URL = "postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-forest-a5d1v3hd.us-east-2.aws.neon.tech/neondb?sslmode=require"
```

### 2. Python Script
Use the `queue_worker.py` file from this Replit project.

### 3. Worker ID
When you run the script, use: `julius-worker-1`

## How to Run

### Option 1: Single Worker (Simple)
```bash
python3 queue_worker.py julius-worker-1
```

### Option 2: Multiple Workers (Faster)
Run these in separate sessions/terminals:
```bash
python3 queue_worker.py julius-worker-1 &
python3 queue_worker.py julius-worker-2 &
python3 queue_worker.py julius-worker-3 &
python3 queue_worker.py julius-worker-4 &
```

## How the System Works

✅ **Queue-based**: The database assigns you unique species to work on
✅ **No conflicts**: Each worker gets different species (using SELECT FOR UPDATE SKIP LOCKED)
✅ **Auto-recovery**: If your worker crashes, jobs are automatically reclaimed after 10 minutes
✅ **Regional priority**: System prioritizes Australia, PNG, SE Asia, Central America

## What It Does

1. **Leases 5 species** from the queue
2. **Searches GBIF** for images (global + priority regions)
3. **Saves images** to PostgreSQL with full metadata
4. **Marks jobs complete**
5. **Repeats** continuously

## Expected Performance

- **Per worker**: 10-30 images/min
- **4 workers**: 40-120 images/min
- **All workers combined (Replit + Mac + Julius)**: 350+ images/min target

## Current Queue Status

- **34,221 species** need images (less than 30 each)
- **Priority tiers**: High priority = species with 0-4 images
- **Target**: 30+ images per species

## Monitoring

Check your progress:
```bash
python3 monitor_queue.py
```

Or query the database:
```sql
SELECT 
    lease_owner, 
    COUNT(*) as jobs_working_on
FROM harvest_jobs 
WHERE status = 'leased' 
GROUP BY lease_owner;
```

## Troubleshooting

**If worker stops:**
- It will auto-restart if you use `&` to run in background
- Jobs will be auto-reclaimed after 10 min

**If you see errors:**
- Check DATABASE_URL is correct
- Ensure `psycopg2-binary` and `requests` are installed
- Check network connection

## Communication

Since you're Julius AI and have autonomous access:
- You can check job status anytime via database queries
- You can adjust PRIORITY_COUNTRIES if you want to target specific regions
- You can run as many workers as your compute allows

## Goal

**Help reach 1,000,000 images in 2 weeks!**
Currently at: ~110,000 images
