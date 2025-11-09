import React, { useState } from 'react';
import { OrchidFilters, FilterPreset, defaultFilters } from '../../types/filters';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Badge } from '../ui/badge';

interface Props {
  filters: OrchidFilters;
  onFiltersChange: (filters: OrchidFilters) => void;
  resultCount: number;
}

const koppenOptions = ['Af', 'Am', 'Aw', 'Cfa', 'Cfb', 'Cfc'];
const usdaOptions = [9, 10, 11, 12, 13];
const lightOptions = ['Low', 'Medium', 'High', 'Very High'];
const regionOptions = ['South America', 'Central America', 'Asia', 'Southeast Asia', 'Africa', 'Oceania'];

export const AdvancedFilters: React.FC<Props> = ({ filters, onFiltersChange, resultCount }) => {
  const [presets, setPresets] = useState<FilterPreset[]>(() => {
    const saved = localStorage.getItem('orchidFilterPresets');
    return saved ? JSON.parse(saved) : [];
  });
  const [presetName, setPresetName] = useState('');

  const toggleMultiSelect = (key: keyof OrchidFilters, value: any) => {
    const current = filters[key] as any[];
    const updated = current.includes(value) 
      ? current.filter(v => v !== value)
      : [...current, value];
    onFiltersChange({ ...filters, [key]: updated });
  };

  const savePreset = () => {
    if (!presetName.trim()) return;
    const newPreset: FilterPreset = {
      id: Date.now().toString(),
      name: presetName,
      filters: { ...filters }
    };
    const updated = [...presets, newPreset];
    setPresets(updated);
    localStorage.setItem('orchidFilterPresets', JSON.stringify(updated));
    setPresetName('');
  };

  const loadPreset = (preset: FilterPreset) => {
    onFiltersChange(preset.filters);
  };

  const deletePreset = (id: string) => {
    const updated = presets.filter(p => p.id !== id);
    setPresets(updated);
    localStorage.setItem('orchidFilterPresets', JSON.stringify(updated));
  };

  const clearFilters = () => {
    onFiltersChange(defaultFilters);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-gray-900">Advanced Filters</h3>
        <Badge variant="secondary" className="text-lg px-3 py-1">
          {resultCount} results
        </Badge>
      </div>

      {/* Köppen Climate Zones */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">Köppen Climate Zones</label>
        <div className="flex flex-wrap gap-2">
          {koppenOptions.map(zone => (
            <Button
              key={zone}
              size="sm"
              variant={filters.koppenZones.includes(zone) ? 'default' : 'outline'}
              onClick={() => toggleMultiSelect('koppenZones', zone)}
            >
              {zone}
            </Button>
          ))}
        </div>
      </div>

      {/* USDA Hardiness Zones */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">USDA Hardiness Zones</label>
        <div className="flex flex-wrap gap-2">
          {usdaOptions.map(zone => (
            <Button
              key={zone}
              size="sm"
              variant={filters.usdaZones.includes(zone) ? 'default' : 'outline'}
              onClick={() => toggleMultiSelect('usdaZones', zone)}
            >
              Zone {zone}
            </Button>
          ))}
        </div>
      </div>

      {/* Temperature Range */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Temperature Range: {filters.tempRange[0]}°F - {filters.tempRange[1]}°F
        </label>
        <Slider
          min={40}
          max={100}
          step={5}
          value={filters.tempRange}
          onValueChange={(value) => onFiltersChange({ ...filters, tempRange: value as [number, number] })}
          className="w-full"
        />
      </div>

      {/* Humidity Range */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Humidity Range: {filters.humidityRange[0]}% - {filters.humidityRange[1]}%
        </label>
        <Slider
          min={0}
          max={100}
          step={5}
          value={filters.humidityRange}
          onValueChange={(value) => onFiltersChange({ ...filters, humidityRange: value as [number, number] })}
          className="w-full"
        />
      </div>

      {/* Light Levels */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">Light Levels</label>
        <div className="flex flex-wrap gap-2">
          {lightOptions.map(level => (
            <Button
              key={level}
              size="sm"
              variant={filters.lightLevels.includes(level) ? 'default' : 'outline'}
              onClick={() => toggleMultiSelect('lightLevels', level)}
            >
              {level}
            </Button>
          ))}
        </div>
      </div>

      {/* Geographic Regions */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">Geographic Regions</label>
        <div className="flex flex-wrap gap-2">
          {regionOptions.map(region => (
            <Button
              key={region}
              size="sm"
              variant={filters.regions.includes(region) ? 'default' : 'outline'}
              onClick={() => toggleMultiSelect('regions', region)}
            >
              {region}
            </Button>
          ))}
        </div>
      </div>

      {/* Save Preset */}
      <div className="border-t pt-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">Save Filter Preset</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={presetName}
            onChange={(e) => setPresetName(e.target.value)}
            placeholder="Preset name..."
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2"
          />
          <Button onClick={savePreset} disabled={!presetName.trim()}>
            Save
          </Button>
        </div>
      </div>

      {/* Saved Presets */}
      {presets.length > 0 && (
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Saved Presets</label>
          <div className="flex flex-wrap gap-2">
            {presets.map(preset => (
              <div key={preset.id} className="flex items-center gap-1 bg-gray-100 rounded-lg px-3 py-1">
                <button
                  onClick={() => loadPreset(preset)}
                  className="text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  {preset.name}
                </button>
                <button
                  onClick={() => deletePreset(preset.id)}
                  className="text-red-500 hover:text-red-700 ml-2"
                  aria-label={`Delete ${preset.name} preset`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <Button onClick={clearFilters} variant="outline" className="w-full">
        Clear All Filters
      </Button>
    </div>
  );
};
