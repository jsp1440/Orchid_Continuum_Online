import React from 'react';
import { OrchidSpecies, SheetTheme } from '../../types/orchid';
import { CultureInfo } from './CultureInfo';
import { PollinatorSection } from './PollinatorSection';
import { CompanionSection } from './CompanionSection';
import { MapView } from './MapView';
import { ClimateHeatmap } from './ClimateHeatmap';
import { PDFExportOptions } from './PDFExportOptions';
import { pollinators, companions } from '../../data/orchidData';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../hooks/use-toast';
import { supabase } from '../../lib/supabase';

interface Props {
  species: OrchidSpecies;
  sections: any;
  theme: SheetTheme;
  location: any;
  onPrint: () => void;
  onShare: () => void;
}

export const GeneratedSheet: React.FC<Props> = ({ species, sections, theme, location, onPrint, onShare }) => {
  const { user } = useAuth();
  const { toast } = useToast();

  const handleSave = async () => {
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in to save culture sheets.",
        variant: "destructive",
      });
      return;
    }

    try {
      const sheetData = {
        species,
        sections,
        theme,
        location,
      };

      const { error } = await supabase
        .from('saved_culture_sheets')
        .insert({
          user_id: user.id,
          orchid_name: species.scientificName,
          sheet_data: sheetData,
        });

      if (error) throw error;

      // Send confirmation email
      try {
        await supabase.functions.invoke('send-culture-sheet-confirmation', {
          body: {
            email: user.email,
            species: species.scientificName,
            theme: theme,
            location: location?.name || 'Not specified',
            userId: user.id,
          },
        });
      } catch (emailError) {
        console.error('Email notification failed:', emailError);
        // Don't fail the save if email fails
      }

      toast({
        title: "Success!",
        description: "Culture sheet saved to your dashboard. Check your email for confirmation.",
      });
    } catch (error: any) {
      console.error('Error saving culture sheet:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to save culture sheet. Please try again.",
        variant: "destructive",
      });
    }
  };


  return (
    <div>
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Export Options</h3>
        <PDFExportOptions elementId="culture-sheet-content" filename={`${species.scientificName.replace(/\s+/g, '_')}_culture_sheet.pdf`} />
      </div>
      <div id="culture-sheet-content" className="max-w-5xl mx-auto bg-white rounded-2xl shadow-2xl p-8 md:p-12">
        <div className="flex flex-col md:flex-row gap-8 mb-8 pb-8 border-b-2 border-gray-100">
          <img src={species.imageUrl} alt={species.scientificName} className="w-full md:w-64 h-64 object-cover rounded-xl shadow-lg" />
          <div className="flex-1">
            <h2 className="text-4xl font-bold text-gray-900 mb-2 italic">{species.scientificName}</h2>
            <p className="text-xl text-gray-600 mb-4">{species.commonName}</p>
            <div className="flex gap-3 mb-4">
              <span className="px-4 py-2 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-full text-sm font-medium">{species.genus}</span>
              <span className="px-4 py-2 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">{species.region}</span>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={handleSave} className="px-6 py-2.5 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity font-medium">Save</button>

              <button onClick={onPrint} className="px-6 py-2.5 bg-gray-700 text-white rounded-lg hover:opacity-90 transition-opacity font-medium">Print</button>
              <button onClick={onShare} className="px-6 py-2.5 bg-[var(--color-accent)] text-white rounded-lg hover:opacity-90 transition-opacity font-medium">Share</button>
            </div>
          </div>
        </div>
        <CultureInfo sections={sections} />
        {sections.maps && (
          <div className="mt-8 space-y-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Native Distribution & Climate</h3>
            <MapView species={species} />
            <ClimateHeatmap species={species} />
          </div>
        )}
        {sections.pollinators && <PollinatorSection pollinators={pollinators} />}
        {sections.companions && <CompanionSection companions={companions} />}
        <div className="mt-8 pt-8 border-t border-gray-200 text-sm text-gray-600">
          <p className="italic">Educational guidance only. Always observe your plant and adjust care accordingly.</p>
        </div>
      </div>
    </div>
  );
};
