#!/usr/bin/env python3
"""Test static download with 5 images"""
import download_to_static

# Override batch size for testing
download_to_static.BATCH_SIZE = 5

if __name__ == "__main__":
    download_to_static.main()
