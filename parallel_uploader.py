#!/usr/bin/env python3
"""
Parallel OAuth Drive Uploader - Maximum Speed
Spawns multiple worker processes to upload in parallel
"""
import os
import sys
import time
import logging
import multiprocessing as mp
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Worker %(process)d] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def worker_upload_batch(worker_id, batch_size=50):
    """
    Worker process that continuously uploads images
    Each worker fetches and processes its own batch
    """
    import psycopg2
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    import requests
    from io import BytesIO
    import json
    from decimal import Decimal
    
    logger = logging.getLogger(f'Worker-{worker_id}')
    logger.info(f"🚀 Worker {worker_id} starting...")
    
    # Load credentials
    try:
        with open('token.json', 'r') as token:
            creds_data = json.load(token)
        creds = Credentials.from_authorized_user_info(creds_data)
        drive_service = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        logger.info(f"✅ Worker {worker_id} authenticated")
    except Exception as e:
        logger.error(f"❌ Worker {worker_id} auth failed: {e}")
        return
    
    # Database connection
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    
    # Target folder and sheet
    FOLDER_ID = '1jQoQ9x-2f1ENZq7iVCgneAmoQIvc6xIS'
    SHEET_ID = '1UQZj4ZaA7cWnU0SozR4_qReWNOm0V9xz'
    
    total_uploaded = 0
    
    try:
        while True:
            # Fetch next batch (always from offset 0 since processed rows are filtered out)
            cur = conn.cursor()
            cur.execute(f"""
                SELECT id, image_url, taxonomy_id, gbif_occurrence_key, image_source, 
                       image_license, latitude, longitude, country, locality, 
                       observation_date, observer_name
                FROM orchid_images
                WHERE (google_drive_url IS NULL OR google_drive_url = '')
                AND image_url IS NOT NULL
                ORDER BY id
                LIMIT {batch_size};
            """)
            batch = cur.fetchall()
            cur.close()
            
            if not batch:
                logger.info(f"✅ Worker {worker_id} finished - no more images")
                break
            
            logger.info(f"📦 Worker {worker_id} processing {len(batch)} images")
            
            for img_data in batch:
                try:
                    img_id = img_data[0]
                    image_url = img_data[1]
                    
                    # Download image
                    response = requests.get(image_url, timeout=30, stream=True)
                    if response.status_code != 200:
                        logger.warning(f"⚠️ Failed to download image {img_id}")
                        continue
                    
                    # Determine file extension
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    ext = '.jpg'
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    
                    # Create temp file
                    temp_file = f'/tmp/orchid_{img_id}{ext}'
                    with open(temp_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Upload to Google Drive
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
                    
                    # Clean up temp file
                    os.remove(temp_file)
                    
                    # Update database
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE orchid_images 
                        SET google_drive_url = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (drive_url, img_id))
                    conn.commit()
                    cur.close()
                    
                    # Add to Google Sheet
                    try:
                        row_data = [
                            str(img_id),
                            str(img_data[2]) if img_data[2] else '',  # taxonomy_id
                            str(img_data[3]) if img_data[3] else '',  # gbif_occurrence_key
                            image_url,
                            drive_url,
                            str(img_data[4]) if img_data[4] else '',  # image_source
                            str(img_data[5]) if img_data[5] else '',  # image_license
                            str(img_data[6]) if img_data[6] else '',  # latitude
                            str(img_data[7]) if img_data[7] else '',  # longitude
                            str(img_data[8]) if img_data[8] else '',  # country
                            str(img_data[9]) if img_data[9] else '',  # locality
                            str(img_data[10]) if img_data[10] else '', # observation_date
                            str(img_data[11]) if img_data[11] else '', # observer_name
                            datetime.now().isoformat()
                        ]
                        
                        sheets_service.spreadsheets().values().append(
                            spreadsheetId=SHEET_ID,
                            range='Sheet1!A:N',
                            valueInputOption='RAW',
                            body={'values': [row_data]}
                        ).execute()
                    except Exception as sheet_error:
                        logger.warning(f"⚠️ Sheet update failed for {img_id}: {sheet_error}")
                    
                    total_uploaded += 1
                    
                    if total_uploaded % 10 == 0:
                        logger.info(f"✅ Worker {worker_id}: {total_uploaded} uploaded")
                    
                except Exception as e:
                    logger.error(f"❌ Worker {worker_id} error on image {img_id}: {e}")
                    continue
            
            logger.info(f"📊 Worker {worker_id} batch complete, fetching next...")
    
    except Exception as e:
        logger.error(f"❌ Worker {worker_id} crashed: {e}")
    finally:
        conn.close()
        logger.info(f"🏁 Worker {worker_id} finished. Total uploaded: {total_uploaded}")

def main():
    """Main parallel upload orchestrator"""
    # Number of parallel workers (adjust based on system resources)
    NUM_WORKERS = 6  # Start with 6 workers for maximum speed
    BATCH_SIZE = 30   # Each worker processes 30 images at a time
    
    print("=" * 80)
    print("🚀 PARALLEL GOOGLE DRIVE UPLOADER - MAXIMUM SPEED")
    print("=" * 80)
    print(f"Workers: {NUM_WORKERS}")
    print(f"Batch size per worker: {BATCH_SIZE}")
    print(f"Estimated speed: {NUM_WORKERS * 2} images/min (6-12x faster!)")
    print("=" * 80)
    print()
    
    # Start time
    start_time = time.time()
    
    # Create worker processes
    processes = []
    for i in range(NUM_WORKERS):
        p = mp.Process(target=worker_upload_batch, args=(i+1, BATCH_SIZE))
        p.start()
        processes.append(p)
        logging.info(f"✅ Started worker {i+1}")
        time.sleep(0.5)  # Stagger starts slightly
    
    # Wait for all workers to complete
    for i, p in enumerate(processes):
        p.join()
        logging.info(f"✅ Worker {i+1} finished")
    
    # Calculate stats
    elapsed = time.time() - start_time
    hours = elapsed / 3600
    
    print()
    print("=" * 80)
    print("🎉 PARALLEL UPLOAD COMPLETE")
    print("=" * 80)
    print(f"⏱️  Time: {hours:.2f} hours")
    print("=" * 80)

if __name__ == '__main__':
    # Enable multiprocessing on all platforms
    mp.set_start_method('spawn', force=True)
    main()
