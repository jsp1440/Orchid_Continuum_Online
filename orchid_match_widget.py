"""
🔥 ORCHID MATCH - Tinder-Style Swipe Widget
The most engaging orchid discovery experience ever built
"""

from flask import render_template_string, request, jsonify, session
from app import app, db
from models import OrchidRecord
from sqlalchemy import func, and_, or_
import random

@app.route('/widgets/orchid-match')
def orchid_match_widget():
    """Swipe-based orchid discovery - addictive UX"""
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌸 Orchid Match - Find Your Perfect Orchid</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .match-container {
                max-width: 400px;
                width: 100%;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 32px;
                margin-bottom: 10px;
            }
            
            .stats {
                display: flex;
                justify-content: center;
                gap: 30px;
                color: white;
                margin-bottom: 20px;
            }
            
            .stat {
                text-align: center;
            }
            
            .stat-number {
                font-size: 24px;
                font-weight: bold;
            }
            
            .stat-label {
                font-size: 12px;
                opacity: 0.9;
            }
            
            .card-stack {
                position: relative;
                width: 100%;
                height: 500px;
            }
            
            .orchid-card {
                position: absolute;
                width: 100%;
                height: 100%;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                transition: transform 0.3s ease, opacity 0.3s ease;
                cursor: grab;
                user-select: none;
            }
            
            .orchid-card:active {
                cursor: grabbing;
            }
            
            .card-image {
                width: 100%;
                height: 350px;
                object-fit: cover;
                border-radius: 20px 20px 0 0;
            }
            
            .card-info {
                padding: 20px;
            }
            
            .card-title {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
                color: #2d3748;
            }
            
            .card-subtitle {
                font-size: 16px;
                color: #718096;
                font-style: italic;
                margin-bottom: 15px;
            }
            
            .card-tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .tag {
                padding: 5px 12px;
                background: #e0e0e0;
                border-radius: 15px;
                font-size: 12px;
                color: #555;
            }
            
            .action-buttons {
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-top: 30px;
            }
            
            .action-btn {
                width: 70px;
                height: 70px;
                border-radius: 50%;
                border: none;
                font-size: 32px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .action-btn:hover {
                transform: scale(1.1);
            }
            
            .action-btn:active {
                transform: scale(0.95);
            }
            
            .nope-btn {
                background: #ff6b6b;
                color: white;
                box-shadow: 0 4px 20px rgba(255,107,107,0.4);
            }
            
            .love-btn {
                background: #4ecdc4;
                color: white;
                box-shadow: 0 4px 20px rgba(78,205,196,0.4);
            }
            
            .swipe-indicator {
                position: absolute;
                top: 50px;
                font-size: 80px;
                font-weight: bold;
                opacity: 0;
                transition: opacity 0.2s;
                pointer-events: none;
            }
            
            .nope-indicator {
                left: 50px;
                color: #ff6b6b;
                transform: rotate(-30deg);
            }
            
            .love-indicator {
                right: 50px;
                color: #4ecdc4;
                transform: rotate(30deg);
            }
            
            .no-more {
                text-align: center;
                color: white;
                padding: 40px;
            }
            
            .matches-btn {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                padding: 10px 20px;
                border-radius: 25px;
                color: #667eea;
                font-weight: bold;
                text-decoration: none;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
        </style>
    </head>
    <body>
        <a href="#" class="matches-btn" onclick="showMatches()">❤️ <span id="matchCount">0</span> Matches</a>
        
        <div class="match-container">
            <div class="header">
                <h1>🌸 Orchid Match</h1>
                <p>Swipe to find your perfect orchids</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number" id="swipeCount">0</div>
                    <div class="stat-label">Swipes</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="matchPercentage">0%</div>
                    <div class="stat-label">Match Rate</div>
                </div>
            </div>
            
            <div class="card-stack" id="cardStack">
                <!-- Cards loaded here -->
            </div>
            
            <div class="action-buttons">
                <button class="action-btn nope-btn" onclick="swipe('left')">✕</button>
                <button class="action-btn love-btn" onclick="swipe('right')">❤️</button>
            </div>
        </div>
        
        <script>
        let orchids = [];
        let currentIndex = 0;
        let swipeCount = 0;
        let matchCount = 0;
        let matches = [];
        
        async function loadOrchids() {
            const response = await fetch('/api/orchid-match/cards');
            const data = await response.json();
            orchids = data.orchids;
            renderCard();
        }
        
        function renderCard() {
            const stack = document.getElementById('cardStack');
            
            if (currentIndex >= orchids.length) {
                stack.innerHTML = `
                    <div class="no-more">
                        <h2>🎉 You've seen them all!</h2>
                        <p style="margin: 20px 0;">Check your matches or reload for more</p>
                        <button onclick="location.reload()" style="background: white; color: #667eea; border: none; padding: 12px 30px; border-radius: 25px; font-weight: bold; cursor: pointer;">Start Over</button>
                    </div>
                `;
                return;
            }
            
            const orchid = orchids[currentIndex];
            
            const card = document.createElement('div');
            card.className = 'orchid-card';
            card.innerHTML = `
                <div class="swipe-indicator nope-indicator">NOPE</div>
                <div class="swipe-indicator love-indicator">LOVE</div>
                <img src="${orchid.image}" alt="${orchid.name}" class="card-image">
                <div class="card-info">
                    <div class="card-title">${orchid.name}</div>
                    <div class="card-subtitle">${orchid.scientific_name}</div>
                    <div class="card-tags">
                        ${orchid.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                </div>
            `;
            
            stack.innerHTML = '';
            stack.appendChild(card);
            
            // Add touch/drag handlers
            let startX = 0;
            let currentX = 0;
            
            card.addEventListener('mousedown', (e) => {
                startX = e.clientX;
                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
            
            card.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
                document.addEventListener('touchmove', onTouchMove);
                document.addEventListener('touchend', onTouchEnd);
            });
            
            function onMouseMove(e) {
                currentX = e.clientX - startX;
                updateCardTransform();
            }
            
            function onTouchMove(e) {
                currentX = e.touches[0].clientX - startX;
                updateCardTransform();
            }
            
            function updateCardTransform() {
                const rotate = currentX / 20;
                card.style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;
                
                if (currentX < -50) {
                    card.querySelector('.nope-indicator').style.opacity = '1';
                } else if (currentX > 50) {
                    card.querySelector('.love-indicator').style.opacity = '1';
                } else {
                    card.querySelector('.nope-indicator').style.opacity = '0';
                    card.querySelector('.love-indicator').style.opacity = '0';
                }
            }
            
            function onMouseUp() {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                handleSwipeEnd();
            }
            
            function onTouchEnd() {
                document.removeEventListener('touchmove', onTouchMove);
                document.removeEventListener('touchend', onTouchEnd);
                handleSwipeEnd();
            }
            
            function handleSwipeEnd() {
                if (currentX < -100) {
                    swipe('left');
                } else if (currentX > 100) {
                    swipe('right');
                } else {
                    card.style.transform = '';
                    card.querySelector('.nope-indicator').style.opacity = '0';
                    card.querySelector('.love-indicator').style.opacity = '0';
                }
                currentX = 0;
            }
        }
        
        function swipe(direction) {
            const card = document.querySelector('.orchid-card');
            if (!card) return;
            
            swipeCount++;
            
            if (direction === 'right') {
                matchCount++;
                matches.push(orchids[currentIndex]);
                card.style.transform = 'translateX(500px) rotate(30deg)';
                
                // Save match to backend
                fetch('/api/orchid-match/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({orchid_id: orchids[currentIndex].id})
                });
            } else {
                card.style.transform = 'translateX(-500px) rotate(-30deg)';
            }
            
            card.style.opacity = '0';
            
            setTimeout(() => {
                currentIndex++;
                renderCard();
                updateStats();
            }, 300);
        }
        
        function updateStats() {
            document.getElementById('swipeCount').textContent = swipeCount;
            document.getElementById('matchCount').textContent = matchCount;
            document.getElementById('matchPercentage').textContent = 
                swipeCount > 0 ? Math.round((matchCount / swipeCount) * 100) + '%' : '0%';
        }
        
        function showMatches() {
            if (matchCount === 0) {
                alert('No matches yet! Keep swiping to find orchids you love 💚');
                return;
            }
            
            const matchList = matches.map(o => `• ${o.name}`).join('\\n');
            alert(`Your Matches (${matchCount}):\\n\\n${matchList}\\n\\nVisit /my-matches to see details!`);
        }
        
        loadOrchids();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/api/orchid-match/cards')
def get_match_cards():
    """Get randomized orchid cards for swiping"""
    
    # Get 50 random orchids with images
    orchids = OrchidRecord.query.filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).order_by(func.random()).limit(50).all()
    
    cards = []
    for orchid in orchids:
        tags = []
        if orchid.genus:
            tags.append(orchid.genus)
        if orchid.climate_preference:
            tags.append(orchid.climate_preference)
        if orchid.light_requirements:
            tags.append(orchid.light_requirements)
        
        cards.append({
            'id': orchid.id,
            'name': orchid.display_name or f"{orchid.genus} {orchid.species}",
            'scientific_name': orchid.scientific_name or f"{orchid.genus} {orchid.species}",
            'image': f"https://lh3.googleusercontent.com/d/{orchid.google_drive_id}",
            'tags': tags[:3]  # Max 3 tags
        })
    
    return jsonify({'orchids': cards})

@app.route('/api/orchid-match/save', methods=['POST'])
def save_match():
    """Save user's orchid match"""
    data = request.json
    orchid_id = data.get('orchid_id')
    
    # Store in session for now (could use database later)
    if 'orchid_matches' not in session:
        session['orchid_matches'] = []
    
    if orchid_id not in session['orchid_matches']:
        session['orchid_matches'].append(orchid_id)
    
    return jsonify({'success': True})

@app.route('/my-matches')
def my_matches():
    """View all matched orchids"""
    match_ids = session.get('orchid_matches', [])
    
    if not match_ids:
        return "<h1>No matches yet! Try <a href='/widgets/orchid-match'>Orchid Match</a></h1>"
    
    matches = OrchidRecord.query.filter(OrchidRecord.id.in_(match_ids)).all()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Orchid Matches</title>
        <style>
            body { font-family: sans-serif; padding: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #667eea; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
            .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card img { width: 100%; height: 200px; object-fit: cover; }
            .card-body { padding: 15px; }
            .card-title { font-weight: bold; margin-bottom: 5px; }
            .card-subtitle { color: #666; font-style: italic; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>❤️ Your Orchid Matches ({{ matches|length }})</h1>
            <p>These are the orchids you loved!</p>
            
            <div class="grid">
                {% for orchid in matches %}
                <div class="card">
                    <img src="https://lh3.googleusercontent.com/d/{{ orchid.google_drive_id }}" alt="{{ orchid.display_name }}">
                    <div class="card-body">
                        <div class="card-title">{{ orchid.display_name or orchid.genus + ' ' + orchid.species }}</div>
                        <div class="card-subtitle">{{ orchid.scientific_name or '' }}</div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/widgets/orchid-match" style="background: #667eea; color: white; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: bold;">Find More Matches</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, matches=matches)
