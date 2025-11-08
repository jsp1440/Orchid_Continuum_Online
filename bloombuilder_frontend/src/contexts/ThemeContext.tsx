import React, { createContext, useContext, useState } from 'react';

export type ThemeMode = 'modern' | 'victorian' | 'regency' | 'fantasy' | 'ecofuturist';

interface ThemeContextType {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  themeConfig: ThemeConfig;
}

interface ThemeConfig {
  name: string;
  description: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
  atmosphere: string;
}

const themeConfigs: Record<ThemeMode, ThemeConfig> = {
  modern: {
    name: 'Modern Scientific',
    description: 'Crisp, minimal, data-driven',
    colors: { primary: 'bg-slate-700', secondary: 'bg-blue-500', accent: 'bg-cyan-400' },
    atmosphere: 'clean'
  },
  victorian: {
    name: 'Victorian Naturalist',
    description: 'Journal tone, sepia palette',
    colors: { primary: 'bg-amber-800', secondary: 'bg-orange-700', accent: 'bg-yellow-600' },
    atmosphere: 'vintage'
  },
  regency: {
    name: 'Regency Botanical Salon',
    description: 'Elegant, pastel, refined',
    colors: { primary: 'bg-pink-400', secondary: 'bg-purple-300', accent: 'bg-rose-300' },
    atmosphere: 'elegant'
  },
  fantasy: {
    name: 'Fantasy Conservatory',
    description: 'Ethereal, art nouveau',
    colors: { primary: 'bg-violet-600', secondary: 'bg-fuchsia-500', accent: 'bg-pink-400' },
    atmosphere: 'magical'
  },
  ecofuturist: {
    name: 'Eco-Futurist',
    description: 'Holographic, teal gradients',
    colors: { primary: 'bg-teal-600', secondary: 'bg-emerald-500', accent: 'bg-cyan-400' },
    atmosphere: 'futuristic'
  }
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<ThemeMode>('modern');

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themeConfig: themeConfigs[theme] }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
