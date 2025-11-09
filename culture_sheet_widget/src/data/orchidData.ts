import { OrchidSpecies, Pollinator, CompanionPlant } from '../types/orchid';

export const sampleSpecies: OrchidSpecies[] = [
  { 
    id: '1', 
    scientificName: 'Cattleya mossiae', 
    commonName: 'Easter Orchid', 
    genus: 'Cattleya', 
    region: 'South America', 
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663639338_cf328881.webp',
    nativeRange: [{ lat: 10.5, lng: -66.9 }, { lat: 8.5, lng: -70.0 }, { lat: 9.0, lng: -68.5 }],
    climateData: { tempRange: { min: 65, max: 85 }, humidity: 70, precipitation: 60, koppenZone: 'Aw', usdaZone: 11, annualPrecipitation: 1800 },
    lightLevel: 'High'
  },

  { 
    id: '2', 
    scientificName: 'Dendrobium nobile', 
    commonName: 'Noble Dendrobium', 
    genus: 'Dendrobium', 
    region: 'Asia', 
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663641077_89b63153.webp',
    nativeRange: [{ lat: 28.0, lng: 85.0 }, { lat: 27.0, lng: 88.0 }, { lat: 26.5, lng: 90.0 }],
    climateData: { tempRange: { min: 50, max: 75 }, humidity: 65, precipitation: 55, koppenZone: 'Cfa', usdaZone: 9, annualPrecipitation: 1200 },
    lightLevel: 'Medium'
  },

  { 
    id: '3', 
    scientificName: 'Oncidium sphacelatum', 
    commonName: 'Dancing Lady', 
    genus: 'Oncidium', 
    region: 'Central America', 
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663643381_4de42b4e.webp',
    nativeRange: [{ lat: 14.6, lng: -90.5 }, { lat: 13.7, lng: -89.2 }, { lat: 15.0, lng: -88.0 }],
    climateData: { tempRange: { min: 60, max: 80 }, humidity: 75, precipitation: 70, koppenZone: 'Am', usdaZone: 10, annualPrecipitation: 2100 },
    lightLevel: 'High'
  },
  { 
    id: '4', 
    scientificName: 'Paphiopedilum rothschildianum', 
    commonName: 'Gold of Kinabalu', 
    genus: 'Paphiopedilum', 
    region: 'Southeast Asia', 
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663646183_d23b486c.webp',
    nativeRange: [{ lat: 6.0, lng: 116.5 }, { lat: 5.8, lng: 116.3 }, { lat: 6.2, lng: 116.7 }],
    climateData: { tempRange: { min: 70, max: 85 }, humidity: 80, precipitation: 90, koppenZone: 'Af', usdaZone: 12, annualPrecipitation: 2500 },
    lightLevel: 'Low'
  },
  { 
    id: '5', 
    scientificName: 'Vanda coerulea', 
    commonName: 'Blue Vanda', 
    genus: 'Vanda', 
    region: 'Asia', 
    imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663647487_449d75c3.webp',
    nativeRange: [{ lat: 25.0, lng: 95.0 }, { lat: 24.5, lng: 94.0 }, { lat: 26.0, lng: 93.5 }],
    climateData: { tempRange: { min: 55, max: 80 }, humidity: 70, precipitation: 65, koppenZone: 'Cfb', usdaZone: 10, annualPrecipitation: 1500 },
    lightLevel: 'Very High'
  },

];

export const pollinators: Pollinator[] = [
  { name: 'Honeybee', type: 'Bee', behavior: 'Collects nectar and pollen', imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663654896_764d8206.webp' },
  { name: 'Hummingbird', type: 'Bird', behavior: 'Hovers while feeding on nectar', imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663657083_6271de08.webp' },
];

export const companions: CompanionPlant[] = [
  { name: 'Tree Fern', scientificName: 'Cyathea cooperi', habitat: 'Understory shade', imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663658347_3804adba.webp' },
  { name: 'Bromeliad', scientificName: 'Guzmania lingulata', habitat: 'Epiphytic canopy', imageUrl: 'https://d64gsuwffb70l.cloudfront.net/69101c9bf3c933dcdd06e831_1762663659191_0e3c0c38.webp' },
];
