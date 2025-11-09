import React from 'react';
import { OrchidSpecies } from '../../types/orchid';

interface Props {
  collection: OrchidSpecies[];
  onSelect: (species: OrchidSpecies) => void;
}

export const CollectionLibrary: React.FC<Props> = ({ collection, onSelect }) => {
  if (collection.length === 0) {
    return (
      <div className="text-center py-16 bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl">
        <div className="text-6xl mb-4">🌸</div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Your Collection is Empty</h3>
        <p className="text-gray-600">Create your first culture sheet to start your collection.</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
      <h2 className="text-3xl font-bold mb-6 text-gray-900">My Collection</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {collection.map(species => (
          <button
            key={species.id}
            onClick={() => onSelect(species)}
            className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all hover:scale-105 text-left"
          >
            <img src={species.imageUrl} alt={species.scientificName} className="w-full h-48 object-cover" />
            <div className="p-4">
              <h4 className="font-bold text-lg text-gray-900 italic mb-1">{species.scientificName}</h4>
              <p className="text-sm text-gray-600">{species.commonName}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
