// Orchid Memory Match - Game Configuration
// Global config accessible via window.MEMORY_GAME_CONFIG

window.MEMORY_GAME_CONFIG = {
  // Image Loading
  IMAGE_LOAD_TIMEOUT_MS: 4000,
  FALLBACK_IMAGE: '/static/images/orchid-fallback.jpg',
  FAILURE_THRESHOLD: 0.1, // Show banner if >10% images fail
  
  // Gameplay
  HINTS_PER_GAME: 3,
  PRACTICE_MODE_DURATION_MS: 15000, // 15 seconds preview
  
  // Rebus Puzzle
  REBUS_GUESS_UNLOCK_PERCENT: 0.5,
  REBUS_BONUS_POINTS: 10,
  GUESS_COOLDOWN_MS: 2000,
  
  // Chat & Multiplayer
  CHAT_RATE_LIMIT_MS: 1000,
  AI_GUESS_DELAY_MIN_MS: 2000,
  AI_GUESS_DELAY_MAX_MS: 4000,
  
  // UI Customization
  TILE_BACK_LOGO: null, // Set dynamically from template data-attribute
  SHOW_TILE_NUMBERS: true, // Toggleable in settings
  TRIVIA_AUTO_DISMISS_MS: 5000, // Auto-close trivia cards after 5s
  
  // Scoring
  MATCH_POINTS: 100,
  TIME_BONUS_PER_SECOND: 5,
  HINT_PENALTY: 20,
  
  // Storage
  SETTINGS_KEY: 'orchid-memory-settings-v4',
  LEADERBOARD_KEY: 'orchid-memory-leaderboard-v4',
  
  // Initialize logo from template
  init() {
    const logoEl = document.querySelector('[data-fcos-logo]');
    if (logoEl) {
      this.TILE_BACK_LOGO = logoEl.dataset.fcosLogo;
    }
    if (!this.TILE_BACK_LOGO) {
      this.TILE_BACK_LOGO = '/static/images/fcos-logo.png';
    }
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.MEMORY_GAME_CONFIG.init();
  });
} else {
  window.MEMORY_GAME_CONFIG.init();
}
