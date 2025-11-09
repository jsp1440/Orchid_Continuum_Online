import React, { useState, useEffect } from 'react';
import { OrchidSpecies } from '../../types/orchid';
import { ComparisonTable } from './ComparisonTable';
import { ComparisonCharts } from './ComparisonCharts';
import { sampleSpecies } from '../../data/orchidData';

export const ComparisonView: React.FC = () => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [compareSpecies, setCompareSpecies] = useState<OrchidSpecies[]>([]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ids = params.get('compare')?.split(',') || [];
    if (ids.length > 0) {
      setSelectedIds(ids);
      setCompareSpecies(sampleSpecies.filter(s => ids.includes(s.id)));
    }
  }, []);

  const toggleSpecies = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(sid => sid !== id));
      setCompareSpecies(compareSpecies.filter(s => s.id !== id));
    } else if (selectedIds.length < 3) {
      setSelectedIds([...selectedIds, id]);
      const species = sampleSpecies.find(s => s.id === id);
      if (species) setCompareSpecies([...compareSpecies, species]);
    }
  };

  const handleShare = () => {
    const url = `${window.location.origin}${window.location.pathname}?compare=${selectedIds.join(',')}`;
    navigator.clipboard.writeText(url);
    alert('Comparison link copied to clipboard!');
  };

  const handleExportPDF = () => {
    alert('PDF export functionality would use jsPDF library. Install with: npm install jspdf');
  };

  return (
    <div className="space-y-8">
      <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Select Species to Compare (2-3)</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {sampleSpecies.map(species => (
            <button
              key={species.id}
              onClick={() => toggleSpecies(species.id)}
              disabled={!selectedIds.includes(species.id) && selectedIds.length >= 3}
              className={`p-4 rounded-lg border-2 transition-all ${
                selectedIds.includes(species.id)
                  ? 'border-purple-600 bg-purple-50'
                  : 'border-gray-200 hover:border-purple-300'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="text-sm font-medium text-center">{species.scientificName}</div>
            </button>
          ))}
        </div>
      </div>

      {compareSpecies.length >= 2 && (
        <>
          <div className="flex gap-4 justify-end">
            <button onClick={handleShare} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              Share Comparison
            </button>
            <button onClick={handleExportPDF} className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              Export as PDF
            </button>
          </div>

          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Comparison Table</h2>
            <ComparisonTable species={compareSpecies} />
          </div>

          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Visual Comparison</h2>
            <ComparisonCharts species={compareSpecies} />
          </div>
        </>
      )}
    </div>
  );
};
