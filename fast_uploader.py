#!/usr/bin/env python3
"""
Optimized OAuth Drive Uploader - Maximum Speed Single Process
Faster than original with larger batches and less logging
"""
import os
import sys
import logging
import time
import psycopg2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
from datetime import datetime
import json

# Minimal logging for speed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Configuration
FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
BATCH_SIZE = 100  # Larger batches for speed
UPDATE_SHEET_EVERY = 50  # Less frequent sheet updates

def main():
    logging.info("🚀 FAST UPLOADER - Authenticating...")
    
    # Load credentials
    with open('token.json', 'r') as token:
        creds_data = json.load(token)
    creds = Credentials.from_authorized_user_info(creds_data)
    
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    logging.info("✅ Authenticated")
    
    # Database connection
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Get total count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orchid_images WHERE google_drive_url IS NULL OR google_drive_url = ''")
    total_remaining = cur.fetchone()[0]
    cur.close()
    
    logging.info(f"📊 Total to upload: {total_remaining:,}")
    
    uploaded_count = 0
    batch_count = 0
    start_time = time.time()
    sheet_batch = []
    
    while True:
        # Fetch batch
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, image_url, taxonomy_id, gbif_occurrence_key, image_source, 
                   image_license, latitude, longitude, country, locality, 
                   observation_date, observer_name
            FROM orchid_images
            WHERE (google_drive_url IS NULL OR google_drive_url = '')
            AND image_url IS NOT NULL
            ORDER BY id
            LIMIT {BATCH_SIZE};
        """)
        batch = cur.fetchall()
        cur.close()
        
        if not batch:
            logging.info("✅ ALL DONE!")
            break
        
        batch_count += 1
        batch_start = time.time()
        
        for img_data in batch:
            try:
                img_id = img_data[0]
                image_url = img_data[1]
                
                # Download image
                response = requests.get(image_url, timeout=30, stream=True)
                if response.status_code != 200:
                    continue
                
                # Determine file extension
                content_type = response.headers.get('content-type', 'image/jpeg')
                ext = '.png' if 'png' in content_type else ('.gif' if 'gif' in content_type else '.jpg')
                
                # Save temp file
                temp_file = f'/tmp/orchid_{img_id}{ext}'
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Upload to Drive
                file_metadata = {
                    'name': f'orchid_{img_id}{ext}',
                    'parents': [FOLDER_ID]
                }
                media = MediaFileUpload(temp_file, resumable=True)
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                drive_url = file.get('webViewLink')
                os.remove(temp_file)
                
                # Update database
                cur = conn.cursor()
                cur.execute("UPDATE orchid_images SET google_drive_url = %s, updated_at = NOW() WHERE id = %s", 
                           (drive_url, img_id))
                conn.commit()
                cur.close()
                
                # Add to sheet batch
                sheet_batch.append([
                    str(img_id),
                    str(img_data[2]) if img_data[2] else '',
                    str(img_data[3]) if img_data[3] else '',
                    image_url,
                    drive_url,
                    str(img_data[4]) if img_data[4] else '',
                    str(img_data[5]) if img_data[5] else '',
                    str(img_data[6]) if img_data[6] else '',
                    str(img_data[7]) if img_data[7] else '',
                    str(img_data[8]) if img_data[8] else '',
                    str(img_data[9]) if img_data[9] else '',
                    str(img_data[10]) if img_data[10] else '',
                    str(img_data[11]) if img_data[11] else '',
                    datetime.now().isoformat()
                ])
                
                uploaded_count += 1
                
                # Bulk update sheet
                if len(sheet_batch) >= UPDATE_SHEET_EVERY:
                    try:
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SHEET_ID,
                            range='Sheet1!A:N',
                            valueInputOption='RAW',
                            body={'values': sheet_batch}
                        ).execute()
                        sheet_batch = []
                    except:
                        pass  # Continue even if sheet update fails
                
            except Exception as e:
                logging.warning(f"⚠️ Skip image {img_id}: {str(e)[:50]}")
                continue
        
        # Batch statistics
        batch_time = time.time() - batch_start
        total_time = time.time() - start_time
        rate = uploaded_count / (total_time / 60) if total_time > 0 else 0
        remaining = total_remaining - uploaded_count
        eta_minutes = remaining / rate if rate > 0 else 0
        eta_hours = eta_minutes / 60
        eta_days = eta_hours / 24
        
        logging.info(f"✅ Batch {batch_count}: {uploaded_count:,} total | {rate:.1f}/min | ETA: {eta_days:.1f} days")
    
    # Upload remaining sheet rows
    if sheet_batch:
        try:
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range='Sheet1!A:N',
                valueInputOption='RAW',
                body={'values': sheet_batch}
            ).execute()
        except:
            pass
    
    conn.close()
    
    total_time = time.time() - start_time
    logging.info(f"🎉 COMPLETE! {uploaded_count:,} images in {total_time/3600:.2f} hours")

if __name__ == '__main__':
    main()
