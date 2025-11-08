import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const UPSTREAM = process.env.UPSTREAM || 'https://orchid-continuum-1.onrender.com';
const PORT = process.env.PORT || 5000;

const app = express();

// Enable CORS for all origins
app.use(cors());

// Serve static files from /public
app.use(express.static(join(__dirname, 'public')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ ok: true });
});

// API proxy endpoint - transforms /api/search-orchids response to widget format
app.get('/api/orchids', async (req, res) => {
  try {
    // Map widget params to backend params
    const params = new URLSearchParams();
    
    // Widget sends: limit, offset, country, genus, temp, min_elev, max_elev
    // Backend expects: limit, q (query), genus, climate
    if (req.query.limit) params.set('limit', req.query.limit);
    if (req.query.genus) params.set('genus', req.query.genus);
    if (req.query.country) params.set('q', req.query.country); // Map country to search query
    if (req.query.temp) params.set('climate', req.query.temp);
    
    // Use the actual backend endpoint
    const url = `${UPSTREAM}/api/search-orchids${params.toString() ? '?' + params.toString() : ''}`;
    console.log(`Proxying request to: ${url}`);
    
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' }
    });
    
    // Handle non-OK responses
    if (!response.ok) {
      return res.status(502).json({
        error: 'upstream_error',
        detail: `${response.status} ${response.statusText}`
      });
    }
    
    // Parse response
    const data = await response.json();
    
    // Transform backend format {orchids: [...], total: N} to widget format {items: [...], total: N}
    const transformed = {
      items: data.orchids || [],
      total: data.total || 0
    };
    
    // Set cache header for successful responses
    res.set('Cache-Control', 'public, max-age=300');
    res.json(transformed);
    
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(502).json({
      error: 'upstream_error',
      detail: error.message
    });
  }
});

// Route aliases for widgets
app.get('/', (req, res) => {
  res.sendFile(join(__dirname, 'public', 'index.html'));
});

app.get('/gallery', (req, res) => {
  res.sendFile(join(__dirname, 'public', 'gallery.html'));
});

app.get('/legend', (req, res) => {
  res.sendFile(join(__dirname, 'public', 'legend.html'));
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌸 Orchid Widget Proxy Server running on port ${PORT}`);
  console.log(`📍 Gallery:  http://0.0.0.0:${PORT}/`);
  console.log(`📍 Legend:   http://0.0.0.0:${PORT}/legend`);
  console.log(`📍 API:      http://0.0.0.0:${PORT}/api/orchids`);
  console.log(`🔗 Upstream: ${UPSTREAM}`);
});
