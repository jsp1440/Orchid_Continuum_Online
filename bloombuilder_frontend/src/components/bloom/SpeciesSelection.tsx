import { useEffect, useState } from 'react';
import { Species } from '@/types/bloombuilder';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/services/api';

interface SpeciesSelectionProps {
  species?: Species[];
  onSelect: (species: Species) => void;
}

export function SpeciesSelection({ species: speciesProp, onSelect }: SpeciesSelectionProps) {
  const [species, setSpecies] = useState<Species[]>(speciesProp || []);
  const [loading, setLoading] = useState(!speciesProp);

  useEffect(() => {
    if (!speciesProp) {
      // Fetch from backend
      api.getSpecies().then(data => {
        // Transform backend data to match frontend Species type
        const transformed = data.map(sp => ({
          id: sp.id.toString(),
          commonName: sp.common_name,
          scientificName: `${sp.genus} ${sp.species}`,
          image: 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145787001_ec797981.webp' // Placeholder
        }));
        setSpecies(transformed);
        setLoading(false);
      }).catch(err => {
        console.error('Failed to fetch species:', err);
        setLoading(false);
      });
    }
  }, [speciesProp]);

  if (loading) {
    return <div className="p-8 text-center">Loading species...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2">Choose Your Orchid Species</h2>
        <p className="text-muted-foreground">
          Select from {species.length} orchid species to begin your journey
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {species.map((sp) => (
          <Card key={sp.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <div className="aspect-[4/3] overflow-hidden">
              <img
                src={sp.image}
                alt={sp.commonName}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-lg mb-1">{sp.commonName}</h3>
              <p className="text-sm text-muted-foreground italic mb-4">
                {sp.scientificName}
              </p>
              <Button onClick={() => onSelect(sp)} className="w-full">
                Select Species
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
