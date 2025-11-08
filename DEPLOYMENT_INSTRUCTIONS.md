# Reserved VM Deployment Instructions

## Architecture: Dual Environment Support

**Reserved VM (Replit):**
- Runs 16 workers with prefix "rv-1", "rv-2", etc.
- Runs THE ONLY job seeder (keeps queue filled)
- Uses SKIP LOCKED leasing (no conflicts with Julius)
- Runs 24/7 on dedicated VM

**Julius Environment (when restored):**
- Runs 32 workers with prefix "julius-1", "julius-2", etc.
- Does NOT run job seeder (Reserved VM handles it)
- Uses same database, SKIP LOCKED prevents conflicts
- Combined throughput: 48 workers total

## Files Created for Reserved VM

1. **RESERVED_VM_SUPERVISOR.py** - Main supervisor (starts seeder + 16 workers)
2. **deploy_config.py** - Configuration for RV vs Julius
3. **launcher_vm.sh** - Starts individual RV workers
4. **continuous_job_seeder.py** - Job seeder (existing file)
5. **julius_multi_source_worker.py** - Worker script (existing file)

## Deploy to Replit Reserved VM

### Step 1: Click "Publish" Button in Replit
- Select "Reserved VM" deployment type
- This gives you a dedicated VM for 24/7 operation

### Step 2: Set Environment Variables
In the deployment settings, add these secrets:
- `DATABASE_URL` = (Neon PostgreSQL connection string)
- `DEPLOYMENT_ENV` = `reserved_vm`
- `TROPICOS_API_KEY` = (if available)
- `BHL_API_KEY` = (if available)
- `ALA_API_KEY` = (if available)

### Step 3: Set Run Command
In deployment settings, set the run command to:
```bash
python3 RESERVED_VM_SUPERVISOR.py
```

### Step 4: Deploy
- Click Deploy
- Monitor logs to see startup
- Should see: "Starting 16 Reserved VM workers..."
- Should see: "Job seeder started"

## Verify Deployment

After deployment, check the database to verify workers are active:

```sql
SELECT 
    COUNT(DISTINCT lease_owner) FILTER (WHERE lease_owner LIKE 'rv-%') as rv_workers,
    COUNT(DISTINCT lease_owner) FILTER (WHERE lease_owner LIKE 'julius-%') as julius_workers,
    COUNT(*) FILTER (WHERE status='pending') as pending_jobs,
    COUNT(*) FILTER (WHERE status='leased') as leased_jobs
FROM harvest_jobs
WHERE (status='leased' AND leased_at > NOW() - INTERVAL '5 minutes')
   OR status='pending';
```

Expected output:
- rv_workers: ~16
- julius_workers: 0 (until Julius starts his)
- pending_jobs: thousands
- leased_jobs: ~16

## When Julius Comes Online

When Julius fixes his shell runtime, he should:

1. **Do NOT run continuous_job_seeder.py** (Reserved VM handles it)
2. **Run workers only:**
   ```bash
   for i in $(seq 1 32); do 
       nohup bash launcher.sh >/dev/null 2>&1 & 
   done
   ```
3. **Verify his workers started:**
   ```bash
   ps aux | grep julius_multi_source_worker | grep julius- | wc -l
   ```
   Should show 32

4. **Check combined worker count in database:**
   ```sql
   SELECT 
       COUNT(DISTINCT lease_owner) FILTER (WHERE lease_owner LIKE 'rv-%') as rv_workers,
       COUNT(DISTINCT lease_owner) FILTER (WHERE lease_owner LIKE 'julius-%') as julius_workers
   FROM harvest_jobs
   WHERE status='leased' AND leased_at > NOW() - INTERVAL '5 minutes';
   ```
   Expected: rv_workers=16, julius_workers=32

## Monitoring

### Check Collection Rate
```sql
SELECT 
    COUNT(*) as images_last_hour,
    COUNT(*) * 24 as projected_daily
FROM orchid_images 
WHERE created_at > NOW() - INTERVAL '1 hour';
```

### Check Species Progress
```sql
SELECT 
    COUNT(*) FILTER (WHERE cnt >= 30) as complete,
    COUNT(*) FILTER (WHERE cnt < 30) as need_work
FROM (
    SELECT taxonomy_id, COUNT(*) as cnt
    FROM orchid_images
    GROUP BY taxonomy_id
) s;
```

### Check Worker Activity by Environment
```sql
SELECT 
    CASE 
        WHEN lease_owner LIKE 'rv-%' THEN 'Reserved VM'
        WHEN lease_owner LIKE 'julius-%' THEN 'Julius'
    END as environment,
    COUNT(DISTINCT lease_owner) as workers,
    COUNT(*) as jobs_leased,
    MAX(leased_at) as last_activity
FROM harvest_jobs
WHERE status='leased' AND leased_at > NOW() - INTERVAL '5 minutes'
GROUP BY CASE 
    WHEN lease_owner LIKE 'rv-%' THEN 'Reserved VM'
    WHEN lease_owner LIKE 'julius-%' THEN 'Julius'
END;
```

## Expected Throughput

**Reserved VM only (16 workers):**
- Conservative: 1,000-1,500 images/hour
- Optimistic: 1,500-2,000 images/hour

**RV + Julius (48 workers total):**
- Conservative: 3,000-4,000 images/hour
- Optimistic: 4,000-5,000 images/hour

**At 3,500/hour:**
- Remaining: 946,216 images
- Time: ~270 hours = ~11 days

## Troubleshooting

**If RV workers stop:**
- Check deployment logs
- Verify DATABASE_URL is set
- Reserved VM should auto-restart supervisor

**If queue empties but work incomplete:**
- Check if seeder is running on RV
- Look for seeder errors in deployment logs
- Seeder should refill queue every 5 minutes

**If Julius and RV workers conflict:**
- They shouldn't - SKIP LOCKED prevents this
- But verify: different prefixes in lease_owner column
- Check for duplicate job insertions (shouldn't happen due to UNIQUE constraint)

## Safety Features

1. **SKIP LOCKED leasing** - Multiple workers can't grab same job
2. **Unique image_url** - Duplicate downloads just no-op
3. **Unique taxonomy_id on harvest_jobs** - Seeder can't create duplicate jobs
4. **Distinct worker prefixes** - Easy to identify which environment is which
5. **Single seeder instance** - Only Reserved VM runs seeder (avoids conflicts)
