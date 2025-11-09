import { InterfaceTheme, CultureSheetTheme, RegionalTheme, ThemeConfig } from '../types/themes';

export const interfaceThemes: Record<InterfaceTheme, ThemeConfig> = {
  'scientific-lab': {
    name: 'Scientific Laboratory',
    description: 'Dark navy, purple accent, clean minimal professional',
    colors: { primary: '#9d4edd', secondary: '#1a1a2e', accent: '#7209b7', bg: '#16213e', text: '#f1f1f1' }
  },
  'botanical-garden': {
    name: 'Artistic Botanical Garden',
    description: 'Cream parchment, olive green, vintage aesthetic',
    colors: { primary: '#6b8e23', secondary: '#f5f5dc', accent: '#556b2f', bg: '#faf8f3', text: '#2d3319' }
  },
  'enchanted-forest': {
    name: 'Fantasy Enchanted Forest',
    description: 'Midnight blue, magical cyan, glowing effects',
    colors: { primary: '#00d9ff', secondary: '#0a1128', accent: '#00ffff', bg: '#1a1a3e', text: '#e0f7ff' }
  },
  'orbital-station': {
    name: 'Sci-Fi Orbital Station',
    description: 'Deep black, matrix green, neon glows',
    colors: { primary: '#00ff41', secondary: '#000000', accent: '#00d4ff', bg: '#0d0d0d', text: '#00ff41' }
  },
  'futuristic-greenhouse': {
    name: 'Futuristic Greenhouse',
    description: 'Clean white, bright green, minimalist modern',
    colors: { primary: '#00c853', secondary: '#ffffff', accent: '#64dd17', bg: '#f8f9fa', text: '#212121' }
  },

  'victorian-parlor': {
    name: 'Victorian Parlor',
    description: 'Deep burgundy, gold accents, ornate elegant design',
    colors: { primary: '#8B0000', secondary: '#FFD700', accent: '#4B0082', bg: '#2F1B1B', text: '#F5E6D3' }
  },

  'field-guide': {
    name: 'Nature Field Guide',
    description: 'Beige, saddle brown, earthy natural',
    colors: { primary: '#8b4513', secondary: '#f5deb3', accent: '#228b22', bg: '#faf0e6', text: '#3e2723' }
  },
  'ecological-research': {
    name: 'Ecological Research',
    description: 'Blue-gray, green accent, professional scientific',
    colors: { primary: '#2e7d32', secondary: '#607d8b', accent: '#4caf50', bg: '#eceff1', text: '#263238' }
  }
};

export const cultureSheetThemes: Record<CultureSheetTheme, ThemeConfig> = {
  'scientific-publication': {
    name: 'Scientific Publication',
    description: 'Academic paper layout, precise typography',
    colors: { primary: '#1976d2', secondary: '#ffffff', accent: '#0d47a1', bg: '#fafafa', text: '#212121' }
  },
  'vintage-botanical': {
    name: 'Vintage Botanical Plate',
    description: 'Ornate borders, aged parchment texture',
    colors: { primary: '#8b7355', secondary: '#f4e8d8', accent: '#6b5d4f', bg: '#fef9f3', text: '#3e2723' }
  },
  'fantasy-grimoire': {
    name: 'Fantasy Spell Grimoire',
    description: 'Medieval fonts, mystical symbols',
    colors: { primary: '#7b1fa2', secondary: '#1a1a1a', accent: '#9c27b0', bg: '#2a1a2a', text: '#e1bee7' }
  },
  'scifi-database': {
    name: 'Sci-Fi Database Entry',
    description: 'Holographic interface, wireframe graphics',
    colors: { primary: '#00e5ff', secondary: '#000a12', accent: '#00b8d4', bg: '#0d1117', text: '#00e5ff' }
  },
  'futuristic-guide': {
    name: 'Futuristic Guide',
    description: 'Minimalist modern, clean infographics',
    colors: { primary: '#00bfa5', secondary: '#ffffff', accent: '#1de9b6', bg: '#f5f5f5', text: '#263238' }
  },
  'field-journal': {
    name: 'Field Journal Entry',
    description: 'Handwritten style, coffee stains, sketches',
    colors: { primary: '#5d4037', secondary: '#efebe9', accent: '#795548', bg: '#faf8f5', text: '#3e2723' }
  },
  'research-report': {
    name: 'Research Report',
    description: 'Professional tables, conservation data',
    colors: { primary: '#1b5e20', secondary: '#e8f5e9', accent: '#2e7d32', bg: '#ffffff', text: '#1b5e20' }
  },
  'victorian-manuscript': {
    name: 'Victorian Manuscript',
    description: 'Ornate Victorian borders, rich burgundy and gold',
    colors: { primary: '#8B0000', secondary: '#FFF8DC', accent: '#DAA520', bg: '#F5F5DC', text: '#2F1B1B' }
  }
};

