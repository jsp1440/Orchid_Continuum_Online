import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { useAppContext } from '../contexts/AppContext';
import { useAuth } from '../contexts/AuthContext';
import { HeroSection } from './orchid/HeroSection';
import { SearchBar } from './orchid/SearchBar';
import { LocationPicker } from './orchid/LocationPicker';
import { SectionToggles } from './orchid/SectionToggles';
import { GeneratedSheet } from './orchid/GeneratedSheet';
import { AboutModal } from './orchid/AboutModal';
import { CollectionLibrary } from './orchid/CollectionLibrary';
import { EmbedWidget } from './orchid/EmbedWidget';
import { Footer } from './orchid/Footer';
import { AdvancedFilters } from './orchid/AdvancedFilters';
import { ComparisonView } from './orchid/ComparisonView';
import { RegionalThemeIndicator } from './orchid/RegionalThemeIndicator';
import { SettingsModal } from './orchid/SettingsModal';
import { AuthModal } from './auth/AuthModal';
import { UserDashboard } from './orchid/UserDashboard';
import { ProtectedRoute } from './ProtectedRoute';
import { OrchidSpecies, SheetTheme } from '../types/orchid';
import { OrchidFilters, defaultFilters } from '../types/filters';
import { sampleSpecies } from '../data/orchidData';
import { Settings, LogIn, LogOut, User } from 'lucide-react';


export default function AppLayout() {
  const { theme, setTheme } = useTheme();
  const { user, signOut } = useAuth();
  const { regionalTheme, setRegionalTheme, isManualRegionalOverride, setIsManualRegionalOverride, resetRegionalTheme } = useAppContext();
  
  const [view, setView] = useState<'home' | 'collection' | 'embed' | 'compare' | 'dashboard'>('home');
  const [sheetTheme, setSheetTheme] = useState<SheetTheme>('scientific-publication');
  const [showSettings, setShowSettings] = useState(false);
  const [showAuth, setShowAuth] = useState(false);


  const [selectedSpecies, setSelectedSpecies] = useState<OrchidSpecies | null>(null);
  const [location, setLocation] = useState<any>(null);
  const [generated, setGenerated] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [collection, setCollection] = useState<OrchidSpecies[]>([]);
  const [filters, setFilters] = useState<OrchidFilters>(defaultFilters);
  const [showFilters, setShowFilters] = useState(false);
  const [sections, setSections] = useState({
    temperature: true, light: true, water: true, 
    humidity: true, potting: true, fertilizer: true,
    pollinators: true, companions: true, maps: false
  });

  // Apply filters to species list
  const filteredSpecies = sampleSpecies.filter(species => {
    // Köppen zones filter
    if (filters.koppenZones.length > 0 && !filters.koppenZones.includes(species.climateData?.koppenZone || '')) {
      return false;
    }
    // USDA zones filter
    if (filters.usdaZones.length > 0 && !filters.usdaZones.includes(species.climateData?.usdaZone || 0)) {
      return false;
    }
    // Temperature range filter
    const minTemp = species.climateData?.tempRange.min || 0;
    const maxTemp = species.climateData?.tempRange.max || 100;
    if (maxTemp < filters.tempRange[0] || minTemp > filters.tempRange[1]) {
      return false;
    }
    // Humidity filter
    const humidity = species.climateData?.humidity || 0;
    if (humidity < filters.humidityRange[0] || humidity > filters.humidityRange[1]) {
      return false;
    }
    // Light levels filter
    if (filters.lightLevels.length > 0 && !filters.lightLevels.includes(species.lightLevel || '')) {
      return false;
    }
    // Regions filter
    if (filters.regions.length > 0 && !filters.regions.includes(species.region)) {
      return false;
    }
    return true;
  });

  const sectionList = [
    { id: 'temperature', label: 'Temperature', tooltip: 'Native and recommended day/night ranges', enabled: sections.temperature },
    { id: 'light', label: 'Light', tooltip: 'Foot-candle or Lux targets', enabled: sections.light },
    { id: 'water', label: 'Water', tooltip: 'Frequency based on media and season', enabled: sections.water },
    { id: 'humidity', label: 'Humidity', tooltip: 'Target RH and air movement tips', enabled: sections.humidity },
    { id: 'potting', label: 'Potting', tooltip: 'Media choices and repot timing', enabled: sections.potting },
    { id: 'fertilizer', label: 'Fertilizer', tooltip: 'Dilution ratios and timing', enabled: sections.fertilizer },
    { id: 'pollinators', label: 'Pollinators', tooltip: 'Who visits this orchid in the wild', enabled: sections.pollinators },
    { id: 'companions', label: 'Companions', tooltip: 'Plants in same habitat', enabled: sections.companions },
    { id: 'maps', label: 'Maps & Climate', tooltip: 'Native distribution and climate match', enabled: sections.maps },
  ];

  const handleToggle = (id: string) => setSections(prev => ({ ...prev, [id]: !prev[id as keyof typeof prev] }));
  const handleGenerate = () => { if (selectedSpecies) { setGenerated(true); window.scrollTo({ top: 9999, behavior: 'smooth' }); } };
  const handleSave = () => { if (selectedSpecies && !collection.find(s => s.id === selectedSpecies.id)) { setCollection([...collection, selectedSpecies]); } };
  
  const handleLoadSheet = (sheetData: any) => {
    setSelectedSpecies(sheetData.species);
    setSections(sheetData.sections);
    setSheetTheme(sheetData.theme);
    setLocation(sheetData.location || null);
    setView('home');
    setGenerated(true);
  };

  // Check for URL parameter to open settings modal (for unsubscribe links)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('openSettings') === 'true') {
      setShowSettings(true);
      // Clean up URL without reloading
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);



  return (
    <div className="min-h-screen transition-colors duration-300" style={{ backgroundColor: 'var(--color-bg)' }}>
      <nav className="bg-white/90 backdrop-blur-lg shadow-md sticky top-0 z-40">
         <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
           <h1 className="text-2xl font-bold text-[var(--color-primary)]">Orchid Culture</h1>
           <div className="flex gap-4 items-center">
             <button onClick={() => setView('home')} className={`px-4 py-2 rounded-lg font-medium transition-colors ${view === 'home' ? 'bg-[var(--color-primary)] text-white' : 'text-gray-700 hover:bg-gray-100'}`}>Home</button>
             <button onClick={() => setView('compare')} className={`px-4 py-2 rounded-lg font-medium transition-colors ${view === 'compare' ? 'bg-[var(--color-primary)] text-white' : 'text-gray-700 hover:bg-gray-100'}`}>Compare</button>
             <button onClick={() => setView('collection')} className={`px-4 py-2 rounded-lg font-medium transition-colors ${view === 'collection' ? 'bg-[var(--color-primary)] text-white' : 'text-gray-700 hover:bg-gray-100'}`}>Collection</button>
             <button onClick={() => setView('embed')} className={`px-4 py-2 rounded-lg font-medium transition-colors ${view === 'embed' ? 'bg-[var(--color-primary)] text-white' : 'text-gray-700 hover:bg-gray-100'}`}>Embed</button>
             <button onClick={() => setShowAbout(true)} className="px-4 py-2 rounded-lg font-medium text-gray-700 hover:bg-gray-100 transition-colors">About</button>
             <button onClick={() => setShowSettings(true)} className="p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors">
               <Settings className="h-5 w-5" />
             </button>
             {user ? (
               <>
                 <button onClick={() => setView('dashboard')} className={`px-4 py-2 rounded-lg font-medium transition-colors ${view === 'dashboard' ? 'bg-[var(--color-primary)] text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                   <User className="h-5 w-5 inline mr-2" />
                   Dashboard
                 </button>
                 <button onClick={signOut} className="px-4 py-2 rounded-lg font-medium text-gray-700 hover:bg-gray-100 transition-colors">
                   <LogOut className="h-5 w-5 inline mr-2" />
                   Logout
                 </button>
               </>
             ) : (
               <button onClick={() => setShowAuth(true)} className="px-4 py-2 rounded-lg font-medium bg-[var(--color-primary)] text-white hover:opacity-90 transition-opacity">
                 <LogIn className="h-5 w-5 inline mr-2" />
                 Login
               </button>
             )}
           </div>
         </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {view === 'compare' && <ComparisonView />}
        {view === 'collection' && <CollectionLibrary collection={collection} onSelect={(s) => { setSelectedSpecies(s); setView('home'); setGenerated(false); }} />}
        {view === 'embed' && <EmbedWidget />}
        {view === 'dashboard' && (
          <ProtectedRoute>
            <UserDashboard onLoadSheet={handleLoadSheet} />
          </ProtectedRoute>
        )}

        {view === 'home' && (
          <>
            <HeroSection />
            <div className="mb-12 bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Search Species</h2>
                <button onClick={() => setShowFilters(!showFilters)} className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity">
                  {showFilters ? 'Hide Filters' : 'Show Advanced Filters'}
                </button>
              </div>
              <p className="text-gray-600 mb-6">Search genus or species (e.g., Cattleya mossiae)</p>
              <SearchBar onSelect={setSelectedSpecies} filteredSpecies={filteredSpecies} />
              {showFilters && (
                <div className="mt-6">
                  <AdvancedFilters filters={filters} onFiltersChange={setFilters} resultCount={filteredSpecies.length} />
                </div>
              )}
            </div>
            <div className="mb-12 bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Location</h2>
              <p className="text-sm text-gray-600 mb-6">Compare your climate to the orchid's native range</p>
              <LocationPicker onLocationSet={setLocation} />
            </div>
            <div className="mb-12 bg-white/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Select Sections</h2>
              <p className="text-gray-600 mb-6">Choose which information to include in your culture sheet</p>
              <SectionToggles sections={sectionList} onToggle={handleToggle} />
            </div>
            <div className="text-center mb-12">
              <button onClick={handleGenerate} disabled={!selectedSpecies} className="px-12 py-5 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-white text-xl font-bold rounded-2xl shadow-2xl hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100">
                Generate My Culture Sheet
              </button>
            </div>
            {generated && selectedSpecies && <GeneratedSheet species={selectedSpecies} sections={sections} theme={sheetTheme} location={location} onPrint={() => window.print()} onShare={() => { navigator.clipboard.writeText(window.location.href); alert('Link copied!'); }} />}

          </>
        )}
      </div>
      
      {regionalTheme !== 'none' && (
        <RegionalThemeIndicator activeTheme={regionalTheme} onOverride={() => {}} onReset={resetRegionalTheme} isManualOverride={isManualRegionalOverride} />
      )}
      
      <Footer />
      <AboutModal isOpen={showAbout} onClose={() => setShowAbout(false)} />
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} currentTheme={theme} onThemeChange={setTheme} sheetTheme={sheetTheme} onSheetThemeChange={setSheetTheme} regionalTheme={regionalTheme} onRegionalThemeChange={setRegionalTheme} />
      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
}
