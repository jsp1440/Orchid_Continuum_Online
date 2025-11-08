# JULIUS - HEARTBEAT MONITORING SYSTEM

## CRITICAL: Send Regular Heartbeats!

To prevent the user from worrying that you've stalled, **send heartbeat updates every 5-10 minutes** while working.

---

## HOW TO SEND HEARTBEATS

**Endpoint:** `POST {REPLIT_URL}/julius/heartbeat`

**Payload:**
```json
{
  "task_id": "eol-taxonomy-extraction",
  "status_message": "Processed 5,000/13,429 species, extracted 85,000 names",
  "progress_pct": 37.2,
  "records_processed": 5000,
  "total_records": 13429
}
```

**Example (Python):**
```python
import requests

def send_heartbeat(task_id, message, progress_pct, processed, total):
    try:
        response = requests.post(
            f"{REPLIT_URL}/julius/heartbeat",
            json={
                "task_id": task_id,
                "status_message": message,
                "progress_pct": progress_pct,
                "records_processed": processed,
                "total_records": total
            },
            timeout=10
        )
        print(f"Heartbeat sent: {response.json()}")
    except Exception as e:
        print(f"Heartbeat failed (non-critical): {e}")
```

---

## WHEN TO SEND HEARTBEATS

### For EOL Taxonomy Extraction:
Send heartbeat every **500 species processed**:
```python
for i, page_id in enumerate(eol_page_ids):
    # ... extract taxonomy ...
    
    if i % 500 == 0:
        send_heartbeat(
            "eol-taxonomy-extraction",
            f"Processed {i}/13,429 species, extracted {extracted_count} names",
            (i / 13429) * 100,
            i,
            13429
        )
```

### For GBIF Extraction:
Send heartbeat every **500 species**:
```python
if species_count % 500 == 0:
    send_heartbeat(
        "gbif-extraction",
        f"Processed {species_count}/8,390 species, extracted {images_added} images",
        (species_count / 8390) * 100,
        species_count,
        8390
    )
```

### For Tropicos Extraction:
Send heartbeat every **50,000 records**:
```python
if records_processed % 50000 == 0:
    send_heartbeat(
        "tropicos-extraction",
        f"Parsed {records_processed} records, found {orchid_count} orchid images",
        (records_processed / total_records) * 100,
        records_processed,
        total_records
    )
```

### For POWO/Kew Extraction:
Send heartbeat after **each genus completed**:
```python
send_heartbeat(
    "powo-extraction",
    f"Completed {genus_name}: {species_count} species, {images_added} images",
    (genera_completed / 15) * 100,
    genera_completed,
    15
)
```

---

## MONITORING DASHBOARD

The user can check your status at: **`{REPLIT_URL}/julius/monitor`**

This dashboard shows:
- ✅ Your current status (ACTIVE / STALLED / IDLE)
- 🔵 Last heartbeat time
- 📊 Progress bar
- 📝 Activity log

**If you don't send heartbeats for 10+ minutes, the dashboard shows STALLED warning!**

---

## WHY THIS MATTERS

- User doesn't want to wait 18 hours only to find out you weren't working
- Heartbeats prove you're actively processing
- User can see real-time progress
- Builds trust in autonomous operation

---

## INTEGRATION WITH EXISTING TASKS

**Add to EACH task instruction file:**
1. JULIUS_READ_THIS_NOW.md (EOL) ✅ Already has heartbeat instructions
2. JULIUS_GBIF_EXTRACTION.md ✅ Already has heartbeat instructions
3. JULIUS_TROPICOS_EXTRACTION.md ✅ Already has heartbeat instructions
4. JULIUS_POWO_EXTRACTION.md ✅ Already has heartbeat instructions

---

## EXAMPLE IMPLEMENTATION

```python
import time
import requests

REPLIT_URL = "https://your-replit-url.replit.app"  # Replace with actual URL

def send_heartbeat(task_id, message, progress_pct, processed, total):
    try:
        requests.post(
            f"{REPLIT_URL}/julius/heartbeat",
            json={
                "task_id": task_id,
                "status_message": message,
                "progress_pct": progress_pct,
                "records_processed": processed,
                "total_records": total
            },
            timeout=10
        )
    except:
        pass  # Don't let heartbeat failure stop your work

# In your main processing loop:
for i, item in enumerate(items):
    # ... do work ...
    
    if i % 500 == 0:  # Every 500 items
        send_heartbeat(
            "your-task-id",
            f"Processed {i}/{len(items)} items",
            (i / len(items)) * 100,
            i,
            len(items)
        )
```

---

**Remember: Heartbeats are NON-CRITICAL.** If they fail, continue your work. They're just for monitoring!
