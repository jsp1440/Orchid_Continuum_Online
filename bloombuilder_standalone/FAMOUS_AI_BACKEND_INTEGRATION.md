# 🔌 Famous AI Backend Integration Guide

## **IMPORTANT: The Backend Is Already Built and Running!**

**Famous AI - DO NOT rebuild the backend!** All APIs, database, and functionality are complete. You only need to:
1. Connect to the existing backend
2. Design the frontend
3. Make API calls to the provided endpoints

---

## 🗄️ **DATABASE CONNECTION**

### **PostgreSQL Database (Already Set Up)**

The BloomBuilder backend uses a PostgreSQL database that's already running with all tables created.

**Connection Details:**
```bash
Database URL: Available via DATABASE_URL environment variable
Host: Provided by Replit
Port: 5432
Database: Automatically configured
```

**Important Tables:**
- `bloombuilder_species` - 25 NAOCC species
- `bloombuilder_creations` - User creations
- `orchid_images` - Image gallery (herbarium, plates, photos)
- `orchid_traits` - Trait toggle data
- `ocu_glossary_terms` - 1,763 botanical terms

**DO NOT create new database or tables - everything exists!**

---

## 🌐 **BACKEND API ENDPOINTS**

### **Base URL**
```
Production: https://[replit-domain]/bloombuilder
Development: http://localhost:5000/bloombuilder
```

### **All Available Endpoints:**

#### **1. Species Selection**
```http
GET /bloombuilder/
Returns: Species selector page with all 25 species

GET /bloombuilder/api/species/{species_id}
Returns: Complete species data including images and traits
```

#### **2. Multi-Stage Gallery**
```http
GET /bloombuilder/gallery/{species_id}
Returns: Gallery selector page

GET /bloombuilder/api/images/{species_id}
Returns: All images (herbarium, plates, photos) with metadata
Response includes: date, location, collector, source
```

#### **3. Workbench & Canvas**
```http
GET /bloombuilder/workbench/{species_id}
Returns: Main workbench interface

POST /bloombuilder/api/save-creation
Body: {
  species_id: number,
  creator_name: string,
  image_data: base64 PNG string,
  style: string,
  canvas_data: object
}
Returns: {success: true, creation_id: number, filename: string}
```

#### **4. Trait Toggle System**
```http
GET /bloombuilder/api/traits/{species_id}
Returns: All available traits for species

POST /bloombuilder/api/traits/toggle
Body: {
  species_id: number,
  trait_category: string,
  new_value: string
}
Returns: Updated image URL showing that phenotype
```

#### **5. Glossary Search**
```http
GET /bloombuilder/api/glossary/search?term={search_term}
Returns: Matching botanical terms with definitions

GET /bloombuilder/api/glossary/random
Returns: Random term (for "word of the day")
```

---

## 🔑 **AUTHENTICATION & SECURITY**

### **Current Setup: No Authentication Required**

The backend is currently **open** - no API keys or authentication needed for development.

**Why?** This is an educational tool for students. Authentication can be added later if needed.

**Session Management:**
- Flask sessions track user progress
- Session ID auto-generated for anonymous users
- Stored in cookies (handled automatically)

---

## 📁 **FILE STORAGE**

### **User Creation Storage**

**Where files are saved:**
```bash
Directory: /static/uploads/bloombuilder/
Filename format: orchid_{species_id}_{timestamp}_{style}.png
Public URL: https://[domain]/static/uploads/bloombuilder/{filename}
```

**How it works:**
1. User saves creation in workbench
2. Canvas exports as base64 PNG
3. Frontend sends to `/api/save-creation`
4. Backend decodes and saves to disk
5. Database stores filename reference
6. User can download via public URL

**Famous AI - You handle canvas export, backend handles storage!**

---

## 🔧 **ENVIRONMENT VARIABLES**

### **Required for Backend (Already Set):**
```bash
DATABASE_URL=postgresql://[credentials]
SESSION_SECRET=[auto-generated]
REPLIT_DEV_DOMAIN=[your-domain]
```

### **Optional API Keys (For Enhanced Features):**
```bash
GOOGLE_API_KEY=[for EOL TraitBank integration]
```

**Famous AI - You don't need these! Backend already has them.**

---

## 🎨 **HOW TO INTEGRATE YOUR FRONTEND**

### **Option 1: Use Existing Templates (Recommended)**

The backend serves HTML templates that you can style:

**Files to enhance:**
```
bloombuilder_standalone/templates/bloombuilder/
├── index.html              # Species selector
├── gallery_selector.html   # Multi-stage gallery
└── workbench.html         # Main workbench
```

**What to do:**
1. Add your CSS to `static/css/bloombuilder.css`
2. Add your JavaScript to `static/js/bloombuilder.js`
3. Keep existing API calls intact
4. Just make it beautiful!

### **Option 2: Build Separate Frontend**

If you want to build independently:

**Your frontend makes HTTP requests:**
```javascript
// Example: Get species data
fetch('https://[backend-domain]/bloombuilder/api/species/1')
  .then(res => res.json())
  .then(data => {
    console.log(data.images); // All images with metadata
    console.log(data.traits); // Available trait toggles
  });

// Example: Save creation
const canvas = document.getElementById('canvas');
const imageData = canvas.toDataURL('image/png');

fetch('https://[backend-domain]/bloombuilder/api/save-creation', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    species_id: 1,
    creator_name: 'Jane Doe',
    image_data: imageData,
    style: 'watercolor',
    canvas_data: {}
  })
})
.then(res => res.json())
.then(result => {
  console.log('Saved!', result.filename);
});
```

---

## 📊 **DATABASE SCHEMA REFERENCE**

### **Key Tables You'll Query:**

#### **bloombuilder_species**
```sql
id                  INTEGER PRIMARY KEY
genus               VARCHAR (e.g., "Cypripedium")
species             VARCHAR (e.g., "acaule")
common_name         VARCHAR (e.g., "Pink Lady's Slipper")
naocc_template_url  VARCHAR (link to Orchid-Gami)
```

#### **orchid_images**
```sql
id                INTEGER PRIMARY KEY
species_id        INTEGER REFERENCES orchid_taxonomy
image_url         VARCHAR
image_type        VARCHAR ('herbarium', 'plate', 'photo')
collected_date    DATE
locality          VARCHAR
collector_name    VARCHAR
source_db         VARCHAR ('Tropicos', 'GBIF', 'EOL')
```

#### **orchid_traits**
```sql
id                    INTEGER PRIMARY KEY
species_id            INTEGER
trait_category        VARCHAR ('spur_length', 'color', 'pollinator')
trait_value           VARCHAR ('long', 'short', etc.)
trait_description     TEXT
image_url             VARCHAR (shows this phenotype)
```

---

## 🚀 **QUICK START FOR FAMOUS AI**

### **Step 1: Test Backend is Live**
```bash
curl https://[backend-domain]/bloombuilder/api/species/1
```

You should get JSON with species data.

### **Step 2: View Existing UI**
```
https://[backend-domain]/bloombuilder/
```

This shows the working (but unstyled) interface.

### **Step 3: Choose Integration Method**

**Method A (Easier):** Style existing templates
- Edit HTML in `templates/bloombuilder/`
- Add CSS/JS to `static/`
- Keep API calls intact

**Method B (More Control):** Build separate frontend
- Use any framework (React, Vue, vanilla JS)
- Make fetch calls to backend APIs
- Handle routing yourself

### **Step 4: Make It Beautiful!**

You handle:
- Widget wrapper design
- Color scheme and branding
- Animations and transitions
- Responsive layouts
- Logo integration

Backend handles:
- All data fetching
- Image storage
- Database operations
- Trait toggle logic
- EOL integration

---

## 🔗 **BACKEND ENDPOINTS SUMMARY**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/bloombuilder/` | GET | Species selector |
| `/bloombuilder/api/species/{id}` | GET | Get species data |
| `/bloombuilder/gallery/{id}` | GET | Gallery page |
| `/bloombuilder/api/images/{id}` | GET | Get all images |
| `/bloombuilder/workbench/{id}` | GET | Workbench page |
| `/bloombuilder/api/traits/{id}` | GET | Get traits |
| `/bloombuilder/api/traits/toggle` | POST | Toggle trait |
| `/bloombuilder/api/save-creation` | POST | Save user creation |
| `/bloombuilder/api/glossary/search` | GET | Search terms |

---

## 📞 **NEED HELP?**

### **Common Questions:**

**Q: Do I need database credentials?**
A: No! Backend handles all database operations via API.

**Q: Do I need API keys?**
A: No! Backend already has them configured.

**Q: Can I see the backend code?**
A: Yes! Check `bloombuilder_standalone/` directory for reference.

**Q: How do I test locally?**
A: Backend runs on `http://localhost:5000` - just make fetch calls.

**Q: What about CORS?**
A: Backend allows cross-origin requests (already configured).

---

## ✅ **INTEGRATION CHECKLIST**

Before you start:
- [ ] Confirm backend is running (test API endpoint)
- [ ] Review existing templates to understand flow
- [ ] Decide: style templates OR build separate frontend
- [ ] Plan widget wrapper design
- [ ] Test image upload/download flow

While building:
- [ ] Make API calls to real endpoints (no mocks!)
- [ ] Test trait toggle crossfade animations
- [ ] Verify image metadata displays correctly
- [ ] Test save flow (canvas → base64 → backend)
- [ ] Check acknowledgment modal shows contributors

Before delivery:
- [ ] Test on mobile/tablet (responsive)
- [ ] Verify all 6 export styles work
- [ ] Check glossary search integration
- [ ] Test complete user journey (select → gallery → workbench → save)
- [ ] Confirm downloads work

---

## 🎯 **BOTTOM LINE**

**Famous AI, you do NOT need to:**
- Set up a database
- Write backend code
- Configure environment variables
- Manage file storage
- Handle authentication

**You ONLY need to:**
- Design beautiful UI/UX
- Make fetch calls to existing APIs
- Create widget wrapper
- Style the templates
- Make it inspiring!

**The backend is DONE. Just plug in and make it beautiful!** 🌸

---

**Any questions? Check the code in `bloombuilder_standalone/` or test the endpoints!**
