import React from 'react';
import { CompanionPlant } from '../../types/orchid';

interface Props {
  plant: CompanionPlant;
}

export const CompanionCard: React.FC<Props> = ({ plant }) => {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow">
      <img 
        src={plant.imageUrl} 
        alt={plant.name}
        className="w-full h-40 object-cover"
      />
      <div className="p-4">
        <h4 className="font-bold text-gray-900 mb-1">{plant.name}</h4>
        <p className="text-sm text-gray-500 italic mb-2">{plant.scientificName}</p>
        <p className="text-xs text-[var(--color-primary)] font-medium">{plant.habitat}</p>
      </div>
    </div>
  );
};
