import React from 'react';
import { RegionalTheme } from '../../types/themes';
import { regionalThemes } from '../../data/regionalThemes';

interface RegionalDecorationsProps {
  theme: RegionalTheme;
  position?: 'top' | 'bottom' | 'both';
}

export function RegionalDecorations({ theme, position = 'both' }: RegionalDecorationsProps) {
  if (theme === 'none') return null;

  const config = regionalThemes[theme];

  const renderAsianDecorations = () => (
    <>
      <svg className="absolute top-0 left-0 w-32 h-32 opacity-10" viewBox="0 0 100 100">
        <path d="M50,10 L50,90 M50,20 L45,15 M50,30 L55,25 M50,40 L45,35 M50,50 L55,45" 
              stroke={config.colors.primary} strokeWidth="2" fill="none"/>
        <circle cx="80" cy="20" r="8" fill={config.colors.decorative} opacity="0.3"/>
        <circle cx="75" cy="25" r="6" fill={config.colors.decorative} opacity="0.3"/>
        <circle cx="85" cy="25" r="6" fill={config.colors.decorative} opacity="0.3"/>
      </svg>
      <svg className="absolute bottom-0 right-0 w-32 h-32 opacity-10" viewBox="0 0 100 100">
        <path d="M20,80 Q30,70 40,80 T60,80 T80,80" 
              stroke={config.colors.accent} strokeWidth="1.5" fill="none"/>
      </svg>
    </>
  );

  const renderSouthAmericanDecorations = () => (
    <>
      <svg className="absolute top-0 right-0 w-40 h-40 opacity-10" viewBox="0 0 100 100">
        <pattern id="mayan" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
          <rect x="0" y="0" width="10" height="10" fill={config.colors.primary}/>
          <rect x="10" y="10" width="10" height="10" fill={config.colors.secondary}/>
        </pattern>
        <rect x="10" y="10" width="80" height="80" fill="url(#mayan)" opacity="0.5"/>
      </svg>
      <svg className="absolute bottom-0 left-0 w-32 h-32 opacity-15" viewBox="0 0 100 100">
        <path d="M20,50 Q30,30 50,30 T80,50 Q70,70 50,70 T20,50" 
              fill={config.colors.accent} opacity="0.4"/>
      </svg>
    </>
  );

  const renderAfricanDecorations = () => (
    <>
      <svg className="absolute top-0 left-0 w-36 h-36 opacity-10" viewBox="0 0 100 100">
        <pattern id="tribal" x="0" y="0" width="25" height="25" patternUnits="userSpaceOnUse">
          <path d="M12.5,5 L20,20 L5,20 Z" fill={config.colors.primary}/>
          <circle cx="12.5" cy="12.5" r="3" fill={config.colors.secondary}/>
        </pattern>
        <rect x="0" y="0" width="100" height="100" fill="url(#tribal)" opacity="0.4"/>
      </svg>
    </>
  );

  const renderAustralianDecorations = () => (
    <>
      <svg className="absolute top-0 right-0 w-48 h-48 opacity-10" viewBox="0 0 100 100">
        <pattern id="dots" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.5" fill={config.colors.primary}/>
          <circle cx="7" cy="7" r="1.5" fill={config.colors.secondary}/>
        </pattern>
        <rect x="0" y="0" width="100" height="100" fill="url(#dots)"/>
      </svg>
      <svg className="absolute bottom-0 left-0 w-32 h-32 opacity-10" viewBox="0 0 100 100">
        <path d="M10,50 Q20,40 30,50 T50,50 T70,50 T90,50" 
              stroke={config.colors.accent} strokeWidth="2" fill="none"/>
        <path d="M10,60 Q20,50 30,60 T50,60 T70,60 T90,60" 
              stroke={config.colors.decorative} strokeWidth="2" fill="none"/>
      </svg>
    </>
  );

  const renderEuropeanDecorations = () => (
    <>
      <svg className="absolute top-0 left-0 w-32 h-32 opacity-10" viewBox="0 0 100 100">
        <rect x="10" y="10" width="15" height="60" fill={config.colors.primary} opacity="0.3"/>
        <rect x="35" y="10" width="15" height="60" fill={config.colors.primary} opacity="0.3"/>
        <rect x="60" y="10" width="15" height="60" fill={config.colors.primary} opacity="0.3"/>
        <path d="M5,70 L80,70" stroke={config.colors.secondary} strokeWidth="3"/>
        <path d="M5,10 L80,10" stroke={config.colors.secondary} strokeWidth="3"/>
      </svg>
    </>
  );

  const renderNorthAmericanDecorations = () => (
    <>
      <svg className="absolute top-0 right-0 w-40 h-40 opacity-10" viewBox="0 0 100 100">
        <path d="M50,20 L30,50 L40,50 L40,70 L60,70 L60,50 L70,50 Z" 
              fill={config.colors.primary} opacity="0.4"/>
        <path d="M20,80 L30,70 L40,75 L50,65 L60,72 L70,68 L80,80" 
              stroke={config.colors.accent} strokeWidth="2" fill="none"/>
      </svg>
    </>
  );

  const decorations = {
    asian: renderAsianDecorations,
    'south-american': renderSouthAmericanDecorations,
    african: renderAfricanDecorations,
    australian: renderAustralianDecorations,
    european: renderEuropeanDecorations,
    'north-american': renderNorthAmericanDecorations,
    none: () => null
  };

  const renderFunc = decorations[theme];

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {(position === 'top' || position === 'both') && renderFunc()}
      {position === 'both' && (
        <div className="transform rotate-180">
          {renderFunc()}
        </div>
      )}
    </div>
  );
}