import React from 'react';
import { Globe, X } from 'lucide-react';
import { RegionalTheme } from '../../types/themes';
import { regionalThemes } from '../../data/regionalThemes';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

interface RegionalThemeIndicatorProps {
  activeTheme: RegionalTheme;
  onOverride: () => void;
  onReset: () => void;
  isManualOverride: boolean;
}

export function RegionalThemeIndicator({
  activeTheme,
  onOverride,
  onReset,
  isManualOverride
}: RegionalThemeIndicatorProps) {
  if (activeTheme === 'none') return null;

  const theme = regionalThemes[activeTheme];

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      <div 
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border-2 p-4"
        style={{ borderColor: theme.colors.primary }}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <Globe className="h-5 w-5" style={{ color: theme.colors.primary }} />
            <h3 className="font-semibold text-sm">{theme.name}</h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
          {theme.description}
        </p>

        <div className="flex flex-wrap gap-1 mb-3">
          {theme.decorativeElements.slice(0, 3).map((element) => (
            <Badge 
              key={element} 
              variant="outline"
              className="text-xs"
              style={{ borderColor: theme.colors.accent, color: theme.colors.accent }}
            >
              {element}
            </Badge>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            {Object.values(theme.colors).map((color, i) => (
              <div
                key={i}
                className="w-6 h-6 rounded-full border border-gray-300"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
          
          {isManualOverride ? (
            <Badge variant="secondary" className="text-xs">
              Manual
            </Badge>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={onOverride}
              className="text-xs h-7"
            >
              Override
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}