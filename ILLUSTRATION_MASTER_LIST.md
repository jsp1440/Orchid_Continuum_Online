# ORCHID CONTINUUM UNIVERSITY - ILLUSTRATION MASTER LIST
**Created:** October 23, 2025  
**Source:** ORCHID_COMPREHENSIVE_GLOSSARY.md (240+ terms)  
**Image Source:** Biodiversity Heritage Library (BHL) - 150,000+ public domain illustrations

---

## PURPOSE
This document tracks which botanical illustrations we need for OCU glossary terms and where to find them.

---

## PRIORITY CLASSIFICATION

### 🔴 CRITICAL (Must have for launch) - 15 terms
These are the most distinctive orchid features students MUST understand:

1. **Column** - Front, side, cross-section views with labeled parts
2. **Pollinia** - Close-up showing waxy pollen masses with caudicle and viscidium
3. **Labellum (Lip)** - Multiple lip types (fringed, pouched, lobed)
4. **Resupinate** - Before/after diagram showing 180° flower twist
5. **Epiphyte** - Orchid growing on tree bark showing aerial roots
6. **Mycorrhiza** - Microscopic view of fungal association with roots
7. **Pseudobulb** - Various types (Cattleya, Oncidium, Dendrobium)
8. **Velamen** - Cross-section of aerial root showing spongy tissue
9. **Sympodial** - Growth pattern diagram showing new shoots from rhizome
10. **Monopodial** - Growth pattern showing single vertical stem
11. **Protocorm** - Early seedling stage (no leaves/roots)
12. **Anther cap** - Side view of column showing removable cap
13. **Callus** - Close-up of labellum showing callus structures
14. **Staminode** - Paphiopedilum showing prominent shield-shaped structure
15. **Nectar spur** - Cross-section showing spur and nectar location

### 🟡 HIGH (Important for completeness) - 25 terms
Essential for comprehensive understanding:

16. **Dorsal sepal** - Labeled flower diagram
17. **Lateral sepals** - Flower diagram showing positions
18. **Petal** - Flower diagram labeling all three petals
19. **Sepal** - Labeled diagram showing all three sepals
20. **Stigma** - Column section showing stigmatic surface
21. **Rostellum** - Column cross-section highlighting position
22. **Column foot** - Side profile showing attachment
23. **Mentum (Chin)** - Side view showing structure
24. **Synsepal** - Paphiopedilum showing fused lateral sepals
25. **Aerial roots** - Growing orchid with visible root system
26. **Rhizome** - Underground stem connecting pseudobulbs
27. **Inflorescence** - Various types (spike, raceme, panicle)
28. **Sheath** - Protective covering around new growth
29. **Keiki** - Plantlet growing on mother plant
30. **Meristem** - Growing tip diagram
31. **Clone** - Identical plants from vegetative propagation
32. **Cultivar** - Named variety with specific characteristics
33. **Hybrid** - Cross between two species
34. **Grex** - Named hybrid group
35. **CITES** - Flowchart showing permit requirements
36. **Ex situ** - Cultivation facility diagram
37. **In situ** - Wild habitat preservation
38. **Mycoheterotrophic** - Leafless orchid dependent on fungi
39. **Autogamy** - Self-pollination mechanism
40. **Cleistogamous** - Flower that never opens

### 🟢 MEDIUM (Nice to have) - 50 terms
Enhance learning but not critical for basic understanding

41-90. See full glossary for complete list

### ⚪ LOW (Optional/Text-only sufficient) - 150+ terms
Simple concepts that don't require visual explanation

---

## BHL SEARCH STRATEGY

### Famous Orchid Books (Download First)
1. **"The Orchid Album"** (1882-1897) - 11 volumes, colored lithographs
   - BHL Search: `The Orchid Album Warner Williams`
   - Best for: Flower morphology, species diversity
   
2. **"Orchidaceae of Mexico and Guatemala"** (1837-1843)
   - BHL Search: `Orchidaceae Mexico Guatemala Bateman`
   - Best for: Classic botanical illustrations, whole plant views
   
3. **"Reichenbachia"** (1886)
   - BHL Search: `Reichenbachia orchids Sander`
   - Best for: High-quality chromolithographs, detailed anatomy

### Specific Search Terms for Glossary
Use BHL Flickr (easiest) or main site:

**Flower Morphology (15 CRITICAL terms):**
- Search: `orchid column anatomy`
- Search: `orchid pollinia close up`
- Search: `orchid labellum lip`
- Search: `orchid flower diagram labeled`
- Search: `Paphiopedilum flower anatomy` (for staminode)

**Vegetative Morphology (10 HIGH terms):**
- Search: `orchid pseudobulb`
- Search: `orchid aerial roots`
- Search: `orchid velamen cross section`
- Search: `epiphytic orchid tree`
- Search: `orchid growth habit`

**Ecology (5 CRITICAL terms):**
- Search: `orchid mycorrhiza fungi`
- Search: `orchid pollination mechanism`
- Search: `orchid seed germination`

**Cultivation (5 HIGH terms):**
- Search: `orchid propagation division`
- Search: `orchid keiki plantlet`
- Search: `orchid meristem culture`

---

## DOWNLOAD WORKFLOW

### Step 1: Run BHL Download Script
```bash
# Get free API key first
# Visit: https://www.biodiversitylibrary.org/getapikey.aspx

# Set API key
export BHL_API_KEY="your_key_here"

# Run downloader
python validation/bhl_orchid_downloader.py
```

**What it does:**
- Downloads 50-100 high-quality orchid illustrations
- Organizes by category (morphology_flower, morphology_vegetative, etc.)
- Saves metadata (title, source, page ID)
- Creates `attached_assets/bhl_illustrations/` folder

### Step 2: Manual Download (for specific terms)
For terms the script misses:

1. Go to: https://www.flickr.com/photos/biodivlibrary/
2. Search specific term (e.g., "orchid column")
3. Download high-res image
4. Save to `attached_assets/bhl_illustrations/manual/`

### Step 3: Select Best Images
Review downloaded images and match to glossary terms:

**Selection Criteria:**
- ✅ Clear, high-contrast illustration
- ✅ Scientific accuracy
- ✅ Labeled parts (or easy to add labels)
- ✅ Public domain confirmed
- ✅ High resolution (min 1200px wide)

### Step 4: Add Text Overlays (Canva)
For each selected image:

1. Import to Canva
2. Add text boxes with:
   - Term name (title)
   - Definition (body text)
   - Key parts labeled (arrows/lines)
3. Export as PNG (1920x1080 for web)
4. Save to `attached_assets/ocu_illustrations/ready/`

### Step 5: Upload to University
Import final illustrations to:
- `/static/images/glossary/` folder
- Update glossary database with image paths
- Link from lesson content

---

## PROGRESS TRACKER

### Downloaded (0/90 target)
- [ ] Column anatomy
- [ ] Pollinia close-up
- [ ] Labellum diversity
- [ ] Resupination diagram
- [ ] Epiphyte on tree
- [ ] Mycorrhiza microscopy
- [ ] Pseudobulb types
- [ ] Velamen cross-section
- [ ] Sympodial growth
- [ ] Monopodial growth
- [ ] Protocorm stage
- [ ] Anther cap
- [ ] Callus structure
- [ ] Staminode (slipper)
- [ ] Nectar spur

### Processed (0/90 target)
- [ ] Text overlay added (Canva)
- [ ] Exported at correct size
- [ ] Saved to ready folder

### Uploaded (0/90 target)
- [ ] Added to /static/images/glossary/
- [ ] Database updated
- [ ] Live on website

---

## ALTERNATIVE SOURCES (if BHL insufficient)

### 1. Wikimedia Commons
- URL: https://commons.wikimedia.org/wiki/Category:Orchidaceae
- License: Public domain / CC BY-SA
- Best for: Modern photos, specific genera

### 2. Encyclopedia of Life (EOL)
- Already integrated in database (78,225 traits)
- Check orchid_images.eol_metadata for existing photos
- Best for: Species-specific images

### 3. Smithsonian Gardens
- URL: https://gardens.si.edu/collections/plants/orchids/
- License: Public domain for historic art
- Best for: Botanical art quality

### 4. North American Orchid Conservation Center
- URL: https://northamericanorchidcenter.org/
- License: Educational use (ask permission)
- Best for: Contemporary scientific illustrations

---

## ESTIMATED TIMELINE

**Phase 1: Download (Target: 100 images)**
- Run script: 2-3 hours
- Manual downloads: 3-4 hours
- Total: 1 day

**Phase 2: Selection & Processing (Target: 90 illustrations)**
- Review and select: 2-3 hours
- Canva text overlay: 15 min each × 90 = 22.5 hours
- Total: 3-4 days (if doing 20-25 per day)

**Phase 3: Upload & Integration**
- Upload to server: 1 hour
- Database updates: 2 hours
- Testing: 2 hours
- Total: 1 day

**TOTAL ESTIMATED TIME: 5-6 days** (or 2-3 days if working full-time)

---

## NOTES

- **Budget:** $0 - All images are public domain from BHL
- **No AI generation needed** - Use real historic botanical illustrations
- **Quality over quantity** - Better to have 40 excellent illustrations than 200 mediocre ones
- **Start with CRITICAL priority** - Get the 15 most important terms illustrated first
- **Can launch without all 240** - Minimum viable: 30-40 key illustrations

---

## CONTACT FOR HELP

If BHL download script fails:
1. Check API key is set correctly
2. Try manual download from BHL Flickr
3. Check rate limiting (add longer delays in script)
4. Contact BHL support: https://about.biodiversitylibrary.org/contact/

---

Last Updated: October 23, 2025
