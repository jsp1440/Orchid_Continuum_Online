import React from 'react';
import { OrchidSpecies } from '../../types/orchid';

interface ComparisonTableProps {
  species: OrchidSpecies[];
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ species }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-3 text-left font-semibold">Attribute</th>
            {species.map(s => (
              <th key={s.id} className="border p-3 text-left font-semibold">{s.scientificName}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Common Name</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.commonName || 'N/A'}</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Region</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.region}</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Temperature Range</td>
            {species.map(s => (
              <td key={s.id} className="border p-3">
                {s.climateData?.tempRange.min}°F - {s.climateData?.tempRange.max}°F
              </td>
            ))}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Humidity</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.climateData?.humidity}%</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Light Level</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.lightLevel}</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Köppen Zone</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.climateData?.koppenZone || 'N/A'}</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">USDA Zone</td>
            {species.map(s => <td key={s.id} className="border p-3">{s.climateData?.usdaZone || 'N/A'}</td>)}
          </tr>
          <tr>
            <td className="border p-3 font-medium bg-gray-50">Annual Precipitation</td>
            {species.map(s => (
              <td key={s.id} className="border p-3">
                {s.climateData?.annualPrecipitation ? `${s.climateData.annualPrecipitation}mm` : 'N/A'}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
};
