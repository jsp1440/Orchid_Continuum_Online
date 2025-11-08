// Image Preflight Validation System
// Validates all orchid images before game starts, replaces failures with fallback

window.OrchidImagePreflight = (function() {
  'use strict';
  
  const CONFIG = window.MEMORY_GAME_CONFIG;
  
  // Track validation results
  const validationResults = {
    total: 0,
    successful: 0,
    failed: 0,
    replacements: [],
    bannerShown: false
  };
  
  /**
   * Preload a single image with timeout
   * @param {string} url - Image URL to load
   * @param {number} timeout - Timeout in ms
   * @returns {Promise<{url: string, success: boolean}>}
   */
  function preloadImage(url, timeout = CONFIG.IMAGE_LOAD_TIMEOUT_MS) {
    return new Promise((resolve) => {
      const img = new Image();
      let timeoutId;
      let resolved = false;
      
      const resolveOnce = (success) => {
        if (resolved) return;
        resolved = true;
        clearTimeout(timeoutId);
        resolve({ url, success });
      };
      
      img.onload = () => resolveOnce(true);
      img.onerror = () => resolveOnce(false);
      
      timeoutId = setTimeout(() => resolveOnce(false), timeout);
      
      img.src = url;
    });
  }
  
  /**
   * Validate array of card objects, replacing failed images
   * @param {Array} cards - Array of card objects with image_url property
   * @returns {Promise<Array>} - Cards with validated/replaced images
   */
  async function validateCards(cards) {
    if (!cards || !cards.length) {
      console.warn('ImagePreflight: No cards to validate');
      return cards;
    }
    
    validationResults.total = cards.length;
    validationResults.successful = 0;
    validationResults.failed = 0;
    validationResults.replacements = [];
    
    // Collect unique image URLs
    const imageUrls = [...new Set(cards.map(c => c.image_url).filter(Boolean))];
    
    console.log(`ImagePreflight: Validating ${imageUrls.length} unique images...`);
    
    // Preload all images in parallel
    const results = await Promise.all(
      imageUrls.map(url => preloadImage(url))
    );
    
    // Create lookup map
    const urlValidation = {};
    results.forEach(result => {
      urlValidation[result.url] = result.success;
      if (result.success) {
        validationResults.successful++;
      } else {
        validationResults.failed++;
        console.warn(`ImagePreflight: Failed to load ${result.url}`);
      }
    });
    
    // Replace failed images with fallback and count per-card failures
    let cardFailures = 0;
    const validatedCards = cards.map(card => {
      if (!card.image_url || !urlValidation[card.image_url]) {
        const originalUrl = card.image_url;
        card.image_url = CONFIG.FALLBACK_IMAGE;
        validationResults.replacements.push({
          original: originalUrl,
          cardId: card.id,
          name: card.name
        });
        cardFailures++;
        return { ...card, _imageFailed: true };
      }
      return { ...card, _imageFailed: false };
    });
    
    // Show banner if failure rate exceeds threshold (based on cards, not unique URLs)
    const failureRate = cardFailures / cards.length;
    if (failureRate > CONFIG.FAILURE_THRESHOLD) {
      showFailureBanner(cardFailures, cards.length);
    }
    
    console.log(`ImagePreflight: Complete - ${validationResults.successful} unique URLs successful, ${validationResults.failed} failed`);
    
    return validatedCards;
  }
  
  /**
   * Show banner warning about fallback images
   */
  function showFailureBanner(failed, total) {
    if (validationResults.bannerShown) return;
    validationResults.bannerShown = true;
    
    const banner = document.createElement('div');
    banner.className = 'alert alert-warning alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    banner.style.zIndex = '9999';
    banner.style.maxWidth = '600px';
    banner.innerHTML = `
      <div class="d-flex align-items-center">
        <i data-feather="alert-triangle" class="me-2"></i>
        <div>
          <strong>Using fallback images</strong><br>
          <small>${failed} of ${total} images (${Math.round(failed/total*100)}%) failed to load and were replaced with placeholders.</small>
        </div>
        <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
      </div>
    `;
    
    document.body.insertBefore(banner, document.body.firstChild);
    
    // Re-initialize feather icons
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
      banner.remove();
    }, 10000);
  }
  
  /**
   * Get validation statistics
   */
  function getStats() {
    return { ...validationResults };
  }
  
  /**
   * Reset validation state
   */
  function reset() {
    validationResults.total = 0;
    validationResults.successful = 0;
    validationResults.failed = 0;
    validationResults.replacements = [];
    validationResults.bannerShown = false;
  }
  
  // Public API
  return {
    validateCards,
    preloadImage,
    getStats,
    reset
  };
})();
