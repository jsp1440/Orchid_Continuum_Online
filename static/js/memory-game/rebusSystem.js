// Orchid Memory Match - Rebus Puzzle System
// Progressive reveal puzzle underneath matched cards

class RebusSystem {
  constructor() {
    this.puzzle = null;
    this.revealedTiles = new Set();
    this.guessTimer = null;
    this.canGuess = false;
    this.init();
  }

  async init() {
    await this.loadPuzzle();
    this.createPuzzleHTML();
  }

  async loadPuzzle() {
    try {
      const response = await fetch('/games/api/rebus-puzzle');
      this.puzzle = await response.json();
    } catch (error) {
      console.error('Error loading rebus puzzle:', error);
      // Fallback puzzle
      this.puzzle = {
        image_url: '/static/images/orchid-fallback.jpg',
        answer: 'ORCHID LOVE',
        hint: 'Passion for orchids'
      };
    }
  }

  createPuzzleHTML() {
    const puzzleHTML = `
      <div id="rebusContainer" class="position-relative" style="display: none;">
        <img id="rebusPuzzle" src="${this.puzzle.image_url}" 
             alt="Rebus Puzzle" 
             class="img-fluid w-100"
             style="opacity: 0; transition: opacity 0.5s;">
        
        <!-- Guess input modal -->
        <div id="guessModal" class="modal fade" tabindex="-1">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-dark text-light border-success">
              <div class="modal-header border-success">
                <h5 class="modal-title text-success">🧩 Guess the Puzzle!</h5>
                <span id="guessTimer" class="badge bg-warning ms-auto">7s</span>
              </div>
              <div class="modal-body">
                <p class="text-muted">Hint: ${this.puzzle.hint}</p>
                <input type="text" id="guessInput" 
                       class="form-control bg-dark text-light border-success" 
                       placeholder="Enter your guess...">
              </div>
              <div class="modal-footer border-success">
                <button type="button" class="btn btn-success" onclick="window.RebusSystem.submitGuess()">
                  Submit Guess
                </button>
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                  Pass
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    const gameContainer = document.getElementById('game-root');
    if (gameContainer && !document.getElementById('rebusContainer')) {
      gameContainer.insertAdjacentHTML('afterbegin', puzzleHTML);
    }
  }

  revealTile(tileNumber) {
    this.revealedTiles.add(tileNumber);
    
    // Calculate reveal percentage
    const totalTiles = 16;
    const revealPercent = (this.revealedTiles.size / totalTiles) * 100;
    
    // Update puzzle opacity
    const puzzleImg = document.getElementById('rebusPuzzle');
    if (puzzleImg) {
      puzzleImg.style.opacity = revealPercent / 100;
    }

    // Check if puzzle is fully revealed
    if (this.revealedTiles.size === totalTiles) {
      this.enableFinalGuess();
    } else {
      // Allow guess after each match (7 seconds)
      this.enableQuickGuess();
    }
  }

  enableQuickGuess() {
    if (!this.canGuess) {
      this.canGuess = true;
      this.showGuessModal(7); // 7 second timer
    }
  }

  enableFinalGuess() {
    this.showGuessModal(10); // 10 second timer for final guess
  }

  showGuessModal(seconds) {
    const modal = new bootstrap.Modal(document.getElementById('guessModal'));
    const timerEl = document.getElementById('guessTimer');
    const inputEl = document.getElementById('guessInput');
    
    inputEl.value = '';
    modal.show();

    let timeLeft = seconds;
    timerEl.textContent = `${timeLeft}s`;

    this.guessTimer = setInterval(() => {
      timeLeft--;
      timerEl.textContent = `${timeLeft}s`;
      
      if (timeLeft <= 0) {
        clearInterval(this.guessTimer);
        modal.hide();
        this.canGuess = false;
      }
    }, 1000);
  }

  submitGuess() {
    const guess = document.getElementById('guessInput').value.trim().toUpperCase();
    const correct = guess === this.puzzle.answer.toUpperCase();

    clearInterval(this.guessTimer);
    const modal = bootstrap.Modal.getInstance(document.getElementById('guessModal'));
    modal.hide();

    if (correct) {
      this.showSuccess();
    } else {
      this.showIncorrect(guess);
    }

    this.canGuess = false;
  }

  showSuccess() {
    const successHTML = `
      <div class="alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">
        <strong>🎉 Correct!</strong> The answer was: ${this.puzzle.answer}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', successHTML);

    // Remove after 3 seconds
    setTimeout(() => {
      const alert = document.querySelector('.alert-success');
      if (alert) alert.remove();
    }, 3000);
  }

  showIncorrect(guess) {
    const incorrectHTML = `
      <div class="alert alert-warning alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">
        <strong>Not quite!</strong> "${guess}" is not the answer. Keep trying!
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', incorrectHTML);

    // Remove after 3 seconds
    setTimeout(() => {
      const alert = document.querySelector('.alert-warning');
      if (alert) alert.remove();
    }, 3000);
  }

  show() {
    const container = document.getElementById('rebusContainer');
    if (container) {
      container.style.display = 'block';
    }
  }
}

// Initialize global rebus system
window.RebusSystem = new RebusSystem();
