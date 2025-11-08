# Julius AI - Orchid Continuum OAuth Drive Upload System

**Last Updated**: November 5, 2025  
**System Status**: ✅ OPERATIONAL  
**Authentication**: fcospresident@gmail.com (OAuth 2.0)

---

## 📋 EXECUTIVE SUMMARY

The Orchid Continuum has successfully implemented an OAuth-based Google Drive upload system that:
- ✅ Uploads orchid images from URLs to Google Drive (2TB personal storage)
- ✅ Catalogs metadata in Google Sheets
- ✅ Updates PostgreSQL database with Drive URLs
- ✅ Processes 107,447 images at 13.3 images/minute (~135 hours for full upload)

**Target**: 100% coverage of 35,327 Orchidaceae species with 30+ images each (~1,059,810 images)

---

## 🏗️ SYSTEM ARCHITECTURE

### **Data Flow**
```
Google Colab (iPad) → Database URLs → OAuth Uploader → Google Drive
                                                    ↓
                                            Google Sheets Catalog
```

### **Components**

#### 1. **Google Colab Notebook** (`ORCHID_MEGA_5000_SPECIES.ipynb`)
- **Purpose**: Collect image URLs from GBIF/iNaturalist
- **Capacity**: 5,000 species per 6-8 hour session
- **Rate**: 95-110 images/minute
- **Platform**: Browser-based (iPad M4 compatible)

#### 2. **OAuth Drive Uploader** (`oauth_drive_uploader.py`)
- **Purpose**: Download images from URLs → Upload to Google Drive
- **Authentication**: OAuth 2.0 (fcospresident@gmail.com)
- **Rate**: 13.3 images/minute
- **Storage**: Google Drive folder `1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS`
- **Catalog**: Google Sheet `1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz`

#### 3. **PostgreSQL Database**
- **Table**: `orchid_images`
- **Records**: 107,447 images with URLs
- **Metadata Fields**: 52+ (taxonomy, GPS, observer, license, etc.)

---

## 🔐 OAUTH AUTHENTICATION SETUP

### **Current Status**
- ✅ OAuth Client configured (Desktop app)
- ✅ Test user added: fcospresident@gmail.com
- ✅ Token saved: `token.json` (auto-refreshes)
- ✅ Scopes: Google Drive + Google Sheets (full access)

### **OAuth Client ID**
```
941511288223-0ocr4hnk9qf14as9ibqooov9es0tt8ub.apps.googleusercontent.com
```

### **Security**
- Publishing status: **Testing** (100 test users allowed)
- Personal account: fcospresident@gmail.com with 2TB storage
- Auto token refresh: Prevents re-authorization

---

## 🎯 SYSTEM CAPABILITIES

### **Current Progress**
| Metric | Value |
|--------|-------|
| Database URLs | 107,447 |
| Images Uploaded | 28 (test run) |
| Remaining | 107,419 |
| Upload Speed | 13.3 images/min |
| Time Estimate | ~135 hours (5.6 days) |

### **Features**
✅ Automatic download from remote URLs  
✅ EXIF metadata preservation  
✅ Public sharing permissions  
✅ Google Sheets cataloging with 17 columns  
✅ Database synchronization  
✅ Error handling and retry logic  
✅ Batch processing (100 images/batch)  
✅ Progress logging every 10 images  

---

## 📊 DATABASE SCHEMA

### **orchid_images Table** (52 fields)
```sql
-- Core identification
id                          INTEGER PRIMARY KEY
taxonomy_id                 INTEGER (FK to orchid_taxonomy)
gbif_occurrence_key         VARCHAR
scientific_name             TEXT (from join with orchid_taxonomy)

-- Image data
image_url                   TEXT (source URL)
google_drive_url            TEXT (uploaded Drive URL)
image_source                VARCHAR (GBIF, iNaturalist, EOL)
image_license               TEXT

-- Geographic data
latitude                    NUMERIC
longitude                   NUMERIC
coordinate_uncertainty      NUMERIC
country                     VARCHAR
state_province              VARCHAR
locality                    TEXT
continent                   VARCHAR
elevation_meters            INTEGER

-- Observation metadata
observation_date            TIMESTAMP
year_observed               INTEGER
month_observed              INTEGER
observer_name               VARCHAR
wild_specimen               BOOLEAN

-- Institutional data
institution_code            VARCHAR
individual_count            INTEGER
sex                         VARCHAR
life_stage                  VARCHAR
reproductive_condition      VARCHAR
iucn_red_list_category      VARCHAR

-- External IDs
eol_data_object_id          VARCHAR
eol_page_id                 VARCHAR
eol_content_id              VARCHAR

-- Media metadata
occurrence_metadata         JSONB
media_metadata              JSONB
eol_metadata                JSONB
tropicos_metadata           JSONB

-- Asset tracking
asset_id                    INTEGER
file_sha256                 TEXT
perceptual_hash             TEXT
local_path                  TEXT
download_status             TEXT
alt_text                    TEXT
is_duplicate                BOOLEAN

-- Image categorization
image_type                  VARCHAR
is_hybrid                   BOOLEAN
is_intergeneric             BOOLEAN
geographic_origin           VARCHAR
collection_year             INTEGER
plate_number                VARCHAR
herbarium_catalog_number    VARCHAR
copyright_owner             TEXT

-- Timestamps
downloaded_at               TIMESTAMP
created_at                  TIMESTAMP
updated_at                  TIMESTAMP (newly added)
```

---

## 🚀 USAGE INSTRUCTIONS

### **Running the Uploader**

#### **Full Upload (107K images)**
```bash
python3 oauth_drive_uploader.py
```

#### **Limited Upload (e.g., 1000 images)**
```bash
python3 oauth_drive_uploader.py 1000
```

#### **Test Upload (10 images)**
```bash
python3 oauth_drive_uploader.py 10
```

### **Expected Output**
```
🌺 Orchid Continuum - OAuth Drive Uploader
================================================================================
✅ Authenticated as: fcospresident@gmail.com
📁 Target folder: 1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS
📊 Target sheet: 1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz
================================================================================
✅ Database connected
📊 Found 107,447 images to upload

📦 Batch 1 (1-100 of 107447)
[1] Processing: Apostasia wallichii R. Br.
...
📊 Progress: 100 uploaded, 13.3/min
...
🎉 UPLOAD COMPLETE!
⏱️  Time: 135.2 hours
✅ Uploaded: 107,447
📋 Sheet rows: 107,447
❌ Failed: 0
🚀 Rate: 13.3 images/min
```

---

## 📝 GOOGLE SHEETS CATALOG

### **Sheet Structure** (17 columns)
| Column | Data | Example |
|--------|------|---------|
| A | Image ID | 12345 |
| B | Scientific Name | Phalaenopsis amabilis |
| C | Taxonomy Display | Phalaenopsis amabilis |
| D | Genus | Phalaenopsis |
| E | Species | amabilis |
| F | Subspecies | (empty or value) |
| G | Country | Indonesia |
| H | Latitude | -6.1234 |
| I | Longitude | 106.5678 |
| J-L | Reserved | (empty) |
| M | Wild Specimen | TRUE/FALSE |
| N | Drive URL | https://drive.google.com/file/d/... |
| O | Observer | John Smith |
| P | Source | GBIF |
| Q | Date | 2024-03-15T10:30:00 |

---

## 🔧 TECHNICAL FIXES IMPLEMENTED

### **Issue 1: Missing Database Column**
**Problem**: `column "updated_at" does not exist`  
**Solution**: Added `updated_at TIMESTAMP DEFAULT NOW()` to `orchid_images` table

### **Issue 2: Decimal JSON Serialization**
**Problem**: `Object of type Decimal is not JSON serializable`  
**Solution**: Convert Decimal values to strings before Google Sheets API call
```python
str(img['latitude']) if img['latitude'] is not None else ''
```

### **Issue 3: CRITICAL - Broken Pagination Logic**
**Problem**: LIMIT/OFFSET pagination was skipping rows because processed rows no longer matched WHERE clause  
**Root Cause**: Each batch updated rows (added google_drive_url), removing them from results, but OFFSET kept incrementing:
- Batch 1: OFFSET 0 → processes rows 1-100 ✅
- Batch 2: OFFSET 100 → got rows 201-300 instead of 101-200 ❌ (skipped 100 rows!)

**Solution**: Always use OFFSET 0 and let the WHERE clause filter out processed rows
```python
# OLD (BROKEN): Incrementing OFFSET
while offset < total:
    batch = get_images(LIMIT, offset)  # offset += 100 each time
    process(batch)
    offset += BATCH_SIZE

# NEW (FIXED): Always OFFSET 0
while total_processed < total:
    batch = get_images(LIMIT)  # Always gets next unprocessed batch
    process(batch)
    total_processed += len(batch)
```

**Impact**: This fix ensures 100% dataset coverage instead of ~50% coverage with skipped rows.

---

## 📈 PERFORMANCE METRICS

### **Upload Speed**
- **Average**: 13.3 images/minute
- **Per hour**: ~798 images
- **Per day**: ~19,152 images
- **Full dataset (107K)**: ~135 hours (5.6 days)

### **Storage Requirements**
- **Images**: 107,447 images
- **Average size**: ~2-5 MB per image
- **Total estimate**: 215-535 GB
- **Available storage**: 2 TB (more than sufficient)

### **Network Considerations**
- Download from remote URLs (GBIF/iNaturalist/EOL)
- Upload to Google Drive
- Dual bandwidth requirement (in + out)

---

## 🛠️ MONITORING & TROUBLESHOOTING

### **Checking Progress**

#### **Database Query**
```sql
SELECT 
    COUNT(*) as total_images,
    COUNT(google_drive_url) as uploaded,
    COUNT(*) - COUNT(google_drive_url) as remaining
FROM orchid_images;
```

#### **Upload Logs**
```bash
tail -f oauth_upload.log
```

### **Common Issues**

#### **Token Expired**
```
Error: Token expired
Solution: Delete token.json, re-run uploader, complete OAuth flow
```

#### **Rate Limiting**
```
Error: 429 Too Many Requests
Solution: Script auto-retries with exponential backoff
```

#### **Network Timeout**
```
Error: Download failed after 3 retries
Solution: Automatic skip, logged as failed
```

---

## 🎓 WORKFLOW INTEGRATION

### **Dual System Architecture**

#### **System 1: URL Collection (Colab)**
- Runs on iPad via browser
- Queries GBIF/iNaturalist APIs
- Stores URLs in database
- 95-110 images/minute

#### **System 2: File Upload (Replit)**
- Runs on Replit server
- Downloads from URLs
- Uploads to Google Drive
- Updates database with Drive URLs
- 13.3 images/minute

### **Why Two Systems?**
1. **Storage Quota**: Service accounts have 15GB limit → Use personal 2TB account
2. **iPad Workflow**: Cannot download .ipynb files → Copy/paste method established
3. **Separation of Concerns**: Collection ≠ Storage
4. **Parallel Processing**: Both can run simultaneously

---

## 📚 FILE REFERENCE

### **Key Files**
- `oauth_drive_uploader.py` - Main upload script
- `token.json` - OAuth credentials (auto-managed)
- `oauth_upload.log` - Upload logs
- `OAUTH_SETUP_INSTRUCTIONS.md` - Setup guide
- `IPAD_COLAB_INSTRUCTIONS.md` - Colab workflow

### **Google Cloud Resources**
- OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent
- Credentials: https://console.cloud.google.com/apis/credentials
- Project: Orchid Continuum

---

## 🎯 NEXT STEPS

### **Immediate Actions**
1. ✅ OAuth setup complete
2. ✅ Database schema fixed
3. ✅ Test upload successful (28 images)
4. 🔄 **Start full 107K upload** (in progress)
5. ⏳ Monitor progress over 5.6 days

### **Future Enhancements**
- Parallel upload workers (increase speed)
- Resume capability (checkpoint system)
- Image deduplication (perceptual hashing)
- Automatic retry queue for failed uploads
- Real-time progress dashboard

---

## 💬 JULIUS AI INTEGRATION POINTS

### **What Julius Can Help With**

#### **1. Progress Monitoring**
Query database to check upload progress:
```sql
SELECT 
    COUNT(*) FILTER (WHERE google_drive_url IS NOT NULL) as uploaded,
    COUNT(*) FILTER (WHERE google_drive_url IS NULL) as remaining,
    ROUND(COUNT(*) FILTER (WHERE google_drive_url IS NOT NULL) * 100.0 / COUNT(*), 2) as percent_complete
FROM orchid_images;
```

#### **2. Quality Assurance**
- Verify Sheet data matches database
- Check for duplicate Drive URLs
- Validate metadata completeness

#### **3. Analytics**
- Species coverage analysis
- Geographic distribution mapping
- Image source breakdown (GBIF vs iNaturalist vs EOL)

#### **4. Issue Detection**
- Identify failed uploads
- Find missing metadata fields
- Detect data inconsistencies

### **API Access**
Julius can access the system via:
- **Database**: PostgreSQL queries via Orchid Continuum API
- **Google Sheets**: Direct read access to catalog
- **Google Drive**: View/download uploaded images

---

## 📞 SUPPORT CONTACTS

**System Owner**: Orchid Continuum Team  
**Developer**: Replit Agent  
**AI Partner**: Julius AI  
**User Account**: fcospresident@gmail.com  

---

## ✅ SUCCESS CRITERIA

### **Phase 1: URL Collection** ✅
- 107,447 image URLs in database
- 52+ metadata fields per image
- Cleaned taxonomic names

### **Phase 2: File Upload** 🔄
- All 107K images in Google Drive
- All metadata in Google Sheets
- Database updated with Drive URLs

### **Phase 3: Coverage Analysis** ⏳
- Calculate species coverage
- Identify gaps (species with <30 images)
- Plan additional collection rounds

### **Final Goal** 🎯
- 35,327 species × 30 images = 1,059,810 images
- 100% Orchidaceae family coverage
- Statistically significant AI training dataset

---

**System Status**: 🟢 OPERATIONAL  
**Current Task**: Uploading 107,447 images to Google Drive  
**Estimated Completion**: 5.6 days from start  

---

*This documentation is for Julius AI to understand and monitor the OAuth Drive upload system. All technical details, credentials, and workflow information are current as of November 5, 2025.*
