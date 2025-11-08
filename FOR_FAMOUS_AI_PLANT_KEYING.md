# FAMOUS AI PROMPT: Plant Keying App (Dichotomous Key)

**Purpose:** Build an interactive dichotomous key system for identifying orchids step-by-step

---

## WHAT IS A DICHOTOMOUS KEY?

A **dichotomous key** is a tool that identifies organisms through a series of yes/no questions:

**Example:**
```
1a. Flower has a lip (labellum) → Go to 2
1b. Flower does not have a lip → Not an orchid

2a. Growth pattern is monopodial (upward) → Go to 3
2b. Growth pattern is sympodial (horizontal) → Go to 4

3a. Flowers have long spur → Angraecum
3b. Flowers have no spur → Phalaenopsis

4a. Pseudobulbs present → Go to 5
4b. No pseudobulbs → Cypripedium

...and so on
```

---

## ARCHITECT'S VISION

**From Architect feedback:** "Create an interactive tool where users can identify orchids by answering visual questions step-by-step, using real images from your database."

**Key features:**
1. Start with broad questions (flower color, growth type)
2. Narrow down with specific traits (lip shape, spur length)
3. Show reference images at each step
4. End with species identification + confidence level
5. Educational explanations for each choice

---

## BUILD SPECIFICATIONS

### Technology Stack:
- **Frontend:** HTML/CSS/JS (vanilla or React)
- **Backend:** Flask (Python)
- **Database:** PostgreSQL (35,320 species, 11,717 images)
- **AI Enhancement:** Optional OpenAI for image matching

### Core Features:

#### 1. Question Tree System
**File: `keying_tree.json`**

```json
{
  "root": {
    "id": "q1",
    "question": "What is the growth pattern?",
    "options": [
      {
        "choice": "Monopodial (upward, single stem)",
        "image": "/static/images/monopodial_example.jpg",
        "next": "q2"
      },
      {
        "choice": "Sympodial (horizontal, multiple growths)",
        "image": "/static/images/sympodial_example.jpg",
        "next": "q3"
      }
    ]
  },
  "q2": {
    "id": "q2",
    "question": "Does the flower have a spur?",
    "options": [
      {
        "choice": "Yes, long spur (> 5cm)",
        "image": "/static/images/spur_long.jpg",
        "result": "Angraecum"
      },
      {
        "choice": "No spur",
        "image": "/static/images/no_spur.jpg",
        "next": "q4"
      }
    ]
  },
  "q3": {
    "id": "q3",
    "question": "Are pseudobulbs present?",
    "options": [
      {
        "choice": "Yes, visible pseudobulbs",
        "image": "/static/images/pseudobulbs.jpg",
        "next": "q5"
      },
      {
        "choice": "No pseudobulbs",
        "image": "/static/images/no_pseudobulbs.jpg",
        "result": "Cypripedium"
      }
    ]
  }
}
```

#### 2. Frontend Interface

**File: `templates/plant_keying.html`**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Orchid Keying Tool</title>
    <style>
        .key-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .question-card {
            background: #f9f9f9;
            border-radius: 10px;
            padding: 30px;
            margin: 20px 0;
        }
        .option {
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
        }
        .option:hover {
            background: #e8f4f8;
            border-color: #007bff;
        }
        .option-image {
            width: 150px;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
            margin-right: 20px;
        }
        .breadcrumb {
            margin-bottom: 20px;
            color: #666;
        }
        .result-card {
            background: #d4edda;
            border: 2px solid #28a745;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="key-container">
        <h1>Interactive Orchid Key</h1>
        
        <!-- Breadcrumb trail -->
        <div class="breadcrumb" id="breadcrumb">
            Start
        </div>
        
        <!-- Question card -->
        <div class="question-card" id="question-card">
            <h2 id="question-text">Loading...</h2>
            <div id="options-container"></div>
        </div>
        
        <!-- Result card (hidden initially) -->
        <div class="result-card" id="result-card" style="display: none;">
            <h2>Identification Result</h2>
            <h1 id="result-species"></h1>
            <img id="result-image" style="max-width: 400px; margin: 20px 0;">
            <p id="result-confidence"></p>
            <button onclick="restart()">Start Over</button>
        </div>
    </div>
    
    <script src="/static/js/plant-keying.js"></script>
</body>
</html>
```

#### 3. Frontend Logic

**File: `static/js/plant-keying.js`**

```javascript
let keyTree = {};
let currentQuestion = 'root';
let breadcrumbTrail = [];

// Load keying tree
async function loadKeyTree() {
    const response = await fetch('/api/keying-tree');
    keyTree = await response.json();
    displayQuestion(currentQuestion);
}

// Display current question
function displayQuestion(questionId) {
    const question = keyTree[questionId];
    document.getElementById('question-text').textContent = question.question;
    
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((option, index) => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';
        optionDiv.innerHTML = `
            <img src="${option.image}" class="option-image">
            <div>
                <strong>${option.choice}</strong>
                <p style="color: #666;">${option.description || ''}</p>
            </div>
        `;
        optionDiv.onclick = () => selectOption(option);
        optionsContainer.appendChild(optionDiv);
    });
}

// Handle option selection
function selectOption(option) {
    breadcrumbTrail.push(option.choice);
    updateBreadcrumb();
    
    if (option.result) {
        // Reached a result!
        showResult(option.result);
    } else {
        // Continue to next question
        currentQuestion = option.next;
        displayQuestion(currentQuestion);
    }
}

// Show final result
function showResult(species) {
    document.getElementById('question-card').style.display = 'none';
    document.getElementById('result-card').style.display = 'block';
    
    // Fetch species info from database
    fetch(`/api/species/${species}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('result-species').textContent = data.scientific_name;
            document.getElementById('result-image').src = data.image_url;
            document.getElementById('result-confidence').textContent = 
                `Confidence: ${data.confidence}% (based on your answers)`;
        });
}

// Restart key
function restart() {
    currentQuestion = 'root';
    breadcrumbTrail = [];
    updateBreadcrumb();
    document.getElementById('question-card').style.display = 'block';
    document.getElementById('result-card').style.display = 'none';
    displayQuestion(currentQuestion);
}

// Update breadcrumb trail
function updateBreadcrumb() {
    document.getElementById('breadcrumb').textContent = 
        'Start → ' + breadcrumbTrail.join(' → ');
}

// Initialize
loadKeyTree();
```

#### 4. Backend Routes

**File: `routes_plant_keying.py`**

```python
from flask import Blueprint, jsonify, render_template
from app import db
from models import OrchidTaxonomy, OrchidImage
import json

keying_bp = Blueprint('keying', __name__)

@keying_bp.route('/plant-keying')
def plant_keying():
    """Render plant keying interface"""
    return render_template('plant_keying.html')

@keying_bp.route('/api/keying-tree')
def get_keying_tree():
    """Return the dichotomous key tree"""
    with open('keying_tree.json') as f:
        tree = json.load(f)
    return jsonify(tree)

@keying_bp.route('/api/species/<genus>')
def get_species_info(genus):
    """Get species info for final result"""
    # Query database for species
    species = OrchidTaxonomy.query.filter_by(genus=genus).first()
    image = OrchidImage.query.filter_by(genus=genus).first()
    
    return jsonify({
        'scientific_name': species.scientific_name if species else genus,
        'image_url': image.image_url if image else '/static/default-orchid.jpg',
        'confidence': 85  # Calculate based on number of questions answered
    })

# Register blueprint in app.py:
# from routes_plant_keying import keying_bp
# app.register_blueprint(keying_bp)
```

---

## KEYING TREE STRUCTURE (Simplified)

**For Famous AI to build:**

Create a JSON tree with ~20-30 questions covering:

**Level 1: Growth Pattern**
- Monopodial vs Sympodial

**Level 2: Flower Features**
- Lip shape (pouch, frilly, simple)
- Spur present (yes/no)
- Column structure

**Level 3: Vegetative Features**
- Pseudobulbs (yes/no)
- Leaf type (plicate, terete, flat)
- Aerial roots (yes/no)

**Level 4: Flower Size/Color**
- Large (> 10cm) vs Small (< 5cm)
- Color groups (purple, white, yellow, etc.)

**Level 5: Specific Traits**
- Fragrance (yes/no)
- Bloom season
- Native region

**Results:** ~50-100 common orchid genera

---

## ENHANCEMENT: AI-ASSISTED KEYING

**Optional feature:** Use OpenAI Vision to assist

```python
@keying_bp.route('/api/ai-identify', methods=['POST'])
def ai_identify():
    """Use AI to suggest key path based on user photo"""
    import openai
    import base64
    
    image_data = request.json.get('image')
    
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this orchid. Is it monopodial or sympodial? Does it have pseudobulbs? What's the lip shape? Answer as JSON."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        }]
    )
    
    # Parse AI response and suggest key path
    return jsonify(response.choices[0].message.content)
```

---

## TESTING INSTRUCTIONS

1. **Load keying tree** - verify JSON loads correctly
2. **Navigate questions** - click through 5-10 questions
3. **Check images** - ensure reference images appear
4. **Reach result** - complete key to species identification
5. **Restart** - verify breadcrumb resets

---

## FAMOUS AI BUILD CHECKLIST

- [ ] Create `keying_tree.json` with 20-30 questions
- [ ] Build frontend interface (`plant_keying.html`)
- [ ] Add JavaScript logic (`plant-keying.js`)
- [ ] Create Flask routes (`routes_plant_keying.py`)
- [ ] Pull reference images from Orchid Continuum database
- [ ] Test full workflow (question → question → result)
- [ ] Add educational descriptions for each choice
- [ ] Optional: Add AI-assisted identification

---

## ESTIMATED TIME

**Famous AI:** 4-6 hours to build complete system

**Priority:** Medium (educational tool for FCOS members)

---

## USER GUIDE

**What is Plant Keying?**
Step-by-step orchid identification using visual questions

**How to use:**
1. Start with broad questions (growth type)
2. Answer each question by selecting image that matches your plant
3. Progress through narrowing questions
4. Reach species identification with confidence score
5. Learn orchid traits along the way!

**Who is it for?**
- Beginners learning to identify orchids
- FCOS members at shows
- Students studying taxonomy
- Anyone with an unknown orchid

---

**Ready for Famous AI to build!** 🚀
