import React from 'react';
import { OrchidSpecies } from '../../types/orchid';

interface ComparisonChartsProps {
  species: OrchidSpecies[];
}

export const ComparisonCharts: React.FC<ComparisonChartsProps> = ({ species }) => {
  const colors = ['#8B5CF6', '#EC4899', '#F59E0B'];
  
  const maxTemp = Math.max(...species.map(s => s.climateData?.tempRange.max || 0));
  const maxHumidity = 100;
  const lightLevels = { 'Low': 25, 'Medium': 50, 'High': 75, 'Very High': 100 };

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Temperature Range Comparison</h3>
        <div className="space-y-4">
          {species.map((s, i) => (
            <div key={s.id}>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: colors[i] }} />
                <span className="text-sm font-medium">{s.scientificName}</span>
              </div>
              <div className="relative h-8 bg-gray-100 rounded">
                <div
                  className="absolute h-full rounded"
                  style={{
                    left: `${((s.climateData?.tempRange.min || 0) / maxTemp) * 100}%`,
                    width: `${(((s.climateData?.tempRange.max || 0) - (s.climateData?.tempRange.min || 0)) / maxTemp) * 100}%`,
                    backgroundColor: colors[i]
                  }}
                />
                <span className="absolute left-2 top-1 text-xs text-white font-medium">
                  {s.climateData?.tempRange.min}°F - {s.climateData?.tempRange.max}°F
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Humidity Requirements</h3>
        <div className="flex gap-4 items-end h-48">
          {species.map((s, i) => (
            <div key={s.id} className="flex-1 flex flex-col items-center">
              <div className="w-full bg-gray-100 rounded-t relative flex-1 flex items-end">
                <div
                  className="w-full rounded-t transition-all"
                  style={{
                    height: `${(s.climateData?.humidity || 0)}%`,
                    backgroundColor: colors[i]
                  }}
                />
              </div>
              <span className="text-sm font-medium mt-2">{s.climateData?.humidity}%</span>
              <span className="text-xs text-gray-600 text-center mt-1">{s.scientificName.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Light Level Requirements</h3>
        <div className="flex gap-4 items-end h-48">
          {species.map((s, i) => (
            <div key={s.id} className="flex-1 flex flex-col items-center">
              <div className="w-full bg-gray-100 rounded-t relative flex-1 flex items-end">
                <div
                  className="w-full rounded-t transition-all"
                  style={{
                    height: `${lightLevels[s.lightLevel || 'Medium']}%`,
                    backgroundColor: colors[i]
                  }}
                />
              </div>
              <span className="text-sm font-medium mt-2">{s.lightLevel}</span>
              <span className="text-xs text-gray-600 text-center mt-1">{s.scientificName.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
