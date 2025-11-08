import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Check, Pin, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { Species } from '@/types/bloombuilder';
import { api } from '@/services/api';

interface HerbariumSheet {
  id: string;
  url: string;
  collector: string;
  collection_date: string;
  locality: string;
  institution: string;
  catalog_number: string;
  source_url: string;
}

interface HerbariumSelectionProps {
  species: Species;
  onComplete: (selectedSheets: string[]) => void;
  onBack: () => void;
}

export function HerbariumSelection({ species, onComplete, onBack }: HerbariumSelectionProps) {
  const [sheets, setSheets] = useState<HerbariumSheet[]>([]);
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());
  const [pinnedSheet, setPinnedSheet] = useState<string | null>(null);
  const [detailView, setDetailView] = useState<HerbariumSheet | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const speciesId = parseInt(species.id);
    api.getSpeciesDetails(speciesId).then(data => {
      const herbariumSheets = data.images.herbarium_sheets.map((img: any) => ({
        id: img.id.toString(),
        url: img.url,
        collector: img.collector || 'Unknown collector',
        collection_date: img.collection_date || 'Date unknown',
        locality: img.locality || 'Locality unknown',
        institution: img.institution || 'Unknown institution',
        catalog_number: img.catalog_number || 'N/A',
        source_url: img.source_url || ''
      }));
      setSheets(herbariumSheets);
      setLoading(false);
    }).catch(err => {
      console.error('Failed to load herbarium sheets:', err);
      setLoading(false);
    });
  }, [species]);

  const toggleSheet = (sheetId: string) => {
    const newSelected = new Set(selectedSheets);
    if (newSelected.has(sheetId)) {
      newSelected.delete(sheetId);
      if (pinnedSheet === sheetId) {
        setPinnedSheet(null);
      }
    } else {
      newSelected.add(sheetId);
    }
    setSelectedSheets(newSelected);
  };

  const handlePin = (sheetId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!selectedSheets.has(sheetId)) {
      toggleSheet(sheetId);
    }
    setPinnedSheet(sheetId === pinnedSheet ? null : sheetId);
  };

  const handleNext = () => {
    if (currentIndex < sheets.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleContinue = () => {
    onComplete(Array.from(selectedSheets));
  };

  if (loading) {
    return <div className="p-8 text-center">Loading herbarium sheets...</div>;
  }

  if (sheets.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-600 mb-4">No herbarium sheets available for this species yet.</p>
        <div className="flex gap-4 justify-center">
          <Button variant="outline" onClick={onBack}>Back</Button>
          <Button onClick={() => onComplete([])}>Continue Anyway</Button>
        </div>
      </div>
    );
  }

  const currentSheet = sheets[currentIndex];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Herbarium Sheet Selection</h2>
        <p className="text-gray-600 mb-4">
          Select one or more herbarium specimens. These historical sheets show pressed orchids with detailed collection data.
        </p>
        <Badge variant="outline" className="text-base">
          {selectedSheets.size} sheet{selectedSheets.size !== 1 ? 's' : ''} selected
        </Badge>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 mb-8">
        {/* Carousel View */}
        <div>
          <div className="relative bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={currentSheet.url}
              alt={`Herbarium sheet ${currentSheet.catalog_number}`}
              className="w-full h-[500px] object-contain"
            />
            
            {/* Navigation Arrows */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white"
              onClick={handlePrev}
              disabled={currentIndex === 0}
            >
              <ChevronLeft className="w-6 h-6" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white"
              onClick={handleNext}
              disabled={currentIndex === sheets.length - 1}
            >
              <ChevronRight className="w-6 h-6" />
            </Button>

            {/* Sheet Counter */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-3 py-1 rounded-full text-sm">
              {currentIndex + 1} / {sheets.length}
            </div>

            {/* Selection Badge */}
            {selectedSheets.has(currentSheet.id) && (
              <div className="absolute top-4 right-4 bg-purple-600 text-white rounded-full p-2">
                <Check className="w-6 h-6" />
              </div>
            )}

            {/* Pinned Badge */}
            {pinnedSheet === currentSheet.id && (
              <div className="absolute top-4 left-4 bg-green-600 text-white text-sm font-bold px-3 py-2 rounded">
                PINNED
              </div>
            )}
          </div>

          {/* Carousel Controls */}
          <div className="flex gap-2 mt-4">
            <Button
              onClick={() => toggleSheet(currentSheet.id)}
              variant={selectedSheets.has(currentSheet.id) ? 'default' : 'outline'}
              className={selectedSheets.has(currentSheet.id) ? 'bg-purple-600' : ''}
            >
              {selectedSheets.has(currentSheet.id) ? 'Selected' : 'Select This Sheet'}
            </Button>
            <Button
              onClick={(e) => handlePin(currentSheet.id, e)}
              variant="outline"
            >
              <Pin className={`w-4 h-4 mr-2 ${pinnedSheet === currentSheet.id ? 'fill-current' : ''}`} />
              {pinnedSheet === currentSheet.id ? 'Unpin' : 'Pin'}
            </Button>
            <Button
              onClick={() => setDetailView(currentSheet)}
              variant="ghost"
            >
              <Info className="w-4 h-4 mr-2" /> Full Details
            </Button>
          </div>
        </div>

        {/* Required Provenance Information */}
        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-bold text-lg mb-4 text-purple-900">Specimen Information</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-semibold text-gray-700">Collector</p>
                <p className="text-gray-900">{currentSheet.collector}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Collection Date</p>
                <p className="text-gray-900">{currentSheet.collection_date}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Locality</p>
                <p className="text-gray-900">{currentSheet.locality}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Institution</p>
                <p className="text-gray-900">{currentSheet.institution}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Catalog Number</p>
                <p className="text-gray-900">{currentSheet.catalog_number}</p>
              </div>
              {currentSheet.source_url && (
                <div>
                  <a
                    href={currentSheet.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-800 underline"
                  >
                    View at Institution →
                  </a>
                </div>
              )}
            </div>
          </Card>

          {/* Thumbnail Grid of All Sheets */}
          <Card className="p-4">
            <h4 className="font-semibold mb-3">All Sheets ({sheets.length})</h4>
            <div className="grid grid-cols-3 gap-2">
              {sheets.map((sheet, idx) => {
                const isSelected = selectedSheets.has(sheet.id);
                const isPinned = pinnedSheet === sheet.id;
                const isCurrent = idx === currentIndex;
                
                return (
                  <div
                    key={sheet.id}
                    className={`relative cursor-pointer border-2 rounded overflow-hidden ${
                      isCurrent ? 'border-blue-500' : isSelected ? 'border-purple-600' : 'border-gray-300'
                    }`}
                    onClick={() => setCurrentIndex(idx)}
                  >
                    <img
                      src={sheet.url}
                      alt={`Sheet ${idx + 1}`}
                      className="w-full aspect-square object-cover"
                    />
                    {isSelected && (
                      <div className="absolute top-1 right-1 bg-purple-600 text-white rounded-full p-0.5">
                        <Check className="w-3 h-3" />
                      </div>
                    )}
                    {isPinned && (
                      <div className="absolute top-1 left-1 bg-green-600 text-white rounded-full p-0.5">
                        <Pin className="w-3 h-3 fill-current" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          className="bg-purple-600 hover:bg-purple-700"
        >
          Continue with {selectedSheets.size} sheet{selectedSheets.size !== 1 ? 's' : ''}
        </Button>
      </div>

      {/* Detail Modal */}
      <Dialog open={detailView !== null} onOpenChange={() => setDetailView(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Herbarium Sheet Details</DialogTitle>
          </DialogHeader>
          {detailView && (
            <div className="space-y-4">
              <img
                src={detailView.url}
                alt="Full resolution"
                className="w-full rounded-lg"
              />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-semibold text-gray-700">Collector</p>
                  <p className="text-gray-900">{detailView.collector}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Date</p>
                  <p className="text-gray-900">{detailView.collection_date}</p>
                </div>
                <div className="col-span-2">
                  <p className="font-semibold text-gray-700">Locality</p>
                  <p className="text-gray-900">{detailView.locality}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Institution</p>
                  <p className="text-gray-900">{detailView.institution}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Catalog</p>
                  <p className="text-gray-900">{detailView.catalog_number}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
