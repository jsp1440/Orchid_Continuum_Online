# Source-Specific Workers for Orchid Continuum

## Overview

This directory contains **dedicated worker scripts** for each image source API. By running source-specific workers instead of multi-source workers, we:

✅ **Prevent rate limiting** - Each API gets its own workers with proper delays  
✅ **Maximize throughput** - All 7 sources work in parallel  
✅ **Easy debugging** - Each source has separate logs  
✅ **Flexible scaling** - Add/remove workers per source as needed  

---

## Worker Distribution (17 Total Workers)

| Source | Workers | Script | Rate Limit |
|--------|---------|--------|------------|
| **GBIF** | 8 | `gbif_worker.py` | 0.5s delay |
| **iNaturalist** | 3 | `inaturalist_worker.py` | 0.3s delay |
| **iDigBio** | 2 | `idigbio_worker.py` | 0.4s delay |
| **Tropicos** | 2 | `tropicos_worker.py` | 0.6s delay (needs API key) |
| **BHL** | 1 | `bhl_worker.py` | 0.8s delay (needs API key) |
| **EOL+ALA** | 1 | `eol_ala_worker.py` | 0.5s delay |

---

## Quick Start

### 1. Create Logs Directory
```bash
mkdir -p logs
```

### 2. Set Environment Variables
```bash
export DATABASE_URL="postgresql://..."
export TROPICOS_API_KEY="your-key-here"  # Optional
export BHL_API_KEY="your-key-here"       # Optional
```

### 3. Launch All Workers
```bash
chmod +x workers/launch_all.sh
./workers/launch_all.sh
```

This starts all 17 workers in the background!

---

## Manual Start (Individual Workers)

### Start GBIF Workers (8 workers)
```bash
python3 workers/gbif_worker.py gbif-1 &
python3 workers/gbif_worker.py gbif-2 &
python3 workers/gbif_worker.py gbif-3 &
python3 workers/gbif_worker.py gbif-4 &
python3 workers/gbif_worker.py gbif-5 &
python3 workers/gbif_worker.py gbif-6 &
python3 workers/gbif_worker.py gbif-7 &
python3 workers/gbif_worker.py gbif-8 &
```

### Start iNaturalist Workers (3 workers)
```bash
python3 workers/inaturalist_worker.py inat-1 &
python3 workers/inaturalist_worker.py inat-2 &
python3 workers/inaturalist_worker.py inat-3 &
```

### Start iDigBio Workers (2 workers)
```bash
python3 workers/idigbio_worker.py idigbio-1 &
python3 workers/idigbio_worker.py idigbio-2 &
```

### Start Tropicos Workers (2 workers - requires API key)
```bash
python3 workers/tropicos_worker.py tropicos-1 &
python3 workers/tropicos_worker.py tropicos-2 &
```

### Start BHL Worker (1 worker - requires API key)
```bash
python3 workers/bhl_worker.py bhl-1 &
```

### Start EOL+ALA Worker (1 worker)
```bash
python3 workers/eol_ala_worker.py eol-ala-1 &
```

---

## Monitoring

### Check Running Workers
```bash
ps aux | grep '_worker.py' | grep -v grep
```

### Monitor Logs
```bash
# GBIF worker logs
tail -f logs/gbif-1.log

# iNaturalist worker logs
tail -f logs/inat-1.log

# All logs at once
tail -f logs/*.log
```

### Database Activity
```sql
-- Check imports by source (last hour)
SELECT image_source, COUNT(*) as count 
FROM orchid_images 
WHERE created_at > NOW() - INTERVAL '1 hour' 
GROUP BY image_source 
ORDER BY count DESC;

-- Check worker queue status
SELECT status, COUNT(*) 
FROM harvest_jobs 
GROUP BY status;
```

---

## Stopping Workers

### Stop All Workers
```bash
pkill -f 'workers/.*_worker.py'
```

### Stop Specific Source Workers
```bash
# Stop only GBIF workers
pkill -f 'gbif_worker.py'

# Stop only iNaturalist workers
pkill -f 'inaturalist_worker.py'
```

---

## Deployment to Render

### Option 1: Multiple Services (Recommended)
Create separate Render services for each source:

1. **gbif-workers** - Run 8 GBIF workers
2. **inat-workers** - Run 3 iNaturalist workers
3. **idigbio-workers** - Run 2 iDigBio workers
4. **tropicos-workers** - Run 2 Tropicos workers
5. **bhl-worker** - Run 1 BHL worker
6. **eol-ala-worker** - Run 1 EOL+ALA worker

**Render service start commands:**
```bash
# GBIF service
for i in {1..8}; do python3 workers/gbif_worker.py gbif-$i & done; wait

# iNaturalist service
for i in {1..3}; do python3 workers/inaturalist_worker.py inat-$i & done; wait

# iDigBio service
for i in {1..2}; do python3 workers/idigbio_worker.py idigbio-$i & done; wait
```

### Option 2: Single Service (All Workers)
Use the master launcher:

**Render start command:**
```bash
./workers/launch_all.sh && tail -f logs/*.log
```

---

## Troubleshooting

### Workers Not Importing Images

1. **Check if workers are running:**
   ```bash
   ps aux | grep _worker.py
   ```

2. **Check logs for errors:**
   ```bash
   tail -n 50 logs/gbif-1.log
   ```

3. **Check database connection:**
   ```bash
   echo $DATABASE_URL
   ```

4. **Check for rate limiting:**
   Look for "Rate limited!" or 429 errors in logs

### Rate Limiting Issues

If you see rate limiting:

1. **Reduce number of workers** for that source
2. **Increase REQUEST_DELAY** in the worker script
3. **Check API documentation** for rate limits

### API Key Issues

**Tropicos/BHL workers not starting:**
```bash
# Check if keys are set
echo $TROPICOS_API_KEY
echo $BHL_API_KEY

# Set keys
export TROPICOS_API_KEY="your-key"
export BHL_API_KEY="your-key"
```

---

## Performance Expectations

### Target Rates (per worker)
- **GBIF**: ~150-200 images/hour per worker
- **iNaturalist**: ~100-150 images/hour per worker
- **iDigBio**: ~80-120 images/hour per worker
- **Tropicos**: ~50-80 images/hour per worker
- **BHL**: ~30-50 images/hour per worker
- **EOL+ALA**: ~100-150 images/hour per worker

### Total Expected Throughput
With all 17 workers running:
- **~2,000-3,000 images/hour** combined
- **~48,000-72,000 images/day**
- **Goal of 1M images**: ~15-20 days

---

## Worker Architecture

Each worker:
1. **Leases jobs** from `harvest_jobs` table
2. **Fetches images** from its dedicated API
3. **Saves to database** with full metadata
4. **Marks job complete** and moves to next

**Key features:**
- ✅ Automatic retry for failed jobs
- ✅ Job lease reclaim after 7 minutes
- ✅ Duplicate detection via URL constraint
- ✅ Source-specific metadata in JSONB columns
- ✅ Graceful error handling

---

## Files in This Directory

```
workers/
├── README.md                  # This file
├── launch_all.sh              # Master launcher script
├── gbif_worker.py             # GBIF-only worker
├── inaturalist_worker.py      # iNaturalist-only worker
├── idigbio_worker.py          # iDigBio-only worker
├── tropicos_worker.py         # Tropicos-only worker
├── bhl_worker.py              # BHL-only worker
└── eol_ala_worker.py          # EOL+ALA combo worker
```

---

## Support

For issues or questions:
1. Check worker logs in `logs/` directory
2. Review database with SQL queries above
3. Check API status pages for source APIs
4. Verify environment variables are set correctly
