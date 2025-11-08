import React, { useState, useEffect } from 'react';
import { BloomBuilderWidget } from './bloom/BloomBuilderWidget';
import { Sparkles, BookOpen, Palette } from 'lucide-react';

interface ContributorStats {
  total_contributors: number;
  years_span: number;
  earliest_year: number;
  latest_year: number;
  images_available: number;
  species_available: number;
}

const AppLayout: React.FC = () => {
  const [stats, setStats] = useState<ContributorStats | null>(null);

  useEffect(() => {
    fetch('/bloombuilder/api/contributors/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Failed to load stats:', err));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-lavender-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-purple-600 to-purple-700 text-white">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative max-w-7xl mx-auto px-6 py-20 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-yellow-300" />
            <h1 className="text-5xl md:text-6xl font-bold">
              The Orchid Continuum
            </h1>
            <Sparkles className="w-8 h-8 text-yellow-300" />
          </div>
          <p className="text-2xl md:text-3xl mb-4 text-purple-50 font-semibold">
            Verify Species Through History
          </p>
          <p className="text-lg md:text-xl mb-8 text-purple-100 max-w-3xl mx-auto">
            Learn botanical identification by comparing herbarium specimens, dichotomous keys, and historical plates — honoring {stats?.total_contributors || 587}+ contributors across {stats?.years_span || 43} years of research.
          </p>
          <div className="flex flex-wrap gap-4 justify-center text-sm">
            <div className="bg-white/20 backdrop-blur-sm px-6 py-3 rounded-full">
              {stats?.total_contributors || 587}+ Contributors
            </div>
            <div className="bg-white/20 backdrop-blur-sm px-6 py-3 rounded-full">
              {stats?.years_span || 43} Years ({stats?.earliest_year || 1982}-{stats?.latest_year || 2025})
            </div>
            <div className="bg-white/20 backdrop-blur-sm px-6 py-3 rounded-full">
              {stats?.species_available || 25} Species • {stats?.images_available?.toLocaleString() || '11,717'} Images
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">How BloomBuilder Works</h2>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Select a species → Compare herbarium specimens → Label structures using dichotomous keys and glossary → Validate through historical plates → Build and save your verified orchid while honoring contributors across time.
          </p>
        </div>

        {/* Widget Display */}
        <div className="flex justify-center">
          <BloomBuilderWidget />
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="font-semibold text-xl mb-2">Select & Compare</h3>
            <p className="text-muted-foreground">
              Choose from 25 species, then scroll through herbarium specimens and botanical plates to select the ones you'll study
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="font-semibold text-xl mb-2">Label & Learn</h3>
            <p className="text-muted-foreground">
              Apply labels to flower structures using dichotomous keys and glossary definitions — learn botanical terminology through hands-on validation
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Palette className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="font-semibold text-xl mb-2">Build & Credit</h3>
            <p className="text-muted-foreground">
              Watch your labeled flower assemble, apply style filters, and save your work while honoring 587+ contributors across 43 years
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppLayout;

