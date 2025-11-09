// Interface themes - how the app looks
export type InterfaceTheme = 
  | 'scientific-lab'
  | 'botanical-garden'
  | 'enchanted-forest'
  | 'orbital-station'
  | 'futuristic-greenhouse'
  | 'victorian-parlor'
  | 'field-guide'
  | 'ecological-research';


// Culture sheet themes - how generated sheets look
export type CultureSheetTheme = 
  | 'scientific-publication'
  | 'vintage-botanical'
  | 'fantasy-grimoire'
  | 'scifi-database'
  | 'futuristic-guide'
  | 'field-journal'
  | 'research-report'
  | 'victorian-manuscript';


// Regional themes - based on orchid origin
export type RegionalTheme = 
  | 'asian'
  | 'south-american'
  | 'african'
  | 'australian'
  | 'european'
  | 'north-american'
  | 'none';

export interface ThemeConfig {
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    bg: string;
    text: string;
  };
  fonts?: {
    heading?: string;
    body?: string;
  };
}
