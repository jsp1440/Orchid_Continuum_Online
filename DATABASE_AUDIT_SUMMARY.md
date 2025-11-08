# Database Audit - Quick Reference
**Audit Date:** October 19, 2025

---

## Summary

**Total Databases:** 16 SQLite files  
**Duplicates:** 6 files (2 duplicate sets)  
**Empty Files:** 3 files  
**Active Databases:** 3 (production + 2 monitoring)  
**System Libraries:** 4 (geospatial - do not modify)

---

## Keep These (6 files)

### 1. Production Database
- **File:** `instance/orchid_continuum.db` (1.4 MB)
- **Purpose:** Development database when DATABASE_URL not set
- **Status:** ✅ Keep - used in local development

### 2. AI Widget Manager
- **File:** `ai_widget_manager.db` (1.2 MB, 4,253 rows)
- **Purpose:** Widget monitoring and AI recommendations
- **Status:** ✅ Keep - active monitoring data

### 3. System Monitoring
- **File:** `monitoring_data.db` (3.7 MB, 25,921 rows)
- **Purpose:** System events, performance metrics, health checks
- **Status:** ✅ Keep - active monitoring

### 4-7. System Libraries (4 files)
- **Files:** `.cache/*/proj.db` and `.pythonlibs/*/proj.db`
- **Purpose:** Geospatial coordinate system databases (pyproj/pyogrio libraries)
- **Status:** ✅ Keep - required by Python libraries

---

## Delete These (8 files)

### Duplicates (5 files)
```bash
# Delete these - exact duplicates:
rm attached_assets/DOWNLOAD_THIS_DATABASE_1758603539993.db
rm your_orchid_database.db
# Keep: DOWNLOAD_THIS_DATABASE.db (if needed for exports)

# Delete empty files:
rm orchid_database_export.db
rm orchids.db
rm orchid-continuum-scaffold/partner-connect/services/api/partner_connect.db
```

### Old/Unused (3 files)
```bash
rm orchid_continuum.db  # Old template in root (instance/ is active)
rm orchid.db  # Test database with sample data
rm research_data.db  # Only 3 rows, feature likely unused
```

**Space Saved:** ~72 KB (minimal, but reduces clutter)

---

## Production Configuration

**Key Finding:** Platform uses **PostgreSQL in production** (via DATABASE_URL environment variable)

**Evidence:**
- `app.py:61-71` - Requires DATABASE_URL or throws error
- `render.yaml:17` - PostgreSQL database service configured
- SQLite only used for local development and monitoring

**No migration needed** - System already production-ready.

---

## Monitoring Database Strategy

**Recommendation:** Keep monitoring databases separate (SQLite is better for high-write monitoring data)

**Action:** Implement 30-day data retention:
```bash
# Archive monthly
sqlite3 monitoring_data.db "DELETE FROM system_events WHERE timestamp < date('now', '-30 days');"
sqlite3 monitoring_data.db "VACUUM;"
```

---

## Full Details

See complete audit: `docs/db_audit.md` (615 lines)  
Machine-readable data: `docs/db_audit.json` (6,955 lines)

---

**Clean-up script:**
```bash
# Run this to clean up duplicates/old databases:
rm -f attached_assets/DOWNLOAD_THIS_DATABASE_1758603539993.db
rm -f your_orchid_database.db
rm -f orchid_database_export.db
rm -f orchids.db
rm -f orchid-continuum-scaffold/partner-connect/services/api/partner_connect.db
rm -f orchid_continuum.db
rm -f orchid.db
rm -f research_data.db

echo "✅ Cleaned up 8 duplicate/unused databases"
```
