#!/usr/bin/env python3
"""
Quick test: Download 5 images and upload to Google Drive
"""
import os
os.environ['SHARED_DRIVE_ID'] = '1VtKUMeQr_bAH6wpp37gsz3ecfwX1yS75'

# Import and modify batch size temporarily
import batch_download_to_shared_drive as main_script

# Override batch size for testing
main_script.BATCH_SIZE = 5
main_script.MAX_DOWNLOADS = 5

# Run the main function
if __name__ == "__main__":
    main_script.main()
