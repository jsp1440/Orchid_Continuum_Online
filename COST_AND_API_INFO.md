# API Costs & Token Usage - The Truth

## 💰 **ZERO COST - You're Safe!**

### GBIF Image Enrichment
- **API:** GBIF (Global Biodiversity Information Facility)
- **Cost:** $0 - Completely FREE
- **Funded by:** International governments
- **Rate limits:** None (we self-limit to 10 req/sec to be polite)
- **AI tokens used:** ZERO
- **OpenAI calls:** ZERO

### How It Works
```python
# Just simple HTTP requests - NO AI!
requests.get('https://api.gbif.org/v1/species/match', ...)
requests.get('https://api.gbif.org/v1/occurrence/search', ...)
```

**That's it!** No machine learning, no GPT, no tokens.

---

## 🔍 **What USES Tokens/Costs Money:**

### AI Image Analysis (Separate Feature)
- **When:** Only when YOU explicitly analyze images with AI
- **What:** OpenAI Vision API to identify species
- **Cost:** ~$0.01-0.02 per image analyzed
- **Status:** NOT running during enrichment

### The Enrichment Script Does NOT Use:
- ❌ OpenAI API
- ❌ AI tokens
- ❌ Machine learning
- ❌ Any paid services

---

## 📊 **API Call Breakdown:**

### For Each Species (Example):
1. **Get GBIF taxon key:** 1 API call (free)
2. **Get images:** ~5 API calls for 100 images (free)
3. **Total:** ~6 API calls per species (all free)

### For All 35,320 Species:
- **Total API calls:** ~200,000
- **Cost:** $0
- **Time:** ~4-8 hours
- **AI tokens:** 0

---

## 🌐 **Free Public APIs Used:**

| API | Purpose | Cost | Limits |
|-----|---------|------|--------|
| GBIF | Biodiversity data & images | FREE | None |
| EOL | Species page IDs | FREE | None |
| Both | 100% free forever | $0 | No caps |

These are **public good** databases funded by:
- National Science Foundation
- European governments
- Biodiversity research institutions

---

## ⚠️ **The ONLY Things That Cost Money:**

1. **OpenAI Vision API** - When YOU explicitly run AI analysis on images
2. **Google Drive API** - If you store massive amounts of data (free tier: 15GB)
3. **Replit** - Your Replit subscription

**The enrichment script uses NONE of these!**

---

## ✅ **Bottom Line:**

**Collecting 50,000-100,000 orchid images from GBIF:**
- Cost: **$0**
- Tokens: **0**  
- AI calls: **0**
- Just free biodiversity data!

**No hidden costs. No surprises. Just free science! 🌸**

---

## 📝 **Proof (From the Code):**

```python
# validation/enrich_images_simple.py

# These are the ONLY external calls:
requests.get(GBIF_SPECIES_API, ...)  # FREE
requests.get(GBIF_OCCURRENCE_API, ...) # FREE

# NO OpenAI imports
# NO AI tokens
# NO paid services
```

**You can verify this yourself by reading `validation/enrich_images_simple.py`!**
