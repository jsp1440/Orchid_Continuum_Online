import React, { useState } from 'react';

interface Props {
  onLocationSet: (location: { lat: number; lng: number; city: string }) => void;
}

export const LocationPicker: React.FC<Props> = ({ onLocationSet }) => {
  const [city, setCity] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUseGPS = () => {
    setLoading(true);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          onLocationSet({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            city: 'Your Location'
          });
          setLoading(false);
        },
        () => {
          alert('Unable to get location');
          setLoading(false);
        }
      );
    }
  };

  const handleCitySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (city) {
      onLocationSet({ lat: 0, lng: 0, city });
      setCity('');
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-3 w-full max-w-2xl">
      <form onSubmit={handleCitySubmit} className="flex-1 flex gap-2">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Enter city name"
          className="flex-1 px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-[var(--color-primary)] focus:outline-none"
        />
        <button type="submit" className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-xl hover:opacity-90 transition-opacity font-medium">
          Set
        </button>
      </form>
      <button
        onClick={handleUseGPS}
        disabled={loading}
        className="px-6 py-3 bg-[var(--color-accent)] text-white rounded-xl hover:opacity-90 transition-opacity font-medium disabled:opacity-50"
      >
        {loading ? 'Getting...' : 'Use GPS'}
      </button>
    </div>
  );
};
