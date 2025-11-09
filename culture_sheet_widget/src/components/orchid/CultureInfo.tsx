import React from 'react';

interface Props {
  sections: {
    temperature?: boolean;
    light?: boolean;
    water?: boolean;
    humidity?: boolean;
    potting?: boolean;
    fertilizer?: boolean;
  };
}

export const CultureInfo: React.FC<Props> = ({ sections }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
      {sections.temperature && (
        <div className="bg-gradient-to-br from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
          <h4 className="font-bold text-lg mb-3 text-orange-900">Temperature</h4>
          <p className="text-sm text-gray-700 mb-2"><strong>Day:</strong> 70-85°F (21-29°C)</p>
          <p className="text-sm text-gray-700"><strong>Night:</strong> 55-65°F (13-18°C)</p>
        </div>
      )}
      {sections.light && (
        <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-6 rounded-xl border border-yellow-200">
          <h4 className="font-bold text-lg mb-3 text-amber-900">Light</h4>
          <p className="text-sm text-gray-700">2000-3000 foot-candles</p>
          <p className="text-xs text-gray-600 mt-2">Bright indirect light, no direct sun</p>
        </div>
      )}
      {sections.water && (
        <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-6 rounded-xl border border-blue-200">
          <h4 className="font-bold text-lg mb-3 text-blue-900">Water</h4>
          <p className="text-sm text-gray-700">Water when media is nearly dry</p>
          <p className="text-xs text-gray-600 mt-2">Typically every 5-7 days</p>
        </div>
      )}
      {sections.humidity && (
        <div className="bg-gradient-to-br from-teal-50 to-emerald-50 p-6 rounded-xl border border-teal-200">
          <h4 className="font-bold text-lg mb-3 text-teal-900">Humidity</h4>
          <p className="text-sm text-gray-700">50-70% relative humidity</p>
          <p className="text-xs text-gray-600 mt-2">Ensure good air circulation</p>
        </div>
      )}
      {sections.potting && (
        <div className="bg-gradient-to-br from-green-50 to-lime-50 p-6 rounded-xl border border-green-200">
          <h4 className="font-bold text-lg mb-3 text-green-900">Potting</h4>
          <p className="text-sm text-gray-700">Medium bark mix with perlite</p>
          <p className="text-xs text-gray-600 mt-2">Repot every 2-3 years</p>
        </div>
      )}
      {sections.fertilizer && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border border-purple-200">
          <h4 className="font-bold text-lg mb-3 text-purple-900">Fertilizer</h4>
          <p className="text-sm text-gray-700">Balanced 20-20-20, weekly weakly</p>
          <p className="text-xs text-gray-600 mt-2">1/4 strength during growth</p>
        </div>
      )}
    </div>
  );
};
