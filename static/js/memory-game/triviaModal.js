// Orchid Memory Match - Trivia Modal System
// Shows orchid facts for 5 seconds after a match

class OrchidTriviaModal {
  constructor() {
    this.modal = null;
    this.isShowing = false;
    this.init();
  }

  init() {
    this.createModalHTML();
  }

  createModalHTML() {
    // Create trivia modal HTML
    const modalHTML = `
      <div id="triviaModal" class="modal fade" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content bg-dark text-light border-warning">
            <div class="modal-header border-warning">
              <h5 class="modal-title text-warning">🌸 Orchid Discovery!</h5>
            </div>
            <div class="modal-body text-center">
              <img id="triviaImage" src="" alt="Orchid" class="img-fluid rounded mb-3" style="max-height: 200px;">
              <h4 id="triviaName" class="text-warning mb-3"></h4>
              <div id="triviaFacts" class="text-start"></div>
            </div>
            <div class="modal-footer border-warning justify-content-center">
              <small class="text-muted" id="triviaTimer">Closing in 5 seconds...</small>
            </div>
          </div>
        </div>
      </div>
    `;

    // Append to body if not exists
    if (!document.getElementById('triviaModal')) {
      document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    this.modal = new bootstrap.Modal(document.getElementById('triviaModal'));
  }

  async show(orchidId) {
    if (this.isShowing) return;
    
    this.isShowing = true;

    try {
      // Fetch trivia data
      const response = await fetch(`/games/api/orchid-trivia/${orchidId}`);
      const data = await response.json();

      if (data.error) {
        console.error('Trivia error:', data.error);
        this.isShowing = false;
        return;
      }

      // Update modal content
      document.getElementById('triviaImage').src = data.image_url;
      document.getElementById('triviaName').textContent = data.name;

      const factsContainer = document.getElementById('triviaFacts');
      factsContainer.innerHTML = '';
      
      data.facts.forEach(fact => {
        const factEl = document.createElement('p');
        factEl.className = 'mb-2';
        factEl.innerHTML = `<i data-feather="check-circle" class="text-success me-2"></i>${fact}`;
        factsContainer.appendChild(factEl);
      });

      // Re-render feather icons
      if (typeof feather !== 'undefined') {
        feather.replace();
      }

      // Show modal
      this.modal.show();

      // Auto-close after 5 seconds with countdown
      let countdown = 5;
      const timerEl = document.getElementById('triviaTimer');
      
      const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          timerEl.textContent = `Closing in ${countdown} seconds...`;
        } else {
          timerEl.textContent = 'Closing...';
        }
      }, 1000);

      setTimeout(() => {
        clearInterval(countdownInterval);
        this.modal.hide();
        this.isShowing = false;
      }, 5000);

    } catch (error) {
      console.error('Error showing trivia:', error);
      this.isShowing = false;
    }
  }
}

// Initialize global trivia modal
window.OrchidTriviaModal = new OrchidTriviaModal();
