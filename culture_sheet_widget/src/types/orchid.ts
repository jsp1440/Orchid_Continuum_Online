export interface OrchidSpecies {
  id: string;
  scientificName: string;
  commonName?: string;
  genus: string;
  region: string;
  imageUrl?: string;
  nativeRange?: { lat: number; lng: number }[];
  climateData?: ClimateData;
  lightLevel?: 'Low' | 'Medium' | 'High' | 'Very High';
}


export interface CultureSheet {
  species: OrchidSpecies;
  temperature: { day: string; night: string };
  light: string;
  water: string;
  humidity: string;
  potting: string;
  fertilizer: string;
  pollinators: Pollinator[];
  companions: CompanionPlant[];
  nativeRange: { lat: number; lng: number }[];
  climateData: ClimateData;
}

export interface Pollinator {
  name: string;
  type: string;
  behavior: string;
  imageUrl: string;
}

export interface CompanionPlant {
  name: string;
  scientificName: string;
  habitat: string;
  imageUrl: string;
}

export interface ClimateData {
  tempRange: { min: number; max: number };
  humidity: number;
  precipitation: number;
  koppenZone?: string;
  usdaZone?: number;
  annualPrecipitation?: number;
}


export type InterfaceTheme = 
  | 'scientific-lab'
  | 'botanical-garden'
  | 'enchanted-forest'
  | 'orbital-station'
  | 'futuristic-greenhouse'
  | 'victorian-parlor'
  | 'field-guide'
  | 'ecological-research';

export type SheetTheme = 
  | 'scientific-publication'
  | 'vintage-botanical'
  | 'fantasy-grimoire'
  | 'scifi-database'
  | 'futuristic-guide'
  | 'field-journal'
  | 'research-report'
  | 'victorian-manuscript';


