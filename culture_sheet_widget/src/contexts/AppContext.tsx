import React, { createContext, useContext, useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { toast } from '@/components/ui/use-toast';
import { RegionalTheme } from '../types/themes';
import { detectRegionalTheme } from '../data/regionalThemes';

interface AppContextType {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  regionalTheme: RegionalTheme;
  setRegionalTheme: (theme: RegionalTheme) => void;
  isManualRegionalOverride: boolean;
  setIsManualRegionalOverride: (value: boolean) => void;
  autoDetectRegionalTheme: (origin: string) => void;
  resetRegionalTheme: () => void;
}

const defaultAppContext: AppContextType = {
  sidebarOpen: false,
  toggleSidebar: () => {},
  regionalTheme: 'none',
  setRegionalTheme: () => {},
  isManualRegionalOverride: false,
  setIsManualRegionalOverride: () => {},
  autoDetectRegionalTheme: () => {},
  resetRegionalTheme: () => {},
};

const AppContext = createContext<AppContextType>(defaultAppContext);

export const useAppContext = () => useContext(AppContext);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [regionalTheme, setRegionalTheme] = useState<RegionalTheme>('none');
  const [isManualRegionalOverride, setIsManualRegionalOverride] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  const autoDetectRegionalTheme = (origin: string) => {
    if (!isManualRegionalOverride) {
      const detectedTheme = detectRegionalTheme(origin);
      setRegionalTheme(detectedTheme);
      if (detectedTheme !== 'none') {
        toast({
          title: 'Regional Theme Applied',
          description: `Applied ${detectedTheme} theme based on orchid origin`,
        });
      }
    }
  };

  const resetRegionalTheme = () => {
    setRegionalTheme('none');
    setIsManualRegionalOverride(false);
  };

  useEffect(() => {
    // Apply regional theme CSS variables
    if (regionalTheme !== 'none') {
      const root = document.documentElement;
      const theme = require('../data/regionalThemes').regionalThemes[regionalTheme];
      
      root.style.setProperty('--regional-primary', theme.colors.primary);
      root.style.setProperty('--regional-secondary', theme.colors.secondary);
      root.style.setProperty('--regional-accent', theme.colors.accent);
      root.style.setProperty('--regional-decorative', theme.colors.decorative);
    } else {
      // Reset regional CSS variables
      const root = document.documentElement;
      root.style.removeProperty('--regional-primary');
      root.style.removeProperty('--regional-secondary');
      root.style.removeProperty('--regional-accent');
      root.style.removeProperty('--regional-decorative');
    }
  }, [regionalTheme]);

  return (
    <AppContext.Provider
      value={{
        sidebarOpen,
        toggleSidebar,
        regionalTheme,
        setRegionalTheme,
        isManualRegionalOverride,
        setIsManualRegionalOverride,
        autoDetectRegionalTheme,
        resetRegionalTheme,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};
