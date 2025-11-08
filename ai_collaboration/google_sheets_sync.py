#!/usr/bin/env python3
"""
Google Sheets Sync for AI Collaboration System
Syncs ai_communication and research_insights tables to Google Sheets
Allows user to monitor and interact with autonomous AI system from Google Sheets!
"""

import psycopg2
import os
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

class GoogleSheetsSyncService:
    def __init__(self):
        """Initialize Google Sheets connection"""
        self.client = None
        self.workbook = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Connect to Google Sheets using service account"""
        try:
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                credentials_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=[
                        'https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                self.client = gspread.authorize(credentials)
                logger.info("✅ Google Sheets connection established")
                return True
            else:
                logger.warning("⚠️  GOOGLE_SERVICE_ACCOUNT_JSON not found")
                logger.info("💡 Set this up to sync data to Google Sheets!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            return False
    
    def get_or_create_workbook(self, title="Orchid Continuum - AI Collaboration"):
        """Get existing workbook or create new one"""
        try:
            # Try to open existing workbook
            try:
                self.workbook = self.client.open(title)
                logger.info(f"✅ Opened existing workbook: {title}")
            except gspread.SpreadsheetNotFound:
                # Create new workbook
                self.workbook = self.client.create(title)
                logger.info(f"✅ Created new workbook: {title}")
                
                # Share with user
                self.workbook.share('fcospresident@gmail.com', perm_type='user', role='writer')
                logger.info(f"✅ Shared with fcospresident@gmail.com")
            
            return self.workbook
            
        except Exception as e:
            logger.error(f"❌ Error with workbook: {e}")
            return None
    
    def sync_ai_communication(self):
        """Sync ai_communication table to Google Sheets"""
        if not self.client:
            logger.warning("⚠️  Google Sheets not connected - skipping sync")
            return
        
        try:
            logger.info("\n🔄 Syncing AI Communication to Google Sheets...")
            
            # Get workbook
            workbook = self.get_or_create_workbook()
            if not workbook:
                return
            
            # Get or create worksheet
            try:
                worksheet = workbook.worksheet("AI Communication")
                # Clear existing data
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = workbook.add_worksheet("AI Communication", rows=1000, cols=15)
            
            # Set headers
            headers = [
                'ID', 'Task ID', 'From Agent', 'To Agent', 'Message Type',
                'Status', 'Priority', 'Prompt Text', 'File Path',
                'Result Summary', 'Error Message', 
                'Created At', 'Read At', 'Completed At'
            ]
            
            # Get data from database
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    id, task_id, from_agent, to_agent, message_type,
                    status, priority, prompt_text, file_path,
                    result_summary, error_message,
                    created_at, read_at, completed_at
                FROM ai_communication
                ORDER BY created_at DESC
                LIMIT 500;
            """)
            
            rows = cur.fetchall()
            
            # Prepare data for sheets (headers + data rows)
            sheet_data = [headers]
            for row in rows:
                # Convert datetime to string
                row_data = list(row)
                for i in range(len(row_data)):
                    if isinstance(row_data[i], datetime):
                        row_data[i] = row_data[i].strftime('%Y-%m-%d %H:%M:%S')
                    elif row_data[i] is None:
                        row_data[i] = ''
                sheet_data.append(row_data)
            
            # Update sheet
            worksheet.update('A1', sheet_data)
            
            # Format header row
            worksheet.format('A1:N1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
            })
            
            # Freeze header row
            worksheet.freeze(rows=1)
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(headers))
            
            logger.info(f"✅ Synced {len(rows)} AI communication records to Google Sheets")
            logger.info(f"📊 View: {worksheet.url}")
            
            conn.close()
            return worksheet.url
            
        except Exception as e:
            logger.error(f"❌ Error syncing AI communication: {e}")
            return None
    
    def sync_research_insights(self):
        """Sync research_insights table to Google Sheets"""
        if not self.client:
            logger.warning("⚠️  Google Sheets not connected - skipping sync")
            return
        
        try:
            logger.info("\n🔄 Syncing Research Insights to Google Sheets...")
            
            # Get workbook
            workbook = self.get_or_create_workbook()
            if not workbook:
                return
            
            # Get or create worksheet
            try:
                worksheet = workbook.worksheet("Research Insights")
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = workbook.add_worksheet("Research Insights", rows=1000, cols=12)
            
            # Set headers
            headers = [
                'ID', 'Type', 'Research Area', 'Insight Text',
                'Confidence Level', 'Proposed Followup',
                'Julius Generated', 'Verified', 'Impact Score',
                'Created At', 'Verified At'
            ]
            
            # Get data from database
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    id, insight_type, research_area, insight_text,
                    confidence_level, proposed_followup,
                    julius_generated, verified, impact_score,
                    created_at, verified_at
                FROM research_insights
                ORDER BY created_at DESC
                LIMIT 500;
            """)
            
            rows = cur.fetchall()
            
            # Prepare data
            sheet_data = [headers]
            for row in rows:
                row_data = list(row)
                for i in range(len(row_data)):
                    if isinstance(row_data[i], datetime):
                        row_data[i] = row_data[i].strftime('%Y-%m-%d %H:%M:%S')
                    elif row_data[i] is None:
                        row_data[i] = ''
                    elif isinstance(row_data[i], bool):
                        row_data[i] = 'Yes' if row_data[i] else 'No'
                sheet_data.append(row_data)
            
            # Update sheet
            worksheet.update('A1', sheet_data)
            
            # Format header
            worksheet.format('A1:K1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.6}
            })
            
            worksheet.freeze(rows=1)
            worksheet.columns_auto_resize(0, len(headers))
            
            logger.info(f"✅ Synced {len(rows)} research insights to Google Sheets")
            logger.info(f"📊 View: {worksheet.url}")
            
            conn.close()
            return worksheet.url
            
        except Exception as e:
            logger.error(f"❌ Error syncing research insights: {e}")
            return None
    
    def sync_orchid_taxonomy(self):
        """Sync orchid_taxonomy to Google Sheets (update existing or create new)"""
        if not self.client:
            logger.warning("⚠️  Google Sheets not connected - skipping sync")
            return
        
        try:
            logger.info("\n🔄 Syncing Orchid Taxonomy to Google Sheets...")
            
            workbook = self.get_or_create_workbook()
            if not workbook:
                return
            
            # Get or create worksheet
            try:
                worksheet = workbook.worksheet("Orchid Taxonomy")
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = workbook.add_worksheet("Orchid Taxonomy", rows=40000, cols=10)
            
            # Set headers
            headers = [
                'ID', 'Genus', 'Species', 'Scientific Name',
                'Common Name', 'Family', 'Subfamily',
                'Distribution', 'Habitat', 'GBIF Key'
            ]
            
            # Get data from database
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    id, genus, species, scientific_name,
                    common_name, family, subfamily,
                    distribution, habitat, gbif_species_key
                FROM orchid_taxonomy
                ORDER BY genus, species
                LIMIT 35500;
            """)
            
            rows = cur.fetchall()
            
            # Prepare data
            sheet_data = [headers]
            for row in rows:
                row_data = list(row)
                for i in range(len(row_data)):
                    if row_data[i] is None:
                        row_data[i] = ''
                sheet_data.append(row_data)
            
            # Update in batches (Google Sheets API limit)
            batch_size = 5000
            for i in range(0, len(sheet_data), batch_size):
                batch = sheet_data[i:i+batch_size]
                start_row = i + 1
                end_row = start_row + len(batch) - 1
                worksheet.update(f'A{start_row}', batch)
                logger.info(f"  📝 Uploaded rows {start_row} to {end_row}")
            
            # Format header
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.8, 'green': 0.5, 'blue': 0.9}
            })
            
            worksheet.freeze(rows=1)
            
            logger.info(f"✅ Synced {len(rows)} taxonomy records to Google Sheets")
            logger.info(f"📊 View: {worksheet.url}")
            
            conn.close()
            return worksheet.url
            
        except Exception as e:
            logger.error(f"❌ Error syncing taxonomy: {e}")
            return None
    
    def sync_orchid_images_summary(self):
        """Sync orchid_images summary to Google Sheets"""
        if not self.client:
            logger.warning("⚠️  Google Sheets not connected - skipping sync")
            return
        
        try:
            logger.info("\n🔄 Syncing Orchid Images Summary to Google Sheets...")
            
            workbook = self.get_or_create_workbook()
            if not workbook:
                return
            
            # Get or create worksheet
            try:
                worksheet = workbook.worksheet("Image Collection Summary")
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = workbook.add_worksheet("Image Collection Summary", rows=40000, cols=12)
            
            # Set headers
            headers = [
                'Scientific Name', 'Genus', 'Species',
                'GBIF Images', 'EOL Images', 'Total Images',
                'Has GPS Data', 'Has Traits', 'Coverage Score',
                'Last Updated'
            ]
            
            # Get aggregated data from database
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                WITH gbif_counts AS (
                    SELECT 
                        scientific_name,
                        COUNT(*) as gbif_count,
                        SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as gps_count
                    FROM orchid_images
                    WHERE source = 'GBIF'
                    GROUP BY scientific_name
                ),
                eol_counts AS (
                    SELECT 
                        scientific_name,
                        COUNT(*) as eol_count
                    FROM eol_images
                    GROUP BY scientific_name
                )
                SELECT 
                    t.scientific_name,
                    t.genus,
                    t.species,
                    COALESCE(g.gbif_count, 0) as gbif_images,
                    COALESCE(e.eol_count, 0) as eol_images,
                    COALESCE(g.gbif_count, 0) + COALESCE(e.eol_count, 0) as total_images,
                    CASE WHEN g.gps_count > 0 THEN 'Yes' ELSE 'No' END as has_gps,
                    'Pending' as has_traits,
                    CASE 
                        WHEN COALESCE(g.gbif_count, 0) + COALESCE(e.eol_count, 0) >= 50 THEN 'Excellent'
                        WHEN COALESCE(g.gbif_count, 0) + COALESCE(e.eol_count, 0) >= 10 THEN 'Good'
                        WHEN COALESCE(g.gbif_count, 0) + COALESCE(e.eol_count, 0) >= 1 THEN 'Fair'
                        ELSE 'No Images'
                    END as coverage,
                    NOW() as updated_at
                FROM orchid_taxonomy t
                LEFT JOIN gbif_counts g ON t.scientific_name = g.scientific_name
                LEFT JOIN eol_counts e ON t.scientific_name = e.scientific_name
                ORDER BY total_images DESC, t.genus, t.species
                LIMIT 35500;
            """)
            
            rows = cur.fetchall()
            
            # Prepare data
            sheet_data = [headers]
            for row in rows:
                row_data = list(row)
                for i in range(len(row_data)):
                    if isinstance(row_data[i], datetime):
                        row_data[i] = row_data[i].strftime('%Y-%m-%d %H:%M:%S')
                    elif row_data[i] is None:
                        row_data[i] = ''
                sheet_data.append(row_data)
            
            # Update in batches
            batch_size = 5000
            for i in range(0, len(sheet_data), batch_size):
                batch = sheet_data[i:i+batch_size]
                start_row = i + 1
                end_row = start_row + len(batch) - 1
                worksheet.update(f'A{start_row}', batch)
                logger.info(f"  📝 Uploaded rows {start_row} to {end_row}")
            
            # Format header
            worksheet.format('A1:J1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.7, 'blue': 0.4}
            })
            
            worksheet.freeze(rows=1)
            
            logger.info(f"✅ Synced {len(rows)} image summaries to Google Sheets")
            logger.info(f"📊 View: {worksheet.url}")
            
            conn.close()
            return worksheet.url
            
        except Exception as e:
            logger.error(f"❌ Error syncing images summary: {e}")
            return None
    
    def sync_all(self):
        """Sync all tables to Google Sheets"""
        if not self.client:
            logger.error("❌ Google Sheets not connected!")
            logger.info("\n💡 To enable Google Sheets sync:")
            logger.info("   1. Create a Google Cloud service account")
            logger.info("   2. Enable Google Sheets API")
            logger.info("   3. Set GOOGLE_SERVICE_ACCOUNT_JSON secret")
            logger.info("   4. Run this script again!")
            return None
        
        logger.info("\n" + "="*60)
        logger.info("🚀 SYNCING ALL DATA TO GOOGLE SHEETS")
        logger.info("="*60)
        
        results = {
            'ai_communication': self.sync_ai_communication(),
            'research_insights': self.sync_research_insights(),
            'orchid_taxonomy': self.sync_orchid_taxonomy(),
            'image_summary': self.sync_orchid_images_summary()
        }
        
        logger.info("\n" + "="*60)
        logger.info("✅ SYNC COMPLETE!")
        logger.info("="*60)
        
        if self.workbook:
            logger.info(f"\n📊 Workbook URL: {self.workbook.url}")
            logger.info(f"👤 Shared with: fcospresident@gmail.com")
            logger.info("\n📱 Access from:")
            logger.info("   - Any computer")
            logger.info("   - iPad/iPhone (Google Sheets app)")
            logger.info("   - Any browser")
        
        return results

def run_sync():
    """Run sync process"""
    sync = GoogleSheetsSyncService()
    return sync.sync_all()

if __name__ == "__main__":
    run_sync()
