from flask import Blueprint, request, jsonify, render_template_string
from app import app, db
from models import OrchidRecord
import os
from datetime import datetime
import secrets

gary_api = Blueprint('gary_api', __name__)

# Generate API key for Gary
GARY_API_KEY = os.environ.get('GARY_API_KEY', 'gary_' + secrets.token_urlsafe(32))

@gary_api.route('/api/gary/submit-orchid', methods=['POST'])
def submit_orchid():
    """
    API endpoint for Gary Yong Gee to submit orchid images
    
    Accepts JSON:
    {
        "api_key": "gary_xxx",
        "scientific_name": "Dendrobium bigibbum",
        "genus": "Dendrobium",
        "species": "bigibbum",
        "image_url": "https://orchids.yonggee.name/images/dendrobium-bigibbum.jpg",
        "location": "Queensland, Australia",
        "notes": "Found in wild, blooming season"
    }
    """
    data = request.json
    
    # Verify API key
    if data.get('api_key') != GARY_API_KEY:
        return jsonify({'error': 'Invalid API key'}), 403
    
    try:
        # Create orchid record
        orchid = OrchidRecord(
            scientific_name=data.get('scientific_name'),
            genus=data.get('genus'),
            species=data.get('species'),
            image_url=data.get('image_url'),
            photographer='Gary Yong Gee',
            image_source='Gary Yong Gee - Australia Wild Orchids',
            native_habitat=data.get('location'),
            cultural_notes=data.get('notes'),
            validation_status='approved',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(orchid)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'orchid_id': orchid.id,
            'message': 'Orchid added successfully to Orchid Continuum database'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@gary_api.route('/api/gary/batch-submit', methods=['POST'])
def batch_submit():
    """Batch submit multiple orchids at once"""
    data = request.json
    
    if data.get('api_key') != GARY_API_KEY:
        return jsonify({'error': 'Invalid API key'}), 403
    
    orchids = data.get('orchids', [])
    added_count = 0
    errors = []
    
    for orchid_data in orchids:
        try:
            orchid = OrchidRecord(
                scientific_name=orchid_data.get('scientific_name'),
                genus=orchid_data.get('genus'),
                species=orchid_data.get('species'),
                image_url=orchid_data.get('image_url'),
                photographer='Gary Yong Gee',
                image_source='Gary Yong Gee - Australia Wild Orchids',
                native_habitat=orchid_data.get('location'),
                cultural_notes=orchid_data.get('notes'),
                validation_status='approved',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(orchid)
            added_count += 1
            
        except Exception as e:
            errors.append(f"{orchid_data.get('scientific_name')}: {str(e)}")
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'added': added_count,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@gary_api.route('/gary-widget-demo')
def widget_demo():
    """Demo widget that Gary can embed on his site"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gary Yong Gee → Orchid Continuum Widget</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .widget { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            input, textarea { 
                width: 100%; 
                padding: 10px; 
                margin: 10px 0; 
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button { 
                background: #4CAF50; 
                color: white; 
                padding: 12px 30px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
            }
            button:hover { background: #45a049; }
            .status { 
                margin-top: 20px; 
                padding: 15px; 
                border-radius: 5px;
                display: none;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="widget">
            <h1>🌸 Share Your Wild Orchid</h1>
            <p>Gary Yong Gee → Orchid Continuum Partnership</p>
            
            <input type="text" id="scientific_name" placeholder="Scientific Name (e.g., Dendrobium bigibbum)" />
            <input type="text" id="genus" placeholder="Genus (e.g., Dendrobium)" />
            <input type="text" id="species" placeholder="Species (e.g., bigibbum)" />
            <input type="text" id="image_url" placeholder="Image URL (full path)" />
            <input type="text" id="location" placeholder="Location (e.g., Queensland, Australia)" />
            <textarea id="notes" rows="3" placeholder="Notes (habitat, season, etc.)"></textarea>
            
            <button onclick="submitOrchid()">Submit to Orchid Continuum</button>
            
            <div id="status" class="status"></div>
        </div>
        
        <script>
        function submitOrchid() {
            const data = {
                api_key: '{{ api_key }}',
                scientific_name: document.getElementById('scientific_name').value,
                genus: document.getElementById('genus').value,
                species: document.getElementById('species').value,
                image_url: document.getElementById('image_url').value,
                location: document.getElementById('location').value,
                notes: document.getElementById('notes').value
            };
            
            fetch('/api/gary/submit-orchid', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                const status = document.getElementById('status');
                status.style.display = 'block';
                
                if (result.success) {
                    status.className = 'status success';
                    status.textContent = '✅ Success! Orchid added to database (ID: ' + result.orchid_id + ')';
                    
                    // Clear form
                    document.getElementById('scientific_name').value = '';
                    document.getElementById('genus').value = '';
                    document.getElementById('species').value = '';
                    document.getElementById('image_url').value = '';
                    document.getElementById('location').value = '';
                    document.getElementById('notes').value = '';
                } else {
                    status.className = 'status error';
                    status.textContent = '❌ Error: ' + result.error;
                }
            })
            .catch(error => {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status error';
                status.textContent = '❌ Error: ' + error;
            });
        }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html, api_key=GARY_API_KEY)

@gary_api.route('/gary-instructions')
def gary_instructions():
    """Simple instructions for Gary"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Instructions for Gary Yong Gee</title>
        <style>
            body { font-family: Arial; padding: 40px; max-width: 800px; margin: 0 auto; }
            h1 { color: #2c5f2d; }
            .box { background: #f0f8f0; padding: 20px; margin: 20px 0; border-radius: 8px; }
            code { background: #e8e8e8; padding: 3px 8px; border-radius: 3px; }
            pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🌺 Gary Yong Gee Partnership Setup</h1>
        
        <h2>Option 1: Use the Widget (Easiest)</h2>
        <div class="box">
            <p><strong>Demo Widget:</strong> <a href="/gary-widget-demo" target="_blank">Click here to test</a></p>
            <p>You can embed this on your website or just use it directly to add orchids one by one.</p>
        </div>
        
        <h2>Option 2: API Integration (For Bulk Upload)</h2>
        <div class="box">
            <p><strong>Your API Key:</strong> <code>{{ api_key }}</code></p>
            <p><strong>Endpoint:</strong> <code>https://workspace.fcospresident.repl.co/api/gary/submit-orchid</code></p>
            
            <h3>Example API Call:</h3>
            <pre>
curl -X POST https://workspace.fcospresident.repl.co/api/gary/submit-orchid \\
  -H "Content-Type: application/json" \\
  -d '{
    "api_key": "{{ api_key }}",
    "scientific_name": "Dendrobium bigibbum",
    "genus": "Dendrobium",
    "species": "bigibbum",
    "image_url": "https://orchids.yonggee.name/images/your-image.jpg",
    "location": "Queensland, Australia",
    "notes": "Wild specimen, photographed in natural habitat"
  }'
            </pre>
        </div>
        
        <h2>Option 3: Batch Upload (Multiple Orchids)</h2>
        <div class="box">
            <p><strong>Endpoint:</strong> <code>/api/gary/batch-submit</code></p>
            <p>Send array of orchids in one request. Perfect for bulk uploads!</p>
            
            <h3>Example:</h3>
            <pre>
{
  "api_key": "{{ api_key }}",
  "orchids": [
    {
      "scientific_name": "Dendrobium bigibbum",
      "genus": "Dendrobium",
      "species": "bigibbum",
      "image_url": "https://orchids.yonggee.name/images/1.jpg",
      "location": "Queensland",
      "notes": "Wild"
    },
    {
      "scientific_name": "Dendrobium kingianum",
      "genus": "Dendrobium", 
      "species": "kingianum",
      "image_url": "https://orchids.yonggee.name/images/2.jpg",
      "location": "NSW",
      "notes": "Growing on rocks"
    }
  ]
}
            </pre>
        </div>
        
        <h2>What Happens Next?</h2>
        <ul>
            <li>✅ Your orchid images are instantly added to Orchid Continuum database</li>
            <li>🤖 AI automatically analyzes each image for traits and features</li>
            <li>🌍 Images appear in our wild orchid gallery</li>
            <li>📊 Data used for biodiversity research and pattern analysis</li>
            <li>📸 Full photo credit given to "Gary Yong Gee"</li>
        </ul>
        
        <p style="margin-top: 40px; color: #666;">
            <strong>Need help?</strong> Email: Fcospresident@gmail.com
        </p>
    </body>
    </html>
    '''
    return render_template_string(html, api_key=GARY_API_KEY)

# Blueprint is registered in app.py - DO NOT register here to avoid duplicate registration error
# app.register_blueprint(gary_api)

if __name__ == "__main__":
    print(f"✅ Gary Partnership API Ready!")
    print(f"📍 Widget Demo: https://workspace.fcospresident.repl.co/gary-widget-demo")
    print(f"📍 Instructions: https://workspace.fcospresident.repl.co/gary-instructions")
    print(f"🔑 API Key: {GARY_API_KEY}")
