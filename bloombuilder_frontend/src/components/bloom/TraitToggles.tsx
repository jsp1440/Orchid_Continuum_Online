import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sliders } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface Trait {
  name: string;
  options: { value: string; label: string }[];
  description: string;
}

const TRAITS: Trait[] = [
  {
    name: 'Spur Length',
    options: [
      { value: 'short', label: 'Short' },
      { value: 'long', label: 'Long' }
    ],
    description: 'Long spurs coevolve with long-tongued moths (Sphingidae) — only long proboscises reach nectar.'
  },
  {
    name: 'Petal Orientation',
    options: [
      { value: 'spreading', label: 'Spreading' },
      { value: 'reflexed', label: 'Reflexed' },
      { value: 'erect', label: 'Erect' }
    ],
    description: 'Petal orientation affects pollinator approach angles and visual signaling.'
  },
  {
    name: 'Color Morph',
    options: [
      { value: 'pink', label: 'Pink' },
      { value: 'white', label: 'White' },
      { value: 'yellow', label: 'Yellow' }
    ],
    description: 'Pink hues may attract bee and butterfly pollinators depending on UV patterns.'
  }
];

interface TraitTogglesProps {
  species: Species;
  onComplete: (traits: any[]) => void;
  onBack: () => void;
}

export function TraitToggles({ species, onComplete, onBack }: TraitTogglesProps) {
  const [selectedTraits, setSelectedTraits] = useState<Record<string, string>>({});

  const handleTraitChange = (traitName: string, value: string) => {
    setSelectedTraits(prev => ({ ...prev, [traitName]: value }));
  };

  const handleContinue = () => {
    const traitsArray = Object.entries(selectedTraits).map(([name, value]) => ({
      trait: name,
      value,
      appliedAt: new Date().toISOString()
    }));
    onComplete(traitsArray);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Apply Trait Toggles</h2>
        <p className="text-gray-600 mb-4">
          Apply known morphological variants for {species.scientificName}. These traits update the visual representation and record phenotypic variation.
        </p>
        <Badge variant="outline" className="text-base">
          {Object.keys(selectedTraits).length} trait{Object.keys(selectedTraits).length !== 1 ? 's' : ''} applied
        </Badge>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {TRAITS.map((trait) => (
          <Card key={trait.name} className="p-6">
            <div className="flex items-start gap-3 mb-4">
              <Sliders className="w-5 h-5 text-purple-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-2">{trait.name}</h3>
                <p className="text-sm text-gray-600 mb-4">{trait.description}</p>
                
                <div className="flex flex-wrap gap-2">
                  {trait.options.map((opt) => (
                    <Button
                      key={opt.value}
                      variant={selectedTraits[trait.name] === opt.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handleTraitChange(trait.name, opt.value)}
                      className={selectedTraits[trait.name] === opt.value ? 'bg-purple-600' : ''}
                    >
                      {opt.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          className="bg-purple-600 hover:bg-purple-700"
        >
          Continue to Assembly
        </Button>
      </div>
    </div>
  );
}

