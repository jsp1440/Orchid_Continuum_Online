export interface FilterPreset {
  id: string;
  name: string;
  filters: OrchidFilters;
}

export interface OrchidFilters {
  koppenZones: string[];
  usdaZones: number[];
  tempRange: [number, number];
  humidityRange: [number, number];
  lightLevels: string[];
  regions: string[];
}

export const defaultFilters: OrchidFilters = {
  koppenZones: [],
  usdaZones: [],
  tempRange: [40, 100],
  humidityRange: [0, 100],
  lightLevels: [],
  regions: []
};
