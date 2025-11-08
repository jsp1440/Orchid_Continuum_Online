"""Inspect what files are in the iDigBio archive"""
import os
import zipfile

archive_path = os.path.expanduser('~/orchid_downloads/temp/idigbio_orchids.zip')

if not os.path.exists(archive_path):
    print("❌ Archive not found at:", archive_path)
    exit(1)

print("📦 Inspecting iDigBio archive...")
print("="*70)

with zipfile.ZipFile(archive_path, 'r') as zip_ref:
    files = zip_ref.namelist()
    print(f"Found {len(files)} files in archive:\n")
    
    for file in sorted(files)[:30]:  # Show first 30
        info = zip_ref.getinfo(file)
        size_mb = info.file_size / 1024 / 1024
        print(f"  {file:50s} {size_mb:8.2f} MB")
    
    if len(files) > 30:
        print(f"\n  ... and {len(files) - 30} more files")

print("\n" + "="*70)
print("✅ Inspection complete!")
