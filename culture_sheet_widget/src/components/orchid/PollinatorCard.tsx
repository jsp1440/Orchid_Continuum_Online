import React from 'react';
import { Pollinator } from '../../types/orchid';

interface Props {
  pollinator: Pollinator;
}

export const PollinatorCard: React.FC<Props> = ({ pollinator }) => {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow">
      <img 
        src={pollinator.imageUrl} 
        alt={pollinator.name}
        className="w-full h-48 object-cover"
      />
      <div className="p-4">
        <h4 className="font-bold text-lg text-gray-900 mb-1">{pollinator.name}</h4>
        <p className="text-sm text-[var(--color-primary)] font-medium mb-2">{pollinator.type}</p>
        <p className="text-sm text-gray-600">{pollinator.behavior}</p>
      </div>
    </div>
  );
};
