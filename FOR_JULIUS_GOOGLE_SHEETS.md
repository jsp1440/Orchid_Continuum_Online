# Julius AI - Google Sheets Integration Guide

## 🎯 Your Mission
Add new GBIF orchid image data to our shared Google Sheet as you process images.

## 📊 Google Sheet Information
- **Sheet URL**: https://docs.google.com/spreadsheets/d/1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz/edit
- **Sheet ID**: `1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz`
- **Sheet Name**: `Sheet1`

## 🗂️ Current Database Stats
- **Total orchid records**: 5,915 in PostgreSQL database
- **Sample export**: 1,000 records exported to CSV (available for import)
- **CSV location**: `/static/orchid_data_export.csv` (download from preview server)

## 📋 Column Structure (17 fields)
The sheet has these columns in this exact order:

1. **id** - Record ID number
2. **display_name** - Common display name
3. **scientific_name** - Full scientific name
4. **genus** - Genus (e.g., "Phalaenopsis")
5. **species** - Species epithet
6. **region** - Geographic region
7. **country** - Country of observation
8. **decimal_latitude** - Latitude coordinate
9. **decimal_longitude** - Longitude coordinate
10. **growth_habit** - Growth pattern (epiphytic, terrestrial, etc.)
11. **bloom_time** - Blooming season
12. **flower_color** - Flower colors
13. **is_flowering** - TRUE/FALSE
14. **image_url** - Direct link to image
15. **photographer** - Photographer name
16. **data_source** - Source (GBIF, EOL, iNaturalist, etc.)
17. **created_at** - Timestamp when added

## 🚀 How to Add New GBIF Data

### Method 1: Append Rows via Google Sheets API
Use Python with Google Sheets API:

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SPREADSHEET_ID = "1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz"

# Initialize service
creds = service_account.Credentials.from_service_account_file(
    'your-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=creds)

# Your new GBIF data
new_rows = [
    [5916, "Cattleya labiata", "Cattleya labiata Lindl.", "Cattleya", "labiata", 
     "South America", "Brazil", -10.5, -50.2, "epiphytic", "Fall", "Pink/Purple",
     "TRUE", "https://gbif.org/image123", "John Smith", "GBIF", "2025-11-05T12:00:00"]
]

# Append to sheet
body = {'values': new_rows}
service.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A:Q',  # A through Q = 17 columns
    valueInputOption='RAW',
    body=body
).execute()

print(f"✅ Added {len(new_rows)} new orchids!")
```

### Method 2: Batch Upload (More Efficient)
For processing many images at once:

```python
# Process 100 GBIF images at a time
batch_rows = []

for gbif_occurrence in your_gbif_data:
    row = [
        next_id,
        display_name,
        scientific_name,
        genus,
        species,
        region,
        country,
        latitude,
        longitude,
        growth_habit,
        bloom_time,
        flower_color,
        'TRUE' if flowering else 'FALSE',
        image_url,
        photographer,
        'GBIF',
        datetime.now().isoformat()
    ]
    batch_rows.append(row)

# Append batch
body = {'values': batch_rows}
service.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID,
    range='Sheet1!A:Q',
    valueInputOption='RAW',
    body=body
).execute()
```

## 🔑 Google Sheets API Setup
If you get "API not enabled" errors:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Enable **Google Sheets API** for your project
3. Use the same service account credentials you use for Drive
4. Wait 2-3 minutes for API activation to propagate

## 📁 Google Drive Integration
Your Google Drive folder for images:
- **Folder ID**: `1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS`
- **Folder URL**: https://drive.google.com/drive/folders/1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS

Upload workflow:
1. Download GBIF image
2. Upload to Drive folder
3. Get shareable link
4. Add row to Google Sheet with Drive link in `image_url` column

## 🎯 Your Workflow (Recommended)

```python
# 1. Fetch GBIF data
gbif_data = fetch_gbif_occurrences(genus="Cattleya", limit=100)

# 2. Process each occurrence
for occurrence in gbif_data:
    # Download image
    image_file = download_gbif_image(occurrence.image_url)
    
    # Upload to Google Drive
    drive_link = upload_to_drive(image_file, folder_id)
    
    # Prepare sheet row
    row = [
        get_next_id(),  # Auto-increment from last row
        occurrence.common_name,
        occurrence.scientific_name,
        occurrence.genus,
        occurrence.species,
        occurrence.region,
        occurrence.country,
        occurrence.latitude,
        occurrence.longitude,
        determine_growth_habit(occurrence),
        determine_bloom_time(occurrence),
        extract_flower_color(occurrence),
        'TRUE' if 'flower' in occurrence.description else 'FALSE',
        drive_link,  # ← Google Drive link, not GBIF link
        occurrence.photographer,
        'GBIF',
        datetime.now().isoformat()
    ]
    
    # Add to batch
    batch.append(row)
    
    # Upload batch every 50 images
    if len(batch) >= 50:
        append_to_sheet(batch)
        batch = []
```

## 🔢 Next Available ID
Check the last row of the sheet to see the highest ID number, then continue from there.

Example: If last row is ID 5915, your first new row should be ID 5916.

## 💾 Data Consistency
**Important**: Keep these values consistent:
- **growth_habit**: epiphytic, terrestrial, lithophytic, or combination
- **bloom_time**: Spring, Summer, Fall, Winter, Year-round, Variable
- **data_source**: GBIF, EOL, iNaturalist, Tropicos, iDigBio
- **is_flowering**: Always use TRUE or FALSE (not true/false)

## ✅ Testing Your Integration
1. Add 1-2 test rows to verify your setup works
2. Check that all 17 columns are populated (empty strings OK for missing data)
3. Verify Drive image links are accessible
4. Confirm timestamps are ISO format (YYYY-MM-DDTHH:MM:SS)

## 🎉 Expected Results
After you process GBIF data:
- Google Sheet grows with new orchid records
- Google Drive fills with orchid images
- We can import Sheet data back to PostgreSQL database
- Coverage increases toward goal of 2 million images!

## 📞 Questions?
If you run into issues:
1. Check API is enabled in Google Cloud Console
2. Verify service account has edit permissions on the Sheet
3. Ensure Drive folder ID is correct
4. Test with small batches first (10 rows) before large uploads

---

**Current Status**: Ready for Julius to start adding GBIF data! 🚀
