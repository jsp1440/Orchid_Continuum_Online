// Orchid Memory Match - Core Game Logic
// Extracted and enhanced from inline script

class OrchidMemoryMatchCore {
  constructor() {
    this.CONFIG = window.MEMORY_GAME_CONFIG;
    this.cards = [];
    this.flippedCards = [];
    this.matchedPairs = 0;
    this.moves = 0;
    this.isProcessing = false;
    this.showTileNumbers = this.CONFIG.SHOW_TILE_NUMBERS;
    
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.loadCards();
  }
  
  bindEvents() {
    document.getElementById('playAgainBtn')?.addEventListener('click', () => this.restart());
  }
  
  async loadCards() {
    const loadingState = document.getElementById('loadingState');
    const gameGrid = document.getElementById('gameGrid');
    
    if (loadingState) loadingState.style.display = 'block';
    if (gameGrid) gameGrid.style.display = 'none';
    
    try {
      const response = await fetch('/games/api/memory-cards');
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Validate images with preflight system
      if (window.OrchidImagePreflight) {
        this.cards = await window.OrchidImagePreflight.validateCards(data.cards);
        const stats = window.OrchidImagePreflight.getStats();
        console.log(`Image validation: ${stats.successful}/${stats.total} loaded successfully`);
      } else {
        this.cards = data.cards;
      }
      
      this.createGameGrid();
      
      if (loadingState) loadingState.style.display = 'none';
      if (gameGrid) gameGrid.style.display = 'flex';
      
    } catch (error) {
      console.error('Error loading cards:', error);
      alert('Error loading memory cards. Please try again.');
    }
  }
  
  createGameGrid() {
    const grid = document.getElementById('gameGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    this.cards.forEach((card, index) => {
      const col = document.createElement('div');
      col.className = 'col-3 col-md-3 col-lg-3';
      
      const cardElement = document.createElement('div');
      cardElement.className = 'memory-card';
      cardElement.dataset.cardId = card.id;
      cardElement.dataset.pairId = card.pair_id;
      cardElement.dataset.tileNumber = index + 1;
      
      // Create card HTML with FCOS logo back
      const logoUrl = this.CONFIG.TILE_BACK_LOGO || '/static/images/fcos-logo.svg';
      const tileNumber = index + 1;
      const showNumber = this.showTileNumbers;
      
      cardElement.innerHTML = `
        <div class="card-inner">
          <div class="card-front">
            <div class="tile-back-content">
              <img src="${logoUrl}" alt="FCOS" class="fcos-logo">
              ${showNumber ? `<span class="tile-number">${tileNumber}</span>` : ''}
            </div>
          </div>
          <div class="card-back">
            <img src="${card.image_url}" alt="${card.name}" class="card-image" 
                 onerror="this.src='${this.CONFIG.FALLBACK_IMAGE}'">
            <div class="card-name">${card.name}</div>
          </div>
        </div>
      `;
      
      cardElement.addEventListener('click', () => this.flipCard(cardElement));
      
      col.appendChild(cardElement);
      grid.appendChild(col);
    });
    
    // Initialize feather icons if available
    if (typeof feather !== 'undefined') {
      setTimeout(() => feather.replace(), 100);
    }
  }
  
  flipCard(cardElement) {
    if (this.isProcessing || 
        cardElement.classList.contains('flipped') || 
        cardElement.classList.contains('matched')) {
      return;
    }
    
    cardElement.classList.add('flipped');
    this.flippedCards.push(cardElement);
    
    if (this.flippedCards.length === 2) {
      this.checkMatch();
    }
  }
  
  checkMatch() {
    this.isProcessing = true;
    this.moves++;
    const movesEl = document.getElementById('moves');
    if (movesEl) movesEl.textContent = this.moves;
    
    const [card1, card2] = this.flippedCards;
    const pair1 = card1.dataset.pairId;
    const pair2 = card2.dataset.pairId;
    
    setTimeout(() => {
      if (pair1 === pair2) {
        // Match found!
        card1.classList.add('matched');
        card2.classList.add('matched');
        this.matchedPairs++;
        
        const matchesEl = document.getElementById('matches');
        if (matchesEl) matchesEl.textContent = this.matchedPairs;
        
        // Get orchid ID from card data
        const orchidId = this.cards.find(c => c.pair_id == pair1)?.orchid_id;
        
        // Show trivia popup if trivia modal is available
        if (window.OrchidTriviaModal && orchidId) {
          window.OrchidTriviaModal.show(orchidId);
        }
        
        // Make matched cards disappear after trivia (fade to 0)
        setTimeout(() => {
          card1.style.opacity = '0';
          card2.style.opacity = '0';
          
          // Reveal rebus puzzle tiles
          if (window.RebusSystem) {
            const tile1 = parseInt(card1.dataset.tileNumber);
            const tile2 = parseInt(card2.dataset.tileNumber);
            window.RebusSystem.revealTile(tile1);
            window.RebusSystem.revealTile(tile2);
            window.RebusSystem.show();
          }
        }, 5500); // After 5 second trivia display
        
        if (this.matchedPairs === 8) {
          setTimeout(() => this.gameComplete(), 6000);
        }
      } else {
        // No match, flip back
        card1.classList.remove('flipped');
        card2.classList.remove('flipped');
      }
      
      this.flippedCards = [];
      this.isProcessing = false;
    }, 1000);
  }
  
  gameComplete() {
    setTimeout(() => {
      const finalMovesEl = document.getElementById('finalMoves');
      const gameCompleteEl = document.getElementById('gameComplete');
      const gameGridEl = document.getElementById('gameGrid');
      
      if (finalMovesEl) finalMovesEl.textContent = this.moves;
      if (gameCompleteEl) gameCompleteEl.style.display = 'block';
      if (gameGridEl) gameGridEl.style.display = 'none';
      
      // Calculate and submit score (lower moves = higher score)
      const maxScore = 100;
      const score = Math.max(0, maxScore - (this.moves - 16) * 2); // 16 is minimum moves
      this.submitScore(score);
      
      // Re-initialize feather icons
      if (typeof feather !== 'undefined') {
        feather.replace();
      }
    }, 1000);
  }
  
  async submitScore(score) {
    try {
      await fetch('/games/api/submit-score', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          game_type: 'memory_match',
          score: score
        })
      });
    } catch (error) {
      console.error('Error submitting score:', error);
    }
  }
  
  restart() {
    this.flippedCards = [];
    this.matchedPairs = 0;
    this.moves = 0;
    this.isProcessing = false;
    
    const movesEl = document.getElementById('moves');
    const matchesEl = document.getElementById('matches');
    const gameCompleteEl = document.getElementById('gameComplete');
    
    if (movesEl) movesEl.textContent = '0';
    if (matchesEl) matchesEl.textContent = '0';
    if (gameCompleteEl) gameCompleteEl.style.display = 'none';
    
    // Reset image validation state
    if (window.OrchidImagePreflight) {
      window.OrchidImagePreflight.reset();
    }
    
    this.loadCards();
  }
  
  toggleTileNumbers(show) {
    this.showTileNumbers = show;
    // Update existing tiles
    document.querySelectorAll('.tile-number').forEach(el => {
      el.style.display = show ? 'block' : 'none';
    });
  }
}

// Initialize game when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof feather !== 'undefined') feather.replace();
    window.orchidMemoryGame = new OrchidMemoryMatchCore();
  });
} else {
  if (typeof feather !== 'undefined') feather.replace();
  window.orchidMemoryGame = new OrchidMemoryMatchCore();
}
