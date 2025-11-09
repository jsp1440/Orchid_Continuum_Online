import { RegionalTheme } from '../types/themes';

export interface RegionalThemeConfig {
  id: RegionalTheme;
  name: string;
  description: string;
  regions: string[];
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    decorative: string;
  };
  patterns: {
    name: string;
    svg: string;
  };
  decorativeElements: string[];
  culturalMotifs: string[];
}

export const regionalThemes: Record<RegionalTheme, RegionalThemeConfig> = {
  asian: {
    id: 'asian',
    name: 'Asian Heritage',
    description: 'Ink wash painting aesthetics with bamboo and cherry blossom motifs',
    regions: ['China', 'Japan', 'Thailand', 'Vietnam', 'Korea', 'Taiwan', 'Myanmar', 'Laos'],
    colors: {
      primary: '#DC143C',
      secondary: '#FFD700',
      accent: '#2F4F4F',
      decorative: '#FF69B4'
    },
    patterns: {
      name: 'bamboo',
      svg: 'M10,2 L10,22 M10,6 L8,4 M10,10 L12,8 M10,14 L8,12 M10,18 L12,16'
    },
    decorativeElements: ['bamboo', 'cherry blossoms', 'pagoda', 'koi fish'],
    culturalMotifs: ['calligraphy', 'ink wash', 'zen circles', 'origami']
  },
  'south-american': {
    id: 'south-american',
    name: 'South American Tropical',
    description: 'Vibrant rainforest imagery with Mayan and Aztec patterns',
    regions: ['Brazil', 'Colombia', 'Ecuador', 'Peru', 'Venezuela', 'Bolivia', 'Argentina'],
    colors: {
      primary: '#FF6B35',
      secondary: '#F7931E',
      accent: '#27AE60',
      decorative: '#E74C3C'
    },
    patterns: {
      name: 'mayan',
      svg: 'M2,2 L6,2 L6,6 L2,6 Z M8,8 L12,8 L12,12 L8,12 Z M14,2 L18,2 L18,6 L14,6 Z'
    },
    decorativeElements: ['tropical leaves', 'toucans', 'pyramids', 'jaguars'],
    culturalMotifs: ['geometric patterns', 'feathers', 'sun symbols', 'spirals']
  },
  african: {
    id: 'african',
    name: 'African Savanna',
    description: 'Textile patterns with warm savanna sunset colors',
    regions: ['Madagascar', 'South Africa', 'Kenya', 'Tanzania', 'Zimbabwe', 'Uganda'],
    colors: {
      primary: '#D2691E',
      secondary: '#8B4513',
      accent: '#FF8C00',
      decorative: '#CD853F'
    },
    patterns: {
      name: 'tribal',
      svg: 'M2,10 L6,2 L10,10 M14,10 L18,2 L22,10 M2,14 L6,22 L10,14'
    },
    decorativeElements: ['acacia trees', 'elephants', 'tribal masks', 'baobab'],
    culturalMotifs: ['kente patterns', 'mud cloth', 'geometric shapes', 'shields']
  },
  australian: {
    id: 'australian',
    name: 'Australian Outback',
    description: 'Indigenous dot painting with ocean wave patterns',
    regions: ['Australia', 'New Zealand', 'Papua New Guinea', 'Fiji', 'Solomon Islands'],
    colors: {
      primary: '#FF7F50',
      secondary: '#40E0D0',
      accent: '#DAA520',
      decorative: '#4682B4'
    },
    patterns: {
      name: 'dots',
      svg: 'M3,3 A1,1 0 1,1 3,5 A1,1 0 1,1 3,3 M9,3 A1,1 0 1,1 9,5 A1,1 0 1,1 9,3'
    },
    decorativeElements: ['kangaroos', 'eucalyptus', 'boomerang', 'coral reef'],
    culturalMotifs: ['dot painting', 'dreamtime', 'wave patterns', 'circles']
  },
  european: {
    id: 'european',
    name: 'European Classical',
    description: 'Mediterranean aesthetic with classical architecture motifs',
    regions: ['Greece', 'Italy', 'Spain', 'France', 'Portugal', 'Turkey', 'Cyprus'],
    colors: {
      primary: '#4169E1',
      secondary: '#FFD700',
      accent: '#8FBC8F',
      decorative: '#DDA0DD'
    },
    patterns: {
      name: 'mosaic',
      svg: 'M2,2 L6,2 L4,6 Z M6,2 L10,2 L8,6 Z M10,2 L14,2 L12,6 Z'
    },
    decorativeElements: ['columns', 'olive branches', 'grapes', 'amphora'],
    culturalMotifs: ['mosaic tiles', 'marble', 'laurel wreaths', 'scrollwork']
  },
  'north-american': {
    id: 'north-american',
    name: 'North American Wilderness',
    description: 'National park aesthetic with native patterns',
    regions: ['USA', 'Canada', 'Mexico', 'Guatemala', 'Costa Rica', 'Panama'],
    colors: {
      primary: '#8B4513',
      secondary: '#228B22',
      accent: '#B8860B',
      decorative: '#CD5C5C'
    },
    patterns: {
      name: 'native',
      svg: 'M2,10 L10,2 L18,10 M6,10 L10,6 L14,10'
    },
    decorativeElements: ['pine trees', 'eagles', 'mountains', 'bears'],
    culturalMotifs: ['native patterns', 'totem poles', 'dreamcatchers', 'arrowheads']
  },
  none: {
    id: 'none',
    name: 'No Regional Theme',
    description: 'Default appearance without regional styling',
    regions: [],
    colors: {
      primary: '#6B7280',
      secondary: '#9CA3AF',
      accent: '#4B5563',
      decorative: '#D1D5DB'
    },
    patterns: {
      name: 'none',
      svg: ''
    },
    decorativeElements: [],
    culturalMotifs: []
  }
};

export function detectRegionalTheme(origin: string): RegionalTheme {
  const normalizedOrigin = origin.toLowerCase();
  
  for (const [themeId, config] of Object.entries(regionalThemes)) {
    if (themeId === 'none') continue;
    
    for (const region of config.regions) {
      if (normalizedOrigin.includes(region.toLowerCase())) {
        return themeId as RegionalTheme;
      }
    }
  }
  
  return 'none';
}