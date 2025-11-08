# Tropicos Integration Guide
## Missouri Botanical Garden API Integration

Last Updated: October 20, 2025

---

## Overview

The Orchid Continuum now integrates with **Tropicos**, Missouri Botanical Garden's authoritative botanical information system containing **4.2+ million herbarium specimens** with images and taxonomic data.

### What is Tropicos?

Tropicos is the world's largest database of botanical nomenclature and specimen data, maintained by the Missouri Botanical Garden since 1982. It provides:

- **Authoritative taxonomy**: Verified scientific names and nomenclature
- **Herbarium specimens**: 4.2M+ digitized specimen records
- **High-quality images**: Specimen photographs from worldwide collections
- **Nomenclatural data**: Publication history, type specimens, synonymy
- **Global coverage**: Special strength in Neotropical, African, and Asian orchids

---

## API Capabilities

### 1. Name Search
Search for orchid names (exact or wildcard matching):
```
http://services.tropicos.org/Name/Search
?name=Phalaenopsis+amabilis
&type=wildcard
&apikey=YOUR_KEY
&format=json
```

**Returns**: List of matching names with IDs

### 2. Name Details
Get comprehensive nomenclatural information:
```
http://services.tropicos.org/Name/{NameId}
?apikey=YOUR_KEY
&format=json
```

**Returns**: Author, rank, family, status, publication details

### 3. Synonyms
Retrieve all synonyms for a name:
```
http://services.tropicos.org/Name/{NameId}/Synonyms
?apikey=YOUR_KEY
&format=json
```

**Returns**: List of synonymous names

### 4. Accepted Names
Get currently accepted names:
```
http://services.tropicos.org/Name/{NameId}/AcceptedNames
?apikey=YOUR_KEY
&format=json
```

**Returns**: Taxonomically accepted name(s)

### 5. Images
Access specimen images:
```
http://services.tropicos.org/Image/Search
?nameid={NameId}
&apikey=YOUR_KEY
&format=json
```

**Returns**: Image URLs, photographer, copyright, specimen info

### 6. Specimens
Get herbarium specimen records:
```
http://services.tropicos.org/Name/{NameId}/Specimens
?apikey=YOUR_KEY
&format=json
```

**Returns**: Collection data, location, collector, institution

---

## Integration Architecture

### Data Flow

```
1. Orchid Taxonomy Database
   ↓
2. Search Tropicos API for scientific name
   ↓
3. Retrieve:
   - Name details
   - Synonyms
   - Accepted names
   - Specimens
   - Images
   ↓
4. Store in PostgreSQL:
   - Taxonomy metadata → external_ids JSONB field
   - Images → orchid_images table
```

### Database Schema

#### orchid_taxonomy.external_ids
Stores Tropicos data in JSONB format:
```json
{
  "tropicos": {
    "tropicos_name_id": 25509881,
    "tropicos_rank": "Species",
    "tropicos_status": "Accepted",
    "tropicos_author": "L.",
    "tropicos_family": "Orchidaceae",
    "tropicos_synonyms": ["Epidendrum amabile", "..."],
    "tropicos_accepted_names": ["Phalaenopsis amabilis"],
    "tropicos_specimen_count": 147,
    "tropicos_last_updated": "2025-10-20T12:00:00"
  }
}
```

#### orchid_images.tropicos_metadata
Stores image-specific metadata:
```json
{
  "ImageId": 123456,
  "Copyright": "Missouri Botanical Garden",
  "Photographer": "John Smith",
  "ImageKind": "Specimen",
  "DetailJpgUrl": "https://...",
  "SpecimenId": "MO-123456"
}
```

---

## Setup Instructions

### 1. Get API Key

Your API key is already configured in Replit Secrets:
- Key name: `TROPICOS_API_KEY`
- Access via: Replit Secrets (Tools → Secrets)

**SECURITY**: Never share your API key publicly or commit it to files!

To request additional keys or manage existing ones:
1. Visit: http://services.tropicos.org/help?requestkey
2. Fill out the API key request form
3. Missouri Botanical Garden will email your key

### 2. Run Enrichment

Execute the Tropicos enrichment script:

```bash
python validation/enrich_tropicos.py
```

**What it does:**
- Searches all 35,320 orchid species in database
- Retrieves authoritative nomenclatural data
- Downloads herbarium specimen images
- Updates taxonomy records with Tropicos IDs
- Logs progress to `/tmp/tropicos.log`

### 3. Monitor Progress

The script provides real-time progress updates:
```
====================================================================
🌿 TROPICOS IMAGE & DATA COLLECTOR
Missouri Botanical Garden - 4.2M+ Herbarium Specimens
====================================================================
    1 | Phalaenopsis amabilis                              | ID:25509881 | Img: 12 | Spec: 47 | 1.2 sp/min
    2 | Dendrobium nobile                                  | ID:25510234 | Img:  8 | Spec: 23 | 1.5 sp/min
...
```

---

## Features & Benefits

### For Researchers

✅ **Authoritative Taxonomy**: Verified by Missouri Botanical Garden botanists
✅ **Type Specimens**: Access to holotype and isotype specimen images
✅ **Publication History**: Original descriptions and nomenclatural citations
✅ **Global Coverage**: Specimens from 200+ countries
✅ **Historical Data**: Records dating back to 1703

### For the Platform

✅ **Additional Images**: Complements GBIF (104K+) and EOL (5.8M) collections
✅ **Specimen Context**: Herbarium data provides scientific provenance
✅ **Nomenclatural Verification**: Cross-reference taxonomy with authoritative source
✅ **Citation Data**: Proper attribution for academic use
✅ **FREE Access**: No cost beyond standard API limits

---

## API Limits & Best Practices

### Rate Limits
- **No official limit** documented by Tropicos
- **Recommended**: 0.5 second delay between requests
- **Our implementation**: 0.5s delay + exponential backoff on errors

### Request Limits
- **No daily limit** on standard API keys
- **Large-scale use**: Contact Tropicos for bulk access

### Best Practices
1. **Cache results**: Store data locally to minimize repeat requests
2. **Handle errors gracefully**: API can be slow during peak hours
3. **Respect copyright**: Attribute images to photographers and MBG
4. **Verify data**: Cross-reference with other sources (GBIF, EOL)

---

## Data Quality

### Strengths
- ✅ Authoritative botanical nomenclature
- ✅ Curated by professional botanists
- ✅ Type specimen records
- ✅ Historical collections (300+ years)
- ✅ Strong Neotropical coverage

### Limitations
- ⚠️ Specimen images (not living plants)
- ⚠️ Limited Asian coverage compared to GBIF
- ⚠️ Slower updates than crowd-sourced platforms
- ⚠️ Fewer images per species than EOL

### Recommended Use
- **Primary**: Taxonomic verification and nomenclature
- **Secondary**: Specimen images and collection data
- **Combined with**: GBIF (wild images) + EOL (variety)

---

## Integration with Other Sources

### GBIF (Global Biodiversity Information Facility)
- **Tropicos**: Authoritative names, specimen images
- **GBIF**: Wild occurrence images, distribution data
- **Complement**: Tropicos verifies names, GBIF shows living plants

### EOL (Encyclopedia of Life)
- **Tropicos**: Missouri Botanical Garden specimens
- **EOL**: Aggregated from 5.8M global images
- **Complement**: Tropicos = scientific, EOL = comprehensive

### Combined Power
```
Tropicos (4.2M specimens)
  + GBIF (104K+ orchid images)
  + EOL (5.8M images)
  = 10M+ authoritative orchid data points
```

---

## Technical Implementation

### Script Location
`validation/enrich_tropicos.py`

### Key Functions

**search_tropicos_name()**
- Searches Tropicos for scientific name
- Returns: Name ID, rank, family
- Handles: Wildcards, retries, rate limits

**get_images()**
- Retrieves specimen images for a name ID
- Extracts: URL, photographer, copyright, specimen ID
- Saves: JSON metadata to database

**update_taxonomy_tropicos()**
- Merges Tropicos data into external_ids field
- Preserves: Existing GBIF, EOL, iNaturalist data
- Atomic: All-or-nothing database updates

### Error Handling
- ✅ Exponential backoff on API failures
- ✅ Database connection pooling
- ✅ Transaction rollback on errors
- ✅ Graceful handling of missing data
- ✅ Comprehensive logging to `/tmp/tropicos.log`

---

## Example API Calls

### Search for Orchid
```bash
curl "http://services.tropicos.org/Name/Search?name=Phalaenopsis&type=wildcard&apikey=YOUR_KEY&format=json"
```

**Response:**
```json
[
  {
    "NameId": 25509881,
    "ScientificName": "Phalaenopsis amabilis",
    "Rank": "Species",
    "Family": "Orchidaceae",
    "Author": "(L.) Blume"
  }
]
```

### Get Images
```bash
curl "http://services.tropicos.org/Image/Search?nameid=25509881&apikey=YOUR_KEY&format=json"
```

**Response:**
```json
[
  {
    "ImageId": 100123456,
    "Copyright": "Missouri Botanical Garden",
    "Photographer": "Barbara Alongi",
    "ImageKind": "Specimen",
    "DetailJpgUrl": "https://www.tropicos.org/Image/100123456",
    "SpecimenId": "MO-1234567"
  }
]
```

---

## Troubleshooting

### Problem: "No matches found"
**Cause**: Species name not in Tropicos database
**Solution**: Normal - Tropicos focuses on Neotropical species. GBIF/EOL have broader coverage.

### Problem: "API timeout"
**Cause**: Tropicos server slow or high load
**Solution**: Script automatically retries with exponential backoff

### Problem: "No images returned"
**Cause**: Not all specimens are photographed
**Solution**: Normal - combine with GBIF and EOL for maximum coverage

### Problem: "Database error"
**Cause**: PostgreSQL connection issue
**Solution**: Check DATABASE_URL in environment, restart script

---

## Future Enhancements

### Planned Features
- [ ] Automatic re-enrichment for updated specimens
- [ ] Tropicos distribution map integration
- [ ] Type specimen highlighting in gallery
- [ ] Nomenclatural history timeline
- [ ] Herbarium specimen viewer widget

### Integration Ideas
- [ ] Link to physical specimens in MBG herbarium
- [ ] Cross-reference with other major herbaria (K, NY, L)
- [ ] Integrate with IPNI for publication data
- [ ] Add Tropicos citation export for papers

---

## Resources

### Official Documentation
- **API Help**: http://services.tropicos.org/help
- **Main Portal**: https://www.tropicos.org/
- **Orchid Project**: http://legacy.tropicos.org/Project/Orchids

### Contact
- **API Support**: Contact through Tropicos website
- **Data Questions**: Missouri Botanical Garden
- **Bug Reports**: Use Orchid Continuum bug report system

---

## License & Attribution

### Data License
Tropicos data is provided by Missouri Botanical Garden under their standard data use agreement.

### Image Attribution
All images must be attributed to:
```
Photographer Name (if provided)
Missouri Botanical Garden
Tropicos.org
```

### Citation Format
For academic papers:
```
Missouri Botanical Garden. [Year]. Tropicos.org. 
Missouri Botanical Garden. Retrieved [Date] from http://www.tropicos.org
```

---

## Summary

✅ **4.2M+ herbarium specimens** with authoritative botanical data
✅ **FREE API access** with your existing key
✅ **Automatic enrichment** via `validation/enrich_tropicos.py`
✅ **Seamless integration** with existing GBIF and EOL data
✅ **Production-ready** with error handling and logging

**Start enriching now:**
```bash
python validation/enrich_tropicos.py
```

Tropicos adds the authoritative voice of Missouri Botanical Garden to your orchid research platform! 🌿
