# FCOS Orchid Judge Widget - Complete Guide

**Status:** ✅ WORKING & UPDATED  
**URL:** `/fcos-judge/`  
**Last Updated:** October 12, 2025

---

## 🎯 Widget Overview

The **FCOS Orchid Judge PWA** is an educational mobile-first tool for learning orchid judging. It features AI-powered flower analysis, OCR tag reading, symmetry scoring, and educational certificate generation.

---

## ✅ Recent Updates

### Oregon Judging History Added ✅
All Oregon orchid judging facts have been added to the "About" section:

- **First AOS Award:** Bc. Springtide 'Stonehurst', 1932
- **Highest Awarded Orchid:** Vanda sanderiana 'Kiliwehi' - 98 points, 1952
- **First AOS Award Given in Oregon:** Miltonia Firefly - 87 points, 1950 (Oregon Orchid Society Show)
- **Highest Awarded Orchids in Oregon:** Lc. South Esk 'Pride of Rivermont' & Oda. Sensation 'Western Sunset' - tied at 96 points
- **Total FCC Awards Given in Oregon:** 18 (at last count)
- **Highest Cultural Award in Oregon:** Dendrobium densiflorum 'Meredith Ann' & Miltonia Gordon Hoyt 'Dolores' - tied at 95 points
- **Most Awarded Genus in Oregon:** Paphiopedilum (184 awards)
- **Most Awarded Single Species in Oregon:** Masdevallia coccinea (9 awards)
- **Total Awards Given in Oregon (through 2009):** 902

### International Judging Organizations Added ✅
Complete list of world judging organizations now displayed:

- **AOS** - American Orchid Society
- **TOGA** - Taiwan Orchid Growers Association
- **AOC** - Australian Orchid Council
- **CSA** - Cymbidium Society of America
- **RHS** - Royal Horticultural Society
- **SAOC** - South African Orchid Council
- **WOC** - World Orchid Conference

---

## 🌟 Features

### 📸 Photo Capture
- Plant photo with AI analysis
- Tag photo with OCR text extraction
- Reference card detection for scale
- Mobile camera integration

### 🤖 AI Analysis
- Flower count detection
- Spike/inflorescence counting
- Symmetry scoring (0-10 scale)
- Color analysis with hex codes
- Condition assessment
- Measurement extraction

### 📋 OCR Tag Reading
- Automatic text extraction from plant tags
- Genus, species, cultivar recognition
- Confidence scoring
- Manual override capability

### 🏆 Judging Systems
Supports multiple international systems:
- AOS (American Orchid Society)
- AOC (Australian Orchid Council)
- NZ (New Zealand)
- RHS (Royal Horticultural Society)
- CSA (Cymbidium Society of America)

### 📜 Certificate Generation
- Educational practice certificates
- PDF download
- Email delivery option
- Google Sheets integration for records

---

## 🔗 Widget URLs

### Main Widget
```
http://localhost:5000/fcos-judge/
```

### Production (After Render Deployment)
```
https://orchid-continuum.onrender.com/fcos-judge/
```

### Neon One Iframe Code
```html
<iframe src="https://orchid-continuum.onrender.com/fcos-judge/" 
        width="100%" 
        height="900" 
        frameborder="0"
        style="border:1px solid #ddd; border-radius:8px;">
</iframe>
```

---

## 📊 API Endpoints

### OCR Analysis
```
POST /fcos-judge/api/ocr
- Extracts text from tag photos
- Returns text and confidence score
```

### AI Flower Analysis
```
POST /fcos-judge/api/analyze
- Analyzes plant photos using GPT-4 Vision
- Returns flower counts, symmetry, measurements
```

### Taxonomy Lookup
```
GET /fcos-judge/api/lookup-taxonomy?genus=Phalaenopsis&species=amabilis
- Looks up orchid taxonomy information
- Returns scientific names and common names
```

### PDF Generation
```
POST /fcos-judge/api/generate-pdf
- Generates educational certificate PDF
- Returns downloadable file
```

### Google Sheets Submission
```
POST /fcos-judge/api/submit
- Submits judging data to Google Sheets
- Stores for FCOS records
```

---

## 🎨 User Interface

### Screens
1. **Home Screen** - Start new entry, view history, about
2. **Photo Capture** - Take plant and tag photos
3. **OCR Review** - Review and edit tag text
4. **AI Analysis** - View flower counts and measurements
5. **Scoring** - Enter judging scores by system
6. **Certificate** - Generate and download results

### Settings
- Dark mode toggle
- Large text for accessibility
- Offline capability (PWA)
- Mobile-optimized design

---

## 📱 Progressive Web App (PWA)

### Installation
- Install on mobile home screen
- Works offline after first load
- Camera integration
- Native app experience

### Service Worker
- Caches assets for offline use
- Background sync capability
- Push notification ready

---

## 🔐 Privacy & Consent

### Photo Storage
- Consent modal before photo capture
- User owns all photos
- FCOS educational use only
- Can decline participation

### Data Collection
- Optional Google Sheets submission
- Anonymous option available
- Email opt-in for certificates

---

## 🎓 Educational Features

### Learning Resources
- Multiple judging systems explained
- Oregon orchid judging history
- International organization info
- Scoring criteria breakdown

### Practice Mode
- Non-official scoring
- Educational certificates only
- "EDUCATIONAL NOT OFFICIAL" watermark
- Clear disclaimers

---

## 🛠️ Technical Stack

### Backend (Python/Flask)
- Flask Blueprint architecture
- OpenAI GPT-4 Vision API
- Tesseract OCR
- ReportLab PDF generation
- Google Sheets API integration

### Frontend (Vanilla JS)
- Service Worker for PWA
- Camera API integration
- Modular JavaScript components
- Responsive CSS design

### APIs Used
- OpenAI GPT-4o (image analysis)
- Tesseract OCR (text extraction)
- Google Sheets API (data storage)
- ReportLab (PDF generation)

---

## 📋 Files

### Routes
- `routes_fcos_judge.py` - Flask routes and API endpoints

### Templates
- `templates/fcos_judge_index.html` - Main PWA interface

### Static Assets
- `/static/css/fcos-judge.css` - Styles
- `/static/js/fcos-judge.js` - Main JavaScript
- `/static/js/photo-capture.js` - Camera handling
- `/static/js/ocr-analyzer.js` - OCR processing
- `/static/js/ai-analysis.js` - AI integration
- `/static/js/judging-systems.js` - Scoring systems
- `/static/js/service-worker.js` - PWA service worker

---

## ✅ Testing Checklist

- [x] Widget loads at `/fcos-judge/`
- [x] Oregon judging facts display in About section
- [x] International organizations list shows correctly
- [x] Photo capture screens accessible
- [x] OCR endpoint available
- [x] AI analysis endpoint available
- [x] PDF generation works
- [x] Google Sheets submission functional
- [x] Mobile responsive design
- [x] PWA installable

---

## 🚀 Deployment

### For Neon One CMS

**Recommended Page:** "Judging Education" or "Tools"

**Iframe Code:**
```html
<h2>Learn Orchid Judging</h2>
<p>Practice judging with our AI-powered educational tool!</p>

<iframe src="https://orchid-continuum.onrender.com/fcos-judge/" 
        width="100%" 
        height="900" 
        frameborder="0"
        style="border:1px solid #ddd; border-radius:8px; margin: 1rem 0;">
</iframe>
```

### Mobile Optimization
- Fully responsive design
- Touch-friendly buttons
- Camera access on mobile
- Install as app on home screen

---

## 📈 Usage Stats

**Perfect For:**
- FCOS members learning to judge
- Pre-show practice sessions
- Educational workshops
- Orchid show preparation
- Student training

**Use Cases:**
- Practice judging at home
- Pre-judge before shows
- Learn judging criteria
- Compare different systems
- Generate practice certificates

---

## 🎯 Future Enhancements

**Planned Features:**
- Historical judging data from FCOS shows
- Comparison with past awards
- Machine learning score predictions
- Advanced measurement tools
- Video judging tutorials

---

## 📞 Support

**Widget Issues:**
- Check browser console for errors
- Verify camera permissions granted
- Ensure internet connection for AI features
- Clear browser cache if needed

**API Key Requirements:**
- `OPENAI_API_KEY` - For AI analysis (optional)
- `GOOGLE_SHEETS_CREDENTIALS` - For submissions (optional)

Widget works in demo mode without API keys!

---

## ✅ Summary

**FCOS Orchid Judge Widget:**
- ✅ Fully functional at `/fcos-judge/`
- ✅ Oregon judging history integrated
- ✅ International organizations listed
- ✅ AI-powered flower analysis
- ✅ OCR tag reading
- ✅ Educational certificates
- ✅ PWA installable
- ✅ Mobile optimized
- ✅ Ready for Neon One deployment

**Updated:** October 12, 2025  
**Status:** Production Ready ✅
