# Orchid Image Download Script Issue - Technical Summary

## Goal
Download 2 million orchid images from biodiversity databases to Mac (~/orchid_downloads/)

## Current Status
- **Working**: 24,865 images downloaded (EOL Batch 1, GBIF, iNaturalist, iDigBio)
- **Failing**: New large-scale download scripts crash immediately with no clear errors

## What Works
**Test Script (10 images)** - Proven working:
```python
#!/usr/bin/env python3
import os, requests

output_dir = os.path.expanduser("~/orchid_downloads/test")
os.makedirs(output_dir, exist_ok=True)

params = {'familyKey': 7689, 'mediaType': 'StillImage', 'limit': 10, 'offset': 0}
response = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=30)

for record in response.json().get('results', []):
    media = record.get('media', [])
    if media and media[0].get('identifier'):
        url = media[0]['identifier']
        img = requests.get(url, timeout=15)
        if img.status_code == 200:
            with open(os.path.join(output_dir, f"test_{i}.jpg"), 'wb') as f:
                f.write(img.content)
```
**Result**: Successfully downloaded 10 images (254KB-464KB each)

## What Fails
**Same script scaled to 100K images** - Crashes immediately:
- Process starts (confirmed with `ps aux`)
- Process disappears within seconds
- Log file shows only SSL warning, then nothing
- No error messages
- No images downloaded

## API Diagnostic Results
All APIs tested and confirmed working:

1. **GBIF** ✅
   - Status: 200 OK
   - Available: **2,422,409 orchid images**
   - Test download: SUCCESS
   - Endpoint: `https://api.gbif.org/v1/occurrence/search`

2. **ALA Australia** ✅
   - Status: 200 OK  
   - Available: **297,891 orchid images**
   - Field structure: `occ.get('image')` exists and works
   - Endpoint: `https://biocache-ws.ala.org.au/ws/occurrences/search`

3. **Wikimedia Commons** ✅
   - Status: 200 OK
   - Search returns results
   - Endpoint: `https://commons.wikimedia.org/w/api.php`

## Environment
- **OS**: macOS (exact version unknown)
- **Python**: 3.9
- **SSL Warning**: urllib3 v2 with LibreSSL 2.8.3 (not OpenSSL 1.1.1+)
- **Location**: ~/orchid_downloads/ (24,865 existing images confirmed)

## Failed Approaches (All Crashed Silently)

### 1. Background Process with nohup
```bash
nohup python3 GBIF_MASSIVE.py > ~/orchid_downloads/gbif.log 2>&1 &
```
- Process ID appears, then disappears
- Log shows SSL warning only
- No actual downloads

### 2. Wikimedia Commons Downloader
- Multiple iterations with User-Agent headers
- Category-based searches
- Direct file searches
- All return 0 images despite API returning results

### 3. ALA Australia Downloader  
- Tried `occ['image']` field (exists per diagnostic)
- Tried `occ['multimedia']` array
- Both approaches return 0 images

### 4. EOL Batch 2 Downloader
- Similar pattern - starts, crashes, 0 images

## Suspected Issues (Unconfirmed)

1. **Memory/Resource Limits**: Mac may be killing process due to:
   - Too many file handles
   - Memory exhaustion with large loops
   - Disk space (unlikely - plenty available)

2. **Python Environment**: 
   - SSL library mismatch (LibreSSL vs OpenSSL)
   - Missing dependencies for long-running processes
   - urllib3 compatibility issues

3. **File System Permissions**:
   - Possible limits on ~/orchid_downloads/ directory
   - File descriptor limits

4. **Network/Firewall**:
   - Rate limiting after initial requests
   - ISP throttling on bulk downloads
   - Firewall blocking background processes

## What We Know For Certain
1. ✅ APIs work (diagnostic confirmed)
2. ✅ Small downloads work (10 images successful)
3. ❌ Large-scale loops crash (100K+ target)
4. ❌ Background processes don't survive
5. ⚠️ No useful error messages in logs

## Recommendations for External Help

### Questions to Ask:
1. What's the maximum file descriptor limit on this Mac? (`ulimit -n`)
2. Is there a process/memory limit killing long-running Python scripts?
3. Does macOS kill background Python processes after certain activity?
4. Any firewall/security software blocking bulk HTTP requests?

### Things to Try:
1. Run `ulimit -n 4096` before launching script
2. Test in foreground mode to see actual errors
3. Add explicit error logging to catch exceptions
4. Try downloading in smaller batches (1000 at a time)
5. Monitor Activity Monitor during download
6. Check Console.app for system-level crash logs

## Alternative Approaches

### Option 1: Batch Processing
Download in small batches (1000 images) with separate scripts:
- `GBIF_batch_1.py` (offset 0-1000)
- `GBIF_batch_2.py` (offset 1000-2000)
- etc.

### Option 2: Cloud-Based Download
Run download scripts on:
- Replit server (better resource limits)
- AWS/GCP instance
- DigitalOcean droplet
Transfer completed images to Mac afterward

### Option 3: Use Existing Download Tools
- `wget` with URL list
- `aria2c` (multi-threaded downloader)
- `curl` with parallel downloads

## Files for Reference
- Working test script: `test_download.py` (confirmed working)
- Failed massive script: `GBIF_MASSIVE.py` (crashes)
- Diagnostic script: `diagnostic_test.py` (confirms APIs work)
- Log file: `~/orchid_downloads/gbif.log` (only shows SSL warning)

## Next Steps
1. Document this issue for external technical help
2. Continue with existing 24,865 images
3. Build dashboard to track/manage current collection
4. Revisit bulk downloads after troubleshooting Mac environment
