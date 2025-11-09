import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { ThemeSelector } from './ThemeSelector';
import { CultureSheetThemeSelector } from './CultureSheetThemeSelector';
import { EmailPreferencesSection } from './EmailPreferencesSection';
import { SheetTheme } from '../../types/orchid';
import { regionalThemes } from '../../data/regionalThemes';
import { Globe } from 'lucide-react';
import { RegionalTheme } from '../../types/themes';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  interfaceTheme: string;
  onInterfaceThemeChange: (theme: string) => void;
  sheetTheme: SheetTheme;
  onSheetThemeChange: (theme: SheetTheme) => void;
  regionalTheme: RegionalTheme;
  onRegionalThemeChange: (theme: RegionalTheme) => void;
  onManualOverride: (value: boolean) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen, onClose, interfaceTheme, onInterfaceThemeChange,
  sheetTheme, onSheetThemeChange, regionalTheme, onRegionalThemeChange, onManualOverride
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">Interface Theme</h3>
            <ThemeSelector currentTheme={interfaceTheme} onThemeChange={onInterfaceThemeChange} />
          </div>
          <div>
            <h3 className="text-lg font-semibold mb-3">Culture Sheet Theme</h3>
            <CultureSheetThemeSelector currentTheme={sheetTheme} onThemeChange={onSheetThemeChange} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Globe className="h-5 w-5" />
              <h3 className="text-lg font-semibold">Regional Theme</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(regionalThemes).map(([key, theme]) => (
                <button
                  key={key}
                  onClick={() => { onRegionalThemeChange(key as RegionalTheme); onManualOverride(key !== 'none'); }}
                  className={`p-3 rounded-lg border-2 transition-all ${regionalTheme === key ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-400'}`}
                >
                  <div className="text-sm font-medium mb-1">{theme.name}</div>
                  {key !== 'none' && (
                    <div className="flex gap-1 justify-center">
                      {Object.values(theme.colors).slice(0, 4).map((color, i) => (
                        <div key={i} className="w-4 h-4 rounded-full" style={{ backgroundColor: color }} />
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
          <div>
            <EmailPreferencesSection />
          </div>

        </div>
      </DialogContent>
    </Dialog>
  );
};
