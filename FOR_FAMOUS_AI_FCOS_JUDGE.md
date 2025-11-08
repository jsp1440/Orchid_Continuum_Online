# FAMOUS AI PROMPT: FCOS Orchid Judge App

**Purpose:** Complete the FCOS Orchid Judge web app for orchid show judging practice

---

## WHAT WE ALREADY HAVE

### Existing Files (Copy from Orchid Continuum repo):
- ✅ `templates/fcos_judge_index.html` (362 lines - COMPLETE UI)
- ✅ `static/js/fcos-judge.js` (23 KB - core functionality)
- ✅ `static/css/fcos-judge.css` (7 KB - styling)
- ✅ `routes_fcos_judge.py` (Flask routes)
- ✅ `static/manifest.json` (PWA config)

### What Works:
- Photo capture interface (plant + tag)
- OCR for tag reading
- AI flower analysis
- Symmetry scoring system
- Certificate generation
- History/storage (last 10 entries)
- Dark mode toggle
- Accessibility features

---

## WHAT NEEDS TO BE COMPLETED

### Backend Integration:
1. **OpenAI Vision API** - for flower analysis
   - Analyze flower morphology
   - Score based on AOS judging criteria
   - Generate educational feedback

2. **OCR Integration** - for tag reading
   - Extract species name from tag photo
   - Parse registration numbers
   - Identify hybrid names

3. **Scoring System** - mathematical calculations
   - Flower symmetry (bilateral/radial)
   - Color intensity
   - Texture quality
   - Size measurements
   - Overall score (0-100)

### Features to Add:
1. **Judging Standards Database**
   - AOS (American Orchid Society) criteria
   - Educational scoring guides
   - Reference photos

2. **Certificate System**
   - Generate practice certificates
   - Download as PDF/image
   - Share functionality

3. **Comparison Mode**
   - Compare 2-3 flowers side-by-side
   - Highlight differences
   - Educational annotations

---

## FAMOUS AI BUILD INSTRUCTIONS

### Step 1: Copy Existing Code
Copy these files from Orchid Continuum repo:
```
templates/fcos_judge_index.html → your project
static/js/fcos-judge.js → your project
static/css/fcos-judge.css → your project
routes_fcos_judge.py → your project
```

### Step 2: Add OpenAI Vision Integration

**File: `routes_fcos_judge.py`**

Add this endpoint:
```python
@app.route('/api/analyze-flower', methods=['POST'])
def analyze_flower():
    """Analyze flower using OpenAI Vision API"""
    import openai
    import base64
    
    # Get image from request
    image_data = request.json.get('image')
    
    # Call OpenAI Vision
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this orchid flower for judging. Score it on: symmetry (0-25), color intensity (0-25), texture quality (0-25), size/presence (0-25). Provide educational feedback for each category. Format as JSON."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                }
            ]
        }]
    )
    
    return jsonify(response.choices[0].message.content)
```

### Step 3: Add OCR for Tag Reading

**File: `routes_fcos_judge.py`**

Add this endpoint:
```python
@app.route('/api/read-tag', methods=['POST'])
def read_tag():
    """Extract text from tag photo using Tesseract"""
    import pytesseract
    from PIL import Image
    import io
    import base64
    
    # Decode image
    image_data = request.json.get('image')
    image_bytes = base64.b64decode(image_data.split(',')[1])
    image = Image.open(io.BytesIO(image_bytes))
    
    # Run OCR
    text = pytesseract.image_to_string(image)
    
    # Parse species name (basic regex)
    import re
    species_pattern = r'([A-Z][a-z]+)\s+([a-z]+)'
    matches = re.findall(species_pattern, text)
    
    return jsonify({
        'raw_text': text,
        'species': matches[0] if matches else None
    })
```

### Step 4: Add Certificate Generation

**File: `routes_fcos_judge.py`**

Add this endpoint:
```python
@app.route('/api/generate-certificate', methods=['POST'])
def generate_certificate():
    """Generate practice judging certificate"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import io
    import base64
    
    data = request.json
    
    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, "FCOS Orchid Judge")
    c.drawCentredString(300, 720, "Practice Certificate")
    
    # Details
    c.setFont("Helvetica", 14)
    c.drawString(100, 650, f"Species: {data['species']}")
    c.drawString(100, 620, f"Score: {data['score']}/100")
    c.drawString(100, 590, f"Date: {data['date']}")
    
    # Scores breakdown
    c.drawString(100, 540, f"Symmetry: {data['symmetry']}/25")
    c.drawString(100, 520, f"Color: {data['color']}/25")
    c.drawString(100, 500, f"Texture: {data['texture']}/25")
    c.drawString(100, 480, f"Size: {data['size']}/25")
    
    c.showPage()
    c.save()
    
    # Return as base64
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return jsonify({
        'pdf': base64.b64encode(pdf_bytes).decode()
    })
```

### Step 5: Add Judging Standards Database

**File: `judging_standards.json`**

Create this JSON file:
```json
{
  "AOS": {
    "categories": [
      {
        "name": "Form",
        "weight": 25,
        "criteria": ["Symmetry", "Balance", "Proportion"]
      },
      {
        "name": "Color",
        "weight": 25,
        "criteria": ["Intensity", "Clarity", "Uniformity"]
      },
      {
        "name": "Texture",
        "weight": 25,
        "criteria": ["Substance", "Finish", "Quality"]
      },
      {
        "name": "Size",
        "weight": 25,
        "criteria": ["Flower size", "Stem length", "Overall presence"]
      }
    ]
  }
}
```

---

## TESTING INSTRUCTIONS

### Test 1: Photo Capture
1. Open app
2. Click "Start New Entry"
3. Take/upload plant photo
4. Take/upload tag photo
5. Verify both photos appear

### Test 2: OCR Tag Reading
1. Upload tag photo with text "Phalaenopsis amabilis"
2. Click "Read Tag"
3. Verify species name extracted correctly

### Test 3: AI Flower Analysis
1. Upload flower photo
2. Click "Analyze Flower"
3. Verify AI returns JSON with scores
4. Check scores appear in UI (0-25 each category)

### Test 4: Certificate Generation
1. Complete judging workflow
2. Click "Generate Certificate"
3. Verify PDF downloads
4. Check all details appear correctly

### Test 5: History/Storage
1. Judge 3 different flowers
2. Navigate to "View My Last 10"
3. Verify all 3 entries appear
4. Click entry to view details

---

## DEPLOYMENT CHECKLIST

- [ ] OpenAI API key configured
- [ ] Tesseract OCR installed
- [ ] ReportLab library installed (for PDFs)
- [ ] Static files served correctly
- [ ] PWA manifest.json configured
- [ ] HTTPS enabled (required for camera access)
- [ ] Test on mobile devices
- [ ] Test on desktop browsers

---

## DEPENDENCIES TO INSTALL

```bash
pip install openai pytesseract pillow reportlab flask
```

---

## USER GUIDE

**What is FCOS Orchid Judge?**
Educational tool for practicing orchid show judging. NOT official - just for learning!

**How to use:**
1. Take 2 photos (plant + tag)
2. AI analyzes flower morphology
3. Get educational scores (0-100)
4. Download practice certificate
5. Compare multiple flowers

**Who is it for?**
- FCOS members preparing for shows
- New judges learning criteria
- Students studying orchid morphology
- Anyone curious about judging standards

---

## FAMOUS AI: WHAT TO BUILD

1. **Complete the backend routes** (OpenAI, OCR, certificates)
2. **Add judging standards database** (JSON file)
3. **Test all features** (photo capture → analysis → certificate)
4. **Deploy as standalone app** OR embed in Orchid Continuum
5. **Make it mobile-friendly** (PWA, camera access)

---

**Estimated Time:** 3-4 hours for Famous AI to complete

**Priority:** Medium (nice-to-have educational tool)

**Status:** 70% complete - just needs backend integration!
