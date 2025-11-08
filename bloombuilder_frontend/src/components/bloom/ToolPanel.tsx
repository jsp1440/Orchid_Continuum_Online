import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Save } from 'lucide-react';
import { ThemeSelector } from './ThemeSelector';
import { TraitToggles } from './TraitToggles';
import { ContinuumCredits } from './ContinuumCredits';
import { OrchidGamiLinks } from './OrchidGamiLinks';
import { TraitImageLibrary } from './TraitImageLibrary';

interface ToolPanelProps {
  onStyleChange: (style: string) => void;
  onSave: () => void;
}

export function ToolPanel({ onStyleChange, onSave }: ToolPanelProps) {
  return (
    <div className="h-full overflow-y-auto p-6 space-y-4 bg-muted/30">
      <div className="text-center py-4 border-b-2 border-primary/20">
        <h2 className="text-lg font-bold text-primary">Continue the Sequence</h2>
        <p className="text-xs text-muted-foreground mt-1">
          Every discovery is part of a living sequence
        </p>
      </div>

      <ThemeSelector />
      <TraitToggles />
      <TraitImageLibrary />
      <ContinuumCredits />
      <OrchidGamiLinks />


      <Button onClick={onSave} className="w-full" size="lg">
        <Save className="mr-2 w-4 h-4" />
        Save & View Credits
      </Button>
    </div>
  );
}

