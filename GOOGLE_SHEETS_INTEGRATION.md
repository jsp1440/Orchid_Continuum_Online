# Google Sheets Integration - Orchid Continuum

## 📊 Sheet Information

### Primary Orchid Database Sheet
- **Sheet URL**: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz/edit
- **Spreadsheet ID**: `1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz`
- **Sheet Name**: `Sheet1`
- **Owner**: User (Frank)
- **Purpose**: Track all orchid records with images for Julius AI integration

## 📁 Google Drive Integration

### Image Storage Folder
- **Folder URL**: https://drive.google.com/drive/folders/1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS
- **Folder ID**: `1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS`
- **Purpose**: Store orchid images uploaded by Julius AI from GBIF

## 🔑 Credentials

### Service Account (Configured in Replit)
- **Secret Name**: `GOOGLE_SERVICE_ACCOUNT_JSON`
- **Status**: ✅ Configured
- **Permissions**: 
  - Google Drive API access (for image uploads)
  - Google Sheets API access (needs to be enabled in Google Cloud Console)
- **Storage Limit**: 15GB (service account limit)

### Required APIs in Google Cloud Console
1. **Google Drive API** - ✅ Assumed enabled (Julius needs this)
2. **Google Sheets API** - ❌ Currently disabled (error 403)
   - Enable at: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=826523037133
   - Project ID: `826523037133`

## 📋 Sheet Schema (17 Columns)

| Column | Field Name | Data Type | Description | Example |
|--------|------------|-----------|-------------|---------|
| A | id | Integer | Unique record ID | 5916 |
| B | display_name | String | Common/display name | "Cattleya labiata" |
| C | scientific_name | String | Full scientific name | "Cattleya labiata Lindl." |
| D | genus | String | Genus name | "Cattleya" |
| E | species | String | Species epithet | "labiata" |
| F | region | String | Geographic region | "South America" |
| G | country | String | Country | "Brazil" |
| H | decimal_latitude | Number | Latitude | -10.5 |
| I | decimal_longitude | Number | Longitude | -50.2 |
| J | growth_habit | String | Growth type | "epiphytic" |
| K | bloom_time | String | Blooming season | "Fall" |
| L | flower_color | String | Flower colors | "Pink/Purple" |
| M | is_flowering | Boolean | Flowering status | TRUE/FALSE |
| N | image_url | String | Image link | Google Drive URL |
| O | photographer | String | Photographer name | "John Smith" |
| P | data_source | String | Data source | "GBIF" |
| Q | created_at | DateTime | Timestamp | "2025-11-05T12:00:00" |

## 🎯 Usage Workflows

### Workflow 1: Export from PostgreSQL to Google Sheets
**Status**: API Disabled - Using CSV Workaround

**CSV Export Method**:
```bash
# Export 1000 records to CSV
python3 export_orchids_simple.py

# Download from preview server
# URL: https://<preview-server>/static/orchid_data_export.csv
# Import manually to Google Sheets
```

**Direct API Method** (when API enabled):
```bash
# Export first 100 records as test
python3 export_to_google_sheets.py --test

# Export all records
python3 export_to_google_sheets.py

# Export specific amount
python3 export_to_google_sheets.py --limit=5000
```

### Workflow 2: Julius Adds GBIF Data to Sheet
**Status**: Ready (once APIs enabled)

**Julius Process**:
1. Query GBIF API for orchid occurrences
2. Download orchid images from GBIF
3. Upload images to Google Drive folder
4. Get shareable Drive link
5. Add row to Google Sheets with Drive link + metadata

**Helper Script**: `julius_google_sheets_helper.py`

```python
# Example usage
from julius_google_sheets_helper import add_orchid_batch

records = [
    {
        'display_name': 'Cattleya labiata',
        'scientific_name': 'Cattleya labiata Lindl.',
        'genus': 'Cattleya',
        'species': 'labiata',
        'country': 'Brazil',
        'decimal_latitude': -10.5,
        'decimal_longitude': -50.2,
        'growth_habit': 'epiphytic',
        'image_url': 'https://drive.google.com/...',
        'photographer': 'John Smith',
        'data_source': 'GBIF'
    }
]

add_orchid_batch(sheets_service, records)
```

### Workflow 3: Import from Google Sheets to PostgreSQL
**Status**: To be implemented

**Purpose**: Sync Julius's new GBIF data back to main database

```python
# Future script: import_from_google_sheets.py
# 1. Read all rows from Google Sheets
# 2. Check for new records (ID > 5915)
# 3. Insert new records into PostgreSQL orchid_record table
# 4. Update image counts and coverage stats
```

## 📊 Current Statistics

### Database (PostgreSQL)
- **Total Records**: 5,915 orchids
- **Last ID**: 5915
- **Next Available ID**: 5916

### Google Sheet
- **Current Rows**: Header only (empty)
- **Sample Export**: 1,000 records in CSV (ready for import)
- **Target Rows**: 2,000,000+ (ultimate goal)

## 🚀 Getting Started

### For User (Frank)
1. ✅ Download CSV: https://preview-server/static/orchid_data_export.csv
2. ✅ Open Google Sheet: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz/edit
3. Import CSV data (File → Import → Upload → Replace Sheet1)
4. Share Sheet with Julius AI's email address
5. (Optional) Enable Google Sheets API in Console for automated exports

### For Julius AI
1. Verify access to Google Sheet
2. Enable Google Sheets API (if needed for programmatic access)
3. Test with `julius_google_sheets_helper.py` script
4. Begin GBIF data collection workflow:
   - Query GBIF API
   - Download images
   - Upload to Drive
   - Add metadata to Sheet

## 📝 Code Files

| File | Purpose | Status |
|------|---------|--------|
| `export_to_google_sheets.py` | Batch export DB → Sheets | ⚠️ Needs API enabled |
| `export_orchids_simple.py` | CSV export (workaround) | ✅ Working |
| `julius_google_sheets_helper.py` | Julius helper script | ✅ Ready |
| `FOR_JULIUS_GOOGLE_SHEETS.md` | Julius documentation | ✅ Complete |
| `GOOGLE_SHEETS_INTEGRATION.md` | This reference doc | ✅ Complete |

## 🔧 Troubleshooting

### Error: "Google Sheets API has not been used..."
**Solution**: Enable API in Google Cloud Console
- URL: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=826523037133
- Wait 2-3 minutes after enabling

### Error: Permission denied
**Solution**: Share Sheet with service account email
- Find email in GOOGLE_SERVICE_ACCOUNT_JSON
- Share Sheet with edit permissions

### Error: Quota exceeded
**Solutions**:
- Batch uploads (500 rows at a time)
- Add 1-second delay between batches
- Check quotas: https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas

## 🎯 Project Goals

### Phase 1: Foundation (Current)
- ✅ Create Google Sheet structure
- ✅ Export sample data (1,000 records)
- ✅ Document integration for Julius
- ✅ Provide helper scripts

### Phase 2: Julius Integration
- ⏳ Julius enables APIs
- ⏳ Julius tests helper script
- ⏳ Begin GBIF data collection
- ⏳ Upload first 1,000 images to Drive

### Phase 3: Scaling
- ⏳ Automate DB ↔ Sheet sync
- ⏳ Reach 10,000 images (2% coverage)
- ⏳ Reach 100,000 images (20% coverage)
- ⏳ Ultimate goal: 2,000,000+ images (100% coverage)

## 📞 Support

### Questions for Replit Agent
- Database exports
- Python script modifications
- Schema changes
- Server configuration

### Questions for Julius
- GBIF API integration
- Google Cloud setup
- Image processing
- Batch upload optimization

---

**Last Updated**: November 5, 2025  
**Status**: Ready for Julius AI integration  
**Next Step**: User imports CSV to Google Sheet
