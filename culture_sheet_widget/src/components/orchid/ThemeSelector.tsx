import React from 'react';
import { InterfaceTheme } from '../../types/orchid';
import { interfaceThemes } from '../../data/themeConfigs';

interface Props {
  currentTheme: InterfaceTheme;
  onThemeChange: (theme: InterfaceTheme) => void;
}

export const ThemeSelector: React.FC<Props> = ({ currentTheme, onThemeChange }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {(Object.keys(interfaceThemes) as InterfaceTheme[]).map(theme => {
        const config = interfaceThemes[theme];
        return (
          <button
            key={theme}
            onClick={() => onThemeChange(theme)}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              currentTheme === theme 
                ? 'border-4 shadow-xl scale-105' 
                : 'border-gray-200 hover:border-gray-400 hover:scale-102 shadow-md'
            }`}
            style={{ 
              backgroundColor: config.colors.bg,
              borderColor: currentTheme === theme ? config.colors.primary : undefined
            }}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-full" style={{ backgroundColor: config.colors.primary }} />
              <h3 className="font-bold text-sm" style={{ color: config.colors.text }}>{config.name}</h3>
            </div>
            <p className="text-xs opacity-80" style={{ color: config.colors.text }}>{config.description}</p>
          </button>
        );
      })}
    </div>
  );
};
