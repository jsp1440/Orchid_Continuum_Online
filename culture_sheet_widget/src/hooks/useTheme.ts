import { useState, useEffect } from 'react';
import { InterfaceTheme } from '../types/orchid';
import { interfaceThemes } from '../data/themeConfigs';

export function useTheme() {
  const [theme, setThemeState] = useState<InterfaceTheme>('scientific-lab');

  useEffect(() => {
    const saved = localStorage.getItem('orchid-interface-theme') as InterfaceTheme;
    if (saved && interfaceThemes[saved]) {
      setThemeState(saved);
    }
  }, []);

  const setTheme = (newTheme: InterfaceTheme) => {
    setThemeState(newTheme);
    localStorage.setItem('orchid-interface-theme', newTheme);
    
    const config = interfaceThemes[newTheme];
    document.documentElement.style.setProperty('--color-primary', config.colors.primary);
    document.documentElement.style.setProperty('--color-secondary', config.colors.secondary);
    document.documentElement.style.setProperty('--color-accent', config.colors.accent);
    document.documentElement.style.setProperty('--color-bg', config.colors.bg);
    document.documentElement.style.setProperty('--color-text', config.colors.text);
  };

  useEffect(() => {
    setTheme(theme);
  }, []);

  return { theme, setTheme };
}
