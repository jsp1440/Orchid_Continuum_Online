#!/usr/bin/env python3
"""
Create Google Sheets template with all Orchid Continuum fields
This exports the database schema to a Google Sheet for Julius to populate
"""
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# All 52+ database fields for orchid_record
ORCHID_FIELDS = [
    # Core Identity
    "id", "display_name", "scientific_name", "genus", "species", "author",
    "common_names", "taxonomy_id",
    
    # Taxonomy & Classification
    "is_hybrid", "is_species", "grex_name", "clone_name", 
    "pod_parent", "pollen_parent", "parentage_formula", "generation",
    "rhs_registration_id", "registration_date", "registrant",
    
    # Geographic Data
    "region", "native_habitat", "country", "state_province", "locality",
    "decimal_latitude", "decimal_longitude", "latitude", "longitude",
    "elevation_m", "coordinate_uncertainty_m", "continent",
    
    # Collection Metadata
    "collector", "collection_number", "event_date", "observation_date",
    "institution_code", "collection_code", "catalog_number",
    "recorded_by", "record_number", "basis_of_record",
    
    # Growing Characteristics
    "growth_habit", "climate_preference", "bloom_time", 
    "leaf_form", "pseudobulb_presence",
    "light_requirements", "temperature_range", 
    "water_requirements", "fertilizer_needs", "cultural_notes",
    
    # Flowering Details
    "is_flowering", "flowering_stage", "flower_count", "inflorescence_count",
    "flower_size_mm", "flower_color", "bloom_stage", "inflorescence_type",
    "flower_longevity_days", "fragrance", "fragrance_description",
    
    # Morphology Details
    "leaf_shape", "pseudobulb_form", "labellum_type", 
    "flower_resupination", "rhizome_spread_type", "tissue_succulence",
    
    # Image & Media
    "image_filename", "image_url", "google_drive_id", 
    "photographer", "image_source", "image_attribution",
    
    # External Database IDs
    "gbif_taxon_key", "gbif_occurrence_key", "eol_page_id",
    "inaturalist_observation_id", "data_source",
    
    # AI Analysis
    "ai_description", "ai_confidence", "ocr_text",
    
    # System Metadata
    "ingestion_source", "validation_status", "created_at", "updated_at"
]

def create_orchid_sheets_template():
    """Create Google Sheets template with proper structure"""
    
    # Load service account credentials
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
        return None
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # Create new spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'Orchid Continuum - Master Database Template'
            },
            'sheets': [
                {
                    'properties': {
                        'title': 'Orchid Records',
                        'gridProperties': {
                            'frozenRowCount': 1,
                            'frozenColumnCount': 2
                        }
                    }
                }
            ]
        }
        
        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']
        print(f"✅ Created spreadsheet: {spreadsheet_id}")
        
        # Add header row
        header_row = [ORCHID_FIELDS]
        
        body = {
            'values': header_row
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Orchid Records!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format header row (bold, frozen)
        requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.48, 'green': 0.17, 'blue': 0.75},
                            'textFormat': {
                                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }
        ]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"\n🌺 Orchid Continuum Google Sheets Template Created!")
        print(f"📊 Spreadsheet ID: {spreadsheet_id}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        print(f"📋 Fields: {len(ORCHID_FIELDS)} columns")
        
        return spreadsheet_id
        
    except HttpError as error:
        print(f"❌ Error creating spreadsheet: {error}")
        return None

if __name__ == '__main__':
    create_orchid_sheets_template()
