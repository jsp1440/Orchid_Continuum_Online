import React from 'react';
import { OrchidSpecies } from '../../types/orchid';

interface ClimateHeatmapProps {
  species: OrchidSpecies;
  userLocation?: { lat: number; lng: number; name: string };
}

export function ClimateHeatmap({ species, userLocation }: ClimateHeatmapProps) {
  const nativeClimate = species.climateData || { tempRange: { min: 60, max: 85 }, humidity: 70, precipitation: 60 };
  const userClimate = { tempRange: { min: 55, max: 90 }, humidity: 65, precipitation: 45 };

  const getTempMatch = () => {
    const nativeMid = (nativeClimate.tempRange.min + nativeClimate.tempRange.max) / 2;
    const userMid = (userClimate.tempRange.min + userClimate.tempRange.max) / 2;
    const diff = Math.abs(nativeMid - userMid);
    return Math.max(0, 100 - diff * 2);
  };

  const getHumidityMatch = () => Math.max(0, 100 - Math.abs(nativeClimate.humidity - userClimate.humidity) * 2);
  const getPrecipMatch = () => Math.max(0, 100 - Math.abs(nativeClimate.precipitation - userClimate.precipitation) * 2);

  const metrics = [
    { label: 'Temperature', native: `${nativeClimate.tempRange.min}-${nativeClimate.tempRange.max}°F`, user: `${userClimate.tempRange.min}-${userClimate.tempRange.max}°F`, match: getTempMatch() },
    { label: 'Humidity', native: `${nativeClimate.humidity}%`, user: `${userClimate.humidity}%`, match: getHumidityMatch() },
    { label: 'Precipitation', native: `${nativeClimate.precipitation}"`, user: `${userClimate.precipitation}"`, match: getPrecipMatch() }
  ];

  return (
    <div className="bg-white/80 backdrop-blur-lg rounded-xl p-6 shadow-lg">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Climate Comparison</h3>
      <p className="text-sm text-gray-600 mb-6">How your climate compares to native habitat</p>
      <div className="space-y-4">
        {metrics.map(m => (
          <div key={m.label}>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">{m.label}</span>
              <span className="text-gray-600">{m.match.toFixed(0)}% match</span>
            </div>
            <div className="h-8 bg-gray-200 rounded-lg overflow-hidden flex">
              <div className="h-full bg-gradient-to-r from-blue-500 to-green-500" style={{ width: `${m.match}%` }} />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Native: {m.native}</span>
              <span>Yours: {m.user}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
