import React, { createContext, useContext, useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { toast } from '@/components/ui/use-toast';

export type SpurLength = 'short' | 'long';
export type PetalColor = 'pink' | 'white' | 'yellow';
export type TraitKey = `${SpurLength}-${PetalColor}`;

export interface TraitImageMappings {
  [key: string]: string; // TraitKey -> image URL
}

interface AppContextType {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  spurLength: SpurLength;
  petalColor: PetalColor;
  setSpurLength: (length: SpurLength) => void;
  setPetalColor: (color: PetalColor) => void;
  traitImageMappings: TraitImageMappings;
  setTraitImageMapping: (traitKey: TraitKey, imageUrl: string) => void;
  getTraitImageUrl: (spurLength: SpurLength, petalColor: PetalColor) => string | null;
}


const defaultAppContext: AppContextType = {
  sidebarOpen: false,
  toggleSidebar: () => {},
  spurLength: 'short',
  petalColor: 'pink',
  setSpurLength: () => {},
  setPetalColor: () => {},
  traitImageMappings: {},
  setTraitImageMapping: () => {},
  getTraitImageUrl: () => null,
};


const AppContext = createContext<AppContextType>(defaultAppContext);

export const useAppContext = () => useContext(AppContext);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [spurLength, setSpurLength] = useState<SpurLength>('short');
  const [petalColor, setPetalColor] = useState<PetalColor>('pink');
  
  // Load trait image mappings from localStorage
  const [traitImageMappings, setTraitImageMappings] = useState<TraitImageMappings>(() => {
    const stored = localStorage.getItem('bloombuilder-trait-images');
    return stored ? JSON.parse(stored) : {};
  });

  // Persist trait image mappings to localStorage
  useEffect(() => {
    localStorage.setItem('bloombuilder-trait-images', JSON.stringify(traitImageMappings));
  }, [traitImageMappings]);

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  const setTraitImageMapping = (traitKey: TraitKey, imageUrl: string) => {
    setTraitImageMappings(prev => ({
      ...prev,
      [traitKey]: imageUrl,
    }));
    toast({
      title: 'Image Updated',
      description: `Trait combination "${traitKey}" image has been set.`,
    });
  };

  const getTraitImageUrl = (spur: SpurLength, color: PetalColor): string | null => {
    const key: TraitKey = `${spur}-${color}`;
    return traitImageMappings[key] || null;
  };

  return (
    <AppContext.Provider
      value={{
        sidebarOpen,
        toggleSidebar,
        spurLength,
        petalColor,
        setSpurLength,
        setPetalColor,
        traitImageMappings,
        setTraitImageMapping,
        getTraitImageUrl,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};


