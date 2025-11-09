import React, { useState, useEffect } from 'react';
import { OrchidSpecies } from '../../types/orchid';
import { sampleSpecies } from '../../data/orchidData';
import { useAppContext } from '../../contexts/AppContext';

interface Props {
  onSelect: (species: OrchidSpecies) => void;
  filteredSpecies?: OrchidSpecies[];
}

export const SearchBar: React.FC<Props> = ({ onSelect, filteredSpecies }) => {
  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const { autoDetectRegionalTheme } = useAppContext();
  
  const speciesToSearch = filteredSpecies || sampleSpecies;
  const filtered = speciesToSearch.filter(s => 
    s.scientificName.toLowerCase().includes(query.toLowerCase()) ||
    s.genus.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (species: OrchidSpecies) => {
    onSelect(species);
    setQuery(species.scientificName);
    setShowResults(false);
    
    // Auto-detect regional theme based on orchid origin
    autoDetectRegionalTheme(species.region);
  };

  return (
    <div className="relative w-full max-w-2xl">
      <input
        type="text"
        value={query}
        onChange={(e) => { setQuery(e.target.value); setShowResults(true); }}
        onFocus={() => setShowResults(true)}
        placeholder="Search genus or species (e.g., Cattleya mossiae)"
        className="w-full px-6 py-4 text-lg rounded-2xl border-2 border-gray-200 focus:border-[var(--color-primary)] focus:outline-none transition-all shadow-lg backdrop-blur-sm bg-white/90"
      />
      {showResults && query && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-xl shadow-2xl border border-gray-100 max-h-96 overflow-y-auto z-50">
          {filtered.length > 0 ? filtered.map(species => (
            <button
              key={species.id}
              onClick={() => handleSelect(species)}
              className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors flex items-center gap-4 border-b border-gray-50 last:border-0"
            >
              <img src={species.imageUrl} alt={species.scientificName} className="w-12 h-12 rounded-lg object-cover" />
              <div>
                <div className="font-semibold text-gray-900 italic">{species.scientificName}</div>
                <div className="text-sm text-gray-500">{species.commonName} • {species.region}</div>
              </div>
            </button>
          )) : (
            <div className="px-6 py-8 text-center text-gray-500">No match yet. Try a genus only or check spelling.</div>
          )}
        </div>
      )}
    </div>
  );
};
