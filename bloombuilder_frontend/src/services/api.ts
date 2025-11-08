// API Service - Connects React UI to Flask Backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5000');

export interface Species {
  id: number;
  genus: string;
  species: string;
  common_name: string;
  naocc_template_url?: string;
}

export interface ImageMetadata {
  id: number;
  image_url: string;
  image_type: 'herbarium' | 'plate' | 'photo';
  collected_date?: string;
  locality?: string;
  collector_name?: string;
  source_db?: string;
}

export interface TraitData {
  id: number;
  trait_category: string;
  trait_value: string;
  trait_description: string;
  image_url?: string;
}

export const api = {
  // Get all species
  async getSpecies(): Promise<Species[]> {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/species/all`);
    if (!response.ok) throw new Error('Failed to fetch species');
    return response.json();
  },

  // Get species details with images and traits
  async getSpeciesDetails(speciesId: number) {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/species/${speciesId}`);
    if (!response.ok) throw new Error('Failed to fetch species details');
    return response.json();
  },

  // Get images for species
  async getImages(speciesId: number): Promise<{
    herbarium: ImageMetadata[];
    plates: ImageMetadata[];
    photos: ImageMetadata[];
  }> {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/images/${speciesId}`);
    if (!response.ok) throw new Error('Failed to fetch images');
    const data = await response.json();
    
    // Group images by type
    const herbarium = data.images.filter((img: ImageMetadata) => img.image_type === 'herbarium');
    const plates = data.images.filter((img: ImageMetadata) => img.image_type === 'plate');
    const photos = data.images.filter((img: ImageMetadata) => img.image_type === 'photo');
    
    return { herbarium, plates, photos };
  },

  // Get traits for species
  async getTraits(speciesId: number): Promise<TraitData[]> {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/traits/${speciesId}`);
    if (!response.ok) throw new Error('Failed to fetch traits');
    const data = await response.json();
    return data.traits || [];
  },

  // Toggle trait and get updated image
  async toggleTrait(speciesId: number, traitCategory: string, newValue: string) {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/traits/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        species_id: speciesId,
        trait_category: traitCategory,
        new_value: newValue
      })
    });
    if (!response.ok) throw new Error('Failed to toggle trait');
    return response.json();
  },

  // Search glossary
  async searchGlossary(term: string) {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/glossary/search?term=${encodeURIComponent(term)}`);
    if (!response.ok) throw new Error('Failed to search glossary');
    return response.json();
  },

  // Save creation
  async saveCreation(data: {
    species_id: number;
    creator_name: string;
    image_data: string; // base64 PNG
    style: string;
    canvas_data: any;
  }) {
    const response = await fetch(`${API_BASE_URL}/bloombuilder/api/save-creation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to save creation');
    return response.json();
  }
};
