export interface Species {
  id: string;
  commonName: string;
  scientificName: string;
  image: string;
}

export interface ImageMetadata {
  id: string;
  url: string;
  date: string;
  location: string;
  contributor: string;
  institution: string;
  type: 'herbarium' | 'botanical' | 'modern';
}

export interface TraitImageMetadata {
  id: string;
  url: string;
  spurLength: 'short' | 'long';
  petalColor: 'pink' | 'white' | 'yellow';
  name: string;
  description?: string;
  characteristics?: string;
  evolutionaryNotes?: string;
  pollinatorType?: string;
}



export interface Trait {
  id: string;
  name: string;
  options: TraitOption[];
}

export interface TraitOption {
  value: string;
  label: string;
  imageUrl: string;
  pollinatorInfo?: string;
  evolutionNote?: string;
}

export interface StyleOption {
  id: string;
  name: string;
  description: string;
}

export type Stage = 
  | 'species'           // Stage 1: Species Selection
  | 'photo'            // Stage 2: Photo Comparison
  | 'herbarium'        // Stage 3: Herbarium Sheet Selection
  | 'plate'            // Stage 4: Botanical Plate Selection
  | 'labeling'         // Stage 5: Labeling Interface
  | 'key'              // Stage 6: Dichotomous Key
  | 'validate'         // Stage 7: Validate & Correct
  | 'traits'           // Stage 8: Trait Toggles
  | 'assemble'         // Stage 9: Assemble Bloom Animation
  | 'export';          // Stage 10: Export & Save

export const STAGE_INFO: Record<Stage, { number: number; title: string; description: string }> = {
  species: { number: 1, title: 'Species Selection', description: 'Choose genus and species to validate' },
  photo: { number: 2, title: 'Photo Comparison', description: 'Select photos to compare and validate' },
  herbarium: { number: 3, title: 'Herbarium Sheets', description: 'Choose herbarium specimens (multi-select)' },
  plate: { number: 4, title: 'Botanical Plates', description: 'Select diagnostic botanical illustrations' },
  labeling: { number: 5, title: 'Label Structures', description: 'Apply labels using dichotomous key' },
  key: { number: 6, title: 'Dichotomous Key', description: 'Follow taxonomic key decisions' },
  validate: { number: 7, title: 'Validate & Correct', description: 'Verify labels and add corrections' },
  traits: { number: 8, title: 'Apply Traits', description: 'Toggle morphological variations' },
  assemble: { number: 9, title: 'Assemble Bloom', description: 'Watch flower parts come together' },
  export: { number: 10, title: 'Export & Save', description: 'Save your validated work' }
};
