import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet.markercluster';
import { OrchidSpecies } from '../../types/orchid';

interface MapViewProps {
  species: OrchidSpecies;
  userLocation?: { lat: number; lng: number; name: string };
}

export function MapView({ species, userLocation }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.MarkerClusterGroup | null>(null);
  const climateLayersRef = useRef<{
    koppen?: L.LayerGroup;
    usda?: L.LayerGroup;
    precipitation?: L.LayerGroup;
  }>({});
  
  const [activeLayers, setActiveLayers] = useState({
    nativeRange: true,
    wildPhotos: false,
    climateZones: false,
    userMatch: false
  });
  
  const [activeClimateLayer, setActiveClimateLayer] = useState<'koppen' | 'usda' | 'precipitation' | null>(null);

  // Köppen climate classification colors
  const koppenColors: Record<string, string> = {
    'Af': '#0000FF', // Tropical rainforest
    'Am': '#0078FF', // Tropical monsoon
    'Aw': '#46A9FF', // Tropical savanna
    'Cfa': '#00FF00', // Humid subtropical
    'Cfb': '#65C365', // Oceanic
    'Cfc': '#328232', // Subpolar oceanic
  };

  // USDA hardiness zone colors
  const usdaColors: Record<number, string> = {
    9: '#FFFF00',
    10: '#FFD700',
    11: '#FFA500',
    12: '#FF8C00',
    13: '#FF4500',
  };

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: species.nativeRange?.[0] ? [species.nativeRange[0].lat, species.nativeRange[0].lng] : [0, 0],
      zoom: 6,
      zoomControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap'
    }).addTo(map);

    // Add markers for native range
    if (species.nativeRange && species.nativeRange.length > 0) {
      const markers = (L as any).markerClusterGroup();
      species.nativeRange.forEach(point => {
        const marker = L.marker([point.lat, point.lng])
          .bindPopup(`<strong>${species.scientificName}</strong><br/>Native habitat location`);
        markers.addLayer(marker);
      });
      map.addLayer(markers);
      markersRef.current = markers;
    }

    // Add user location marker if available
    if (userLocation) {
      L.marker([userLocation.lat, userLocation.lng], {
        icon: L.icon({
          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41]
        })
      }).addTo(map).bindPopup(`<strong>Your Location</strong><br/>${userLocation.name}`);
    }

    // Create Köppen climate layer
    const koppenLayer = L.layerGroup();
    if (species.nativeRange && species.climateData?.koppenZone) {
      species.nativeRange.forEach(point => {
        L.circle([point.lat, point.lng], {
          radius: 100000,
          color: koppenColors[species.climateData.koppenZone] || '#888888',
          fillColor: koppenColors[species.climateData.koppenZone] || '#888888',
          fillOpacity: 0.3,
          weight: 2
        }).bindPopup(`<strong>Köppen: ${species.climateData.koppenZone}</strong><br/>Tropical climate zone`).addTo(koppenLayer);
      });
    }
    climateLayersRef.current.koppen = koppenLayer;

    // Create USDA hardiness zone layer
    const usdaLayer = L.layerGroup();
    if (species.nativeRange && species.climateData?.usdaZone) {
      species.nativeRange.forEach(point => {
        L.circle([point.lat, point.lng], {
          radius: 100000,
          color: usdaColors[species.climateData.usdaZone] || '#888888',
          fillColor: usdaColors[species.climateData.usdaZone] || '#888888',
          fillOpacity: 0.3,
          weight: 2
        }).bindPopup(`<strong>USDA Zone: ${species.climateData.usdaZone}</strong><br/>Hardiness zone`).addTo(usdaLayer);
      });
    }
    climateLayersRef.current.usda = usdaLayer;

    // Create precipitation pattern layer
    const precipLayer = L.layerGroup();
    if (species.nativeRange && species.climateData?.annualPrecipitation) {
      const precip = species.climateData.annualPrecipitation;
      const color = precip > 2000 ? '#0000FF' : precip > 1500 ? '#4169E1' : precip > 1000 ? '#87CEEB' : '#B0E0E6';
      species.nativeRange.forEach(point => {
        L.circle([point.lat, point.lng], {
          radius: 100000,
          color: color,
          fillColor: color,
          fillOpacity: 0.3,
          weight: 2
        }).bindPopup(`<strong>Precipitation: ${precip}mm/year</strong><br/>Annual rainfall`).addTo(precipLayer);
      });
    }
    climateLayersRef.current.precipitation = precipLayer;

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [species, userLocation]);

  // Handle climate layer toggling
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove all climate layers first
    Object.values(climateLayersRef.current).forEach(layer => {
      if (layer && mapRef.current?.hasLayer(layer)) {
        mapRef.current.removeLayer(layer);
      }
    });

    // Add the active climate layer
    if (activeClimateLayer && climateLayersRef.current[activeClimateLayer]) {
      mapRef.current.addLayer(climateLayersRef.current[activeClimateLayer]!);
    }
  }, [activeClimateLayer]);

  const toggleLayer = (layer: keyof typeof activeLayers) => {
    setActiveLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  const toggleClimateLayer = (layer: 'koppen' | 'usda' | 'precipitation') => {
    setActiveClimateLayer(prev => prev === layer ? null : layer);
  };

  return (
    <div className="relative">
      <div ref={containerRef} className="h-96 rounded-xl overflow-hidden shadow-lg" role="application" aria-label="Interactive orchid distribution map" />
      
      {/* Main layer toggles */}
      <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 space-y-2 z-[1000]">
        <div className="text-xs font-semibold text-gray-600 mb-2">Map Layers</div>
        {Object.entries(activeLayers).map(([key, active]) => (
          <button key={key} onClick={() => toggleLayer(key as keyof typeof activeLayers)} className={`block w-full text-left px-3 py-2 rounded text-sm font-medium transition ${active ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`} aria-pressed={active}>
            {key === 'nativeRange' && 'Native Range'}
            {key === 'wildPhotos' && 'Wild Photos'}
            {key === 'climateZones' && 'Climate Zones'}
            {key === 'userMatch' && 'Your Climate Match'}
          </button>
        ))}
      </div>

      {/* Climate zone overlay toggles */}
      <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 space-y-2 z-[1000]">
        <div className="text-xs font-semibold text-gray-600 mb-2">Climate Overlays</div>
        <button onClick={() => toggleClimateLayer('koppen')} className={`block w-full text-left px-3 py-2 rounded text-sm font-medium transition ${activeClimateLayer === 'koppen' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`} aria-pressed={activeClimateLayer === 'koppen'}>
          Köppen Classification
        </button>
        <button onClick={() => toggleClimateLayer('usda')} className={`block w-full text-left px-3 py-2 rounded text-sm font-medium transition ${activeClimateLayer === 'usda' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`} aria-pressed={activeClimateLayer === 'usda'}>
          USDA Hardiness
        </button>
        <button onClick={() => toggleClimateLayer('precipitation')} className={`block w-full text-left px-3 py-2 rounded text-sm font-medium transition ${activeClimateLayer === 'precipitation' ? 'bg-cyan-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`} aria-pressed={activeClimateLayer === 'precipitation'}>
          Precipitation
        </button>
      </div>

      {/* Legend */}
      {activeClimateLayer && (
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 z-[1000] max-w-xs">
          <div className="text-xs font-semibold text-gray-700 mb-2">
            {activeClimateLayer === 'koppen' && 'Köppen Climate Zones'}
            {activeClimateLayer === 'usda' && 'USDA Hardiness Zones'}
            {activeClimateLayer === 'precipitation' && 'Annual Precipitation'}
          </div>
          <div className="space-y-1 text-xs">
            {activeClimateLayer === 'koppen' && (
              <>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded" style={{backgroundColor: '#0000FF'}}></span> Af - Tropical Rainforest</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded" style={{backgroundColor: '#0078FF'}}></span> Am - Tropical Monsoon</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded" style={{backgroundColor: '#46A9FF'}}></span> Aw - Tropical Savanna</div>
              </>
            )}
            {activeClimateLayer === 'usda' && (
              <>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-yellow-400"></span> Zone 9 (20-30°F)</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-yellow-500"></span> Zone 10 (30-40°F)</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-orange-400"></span> Zone 11 (40-50°F)</div>
              </>
            )}
            {activeClimateLayer === 'precipitation' && (
              <>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-blue-800"></span> &gt;2000mm High</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-blue-600"></span> 1500-2000mm</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-blue-400"></span> 1000-1500mm</div>
                <div className="flex items-center gap-2"><span className="w-4 h-4 rounded bg-blue-200"></span> &lt;1000mm Low</div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

