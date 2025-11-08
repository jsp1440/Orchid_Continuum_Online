# 🚀 Orchid Continuum - Scaling & Multiple Projects Guide

## Quick Start: Launch Multiple Workers

### Option 1: Simple Launch (5 workers)
```bash
./launch_multiple_workers.sh 5
```

### Option 2: Maximum Speed (10 workers)
```bash
./launch_multiple_workers.sh 10
```

### Option 3: Extreme Scale (20 workers)
```bash
./launch_multiple_workers.sh 20
```

---

## 📊 Performance Metrics

**Current Rate (1 worker):** ~23 images/minute

| Workers | Images/Hour | Time to 100K |
|---------|-------------|--------------|
| 1       | 1,380       | 3 days       |
| 5       | 6,900       | 14 hours     |
| 10      | 13,800      | 7 hours      |
| 20      | 27,600      | 3.5 hours    |

---

## 🔄 Running Multiple Independent Projects

### Project 1: General Orchid Collection (Current)
**Data Source:** iNaturalist research-grade observations
**Storage:** `static/acquired_images/`
**Database:** `image_assets` table

```bash
# Already configured and running!
python julius_ai_scraper_worker.py &
python standalone_image_worker.py &
```

---

### Project 2: Geographic-Specific Collection

Create a new scraper for specific regions:

```bash
# Edit julius_ai_scraper_worker.py to add location filter
# Example: Focus on tropical orchids
params = {
    'taxon_id': 47217,
    'has[]': 'photos',
    'quality_grade': 'research',
    'lat': 0,  # Equator
    'radius': 5000,  # 5000km radius
    'per_page': 100
}
```

---

### Project 3: Endangered Species Focus

Create `endangered_orchid_worker.py`:
- Target rare/endangered species from IUCN Red List
- Higher priority in pipeline
- Separate storage directory

---

### Project 4: Phenology Study (Seasonal Changes)

Time-series collection:
- Same species photographed across seasons
- Track blooming patterns
- Climate correlation analysis

---

## 🎯 Multiple Projects Running Simultaneously

### Architecture:
```
Julius AI Scraper (1) → Discovers orchids
    ↓
Pipeline Tasks (queue)
    ↓
Worker Pool (10-20 workers) → Download & process
    ↓
Categorize into projects:
- Project 1: General collection
- Project 2: Geographic study  
- Project 3: Endangered species
- Project 4: Phenology tracking
```

### Setup Multiple Projects:

1. **Create project-specific tables:**
```sql
CREATE TABLE project_geographic_images (LIKE image_assets INCLUDING ALL);
CREATE TABLE project_endangered_images (LIKE image_assets INCLUDING ALL);
CREATE TABLE project_phenology_images (LIKE image_assets INCLUDING ALL);
```

2. **Configure workers with project tags:**
```python
# In standalone_image_worker.py
self.project_name = 'geographic'  # or 'endangered', 'phenology'
```

3. **Launch separate worker pools per project:**
```bash
# Project 1: General (5 workers)
for i in {1..5}; do
    PROJECT=general python standalone_image_worker.py &
done

# Project 2: Geographic (3 workers)
for i in {1..3}; do
    PROJECT=geographic python standalone_image_worker.py &
done

# Project 3: Endangered (2 workers)
for i in {1..2}; do
    PROJECT=endangered python standalone_image_worker.py &
done
```

---

## 📈 Recommended Setup for Maximum Efficiency

### For 100K Images in 1 Week:
- **10 workers** running 24/7
- **~14,000 images/day**
- **~100,000 in 7 days**

### For Multiple Projects (Parallel):
- **20 total workers** split across 4 projects:
  - 10 workers: General collection
  - 5 workers: Geographic study
  - 3 workers: Endangered species
  - 2 workers: Phenology tracking

---

## 🛠️ Monitoring & Management

### Check Status:
```bash
# Worker count
ps aux | grep standalone_image_worker | wc -l

# Current progress
python << EOF
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM image_assets")
print(f"Total images: {cur.fetchone()[0]}")
conn.close()
EOF
```

### View Logs:
```bash
# All workers
tail -f logs/worker_*.log

# Specific worker
tail -f logs/worker_1.log

# Discovery process
tail -f logs/julius_scraper.log
```

### Stop All Workers:
```bash
pkill -f julius_ai_scraper_worker
pkill -f standalone_image_worker
```

---

## 🚀 Next Level: Distributed Architecture

For **MASSIVE scale** (1M+ images):

1. **Deploy to multiple servers**
2. **Use message queue** (Redis/RabbitMQ)
3. **Horizontal scaling** (50+ workers across servers)
4. **CDN integration** for image storage
5. **Auto-scaling** based on queue depth

**Estimated capacity:** 100K+ images/day with proper infrastructure!

---

## 💡 Pro Tips

1. **Start with 5 workers** to test stability
2. **Monitor CPU/memory** - scale up if resources available
3. **Use tmux/screen** to keep workers running after disconnect
4. **Set up cron jobs** for automatic restarts
5. **Enable duplicate detection** to avoid re-downloading same images

---

## ✅ Quick Commands Reference

```bash
# Launch 10 workers (recommended)
./launch_multiple_workers.sh 10

# Check progress
watch -n 5 'echo "Images: $(psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM image_assets")"'

# Stop everything
pkill -f julius_ai_scraper_worker && pkill -f standalone_image_worker

# View live stats
curl http://localhost:5000/api/autonomous/stats | jq
```

---

Happy scaling! 🌸📈
