import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Check, ZoomIn, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { Species } from '@/types/bloombuilder';
import { api } from '@/services/api';

interface BotanicalPlate {
  id: string;
  url: string;
  artist: string;
  plate_number: string;
  year_range: string;
  source: string;
  source_url: string;
}

interface BotanicalPlateSelectionProps {
  species: Species;
  onComplete: (selectedPlates: string[]) => void;
  onBack: () => void;
}

export function BotanicalPlateSelection({ species, onComplete, onBack }: BotanicalPlateSelectionProps) {
  const [plates, setPlates] = useState<BotanicalPlate[]>([]);
  const [selectedPlates, setSelectedPlates] = useState<Set<string>>(new Set());
  const [zoomedPlate, setZoomedPlate] = useState<BotanicalPlate | null>(null);
  const [detailView, setDetailView] = useState<BotanicalPlate | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    const speciesId = parseInt(species.id);
    api.getSpeciesDetails(speciesId).then(data => {
      const botanicalPlates = data.images.botanical_plates.map((img: any) => ({
        id: img.id.toString(),
        url: img.url,
        artist: img.artist || 'Unknown artist',
        plate_number: img.plate_number || 'N/A',
        year_range: img.year_range || 'Date unknown',
        source: img.source || 'Unknown source',
        source_url: img.source_url || ''
      }));
      setPlates(botanicalPlates);
      setLoading(false);
    }).catch(err => {
      console.error('Failed to load botanical plates:', err);
      setLoading(false);
    });
  }, [species]);

  const togglePlate = (plateId: string) => {
    const newSelected = new Set(selectedPlates);
    if (newSelected.has(plateId)) {
      newSelected.delete(plateId);
    } else {
      newSelected.add(plateId);
    }
    setSelectedPlates(newSelected);
  };

  const handleNext = () => {
    if (currentIndex < plates.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleContinue = () => {
    onComplete(Array.from(selectedPlates));
  };

  if (loading) {
    return <div className="p-8 text-center">Loading botanical plates...</div>;
  }

  if (plates.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-600 mb-4">No botanical plates available for this species yet.</p>
        <div className="flex gap-4 justify-center">
          <Button variant="outline" onClick={onBack}>Back</Button>
          <Button onClick={() => onComplete([])}>Continue Anyway</Button>
        </div>
      </div>
    );
  }

  const currentPlate = plates[currentIndex];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Botanical Plate Selection</h2>
        <p className="text-gray-600 mb-4">
          Select diagnostic botanical illustrations. These historical plates show deconstructed orchid structures with scientific detail.
        </p>
        <Badge variant="outline" className="text-base">
          {selectedPlates.size} plate{selectedPlates.size !== 1 ? 's' : ''} selected
        </Badge>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 mb-8">
        {/* Carousel View */}
        <div>
          <div className="relative bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={currentPlate.url}
              alt={`Botanical plate ${currentPlate.plate_number}`}
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
              disabled={currentIndex === plates.length - 1}
            >
              <ChevronRight className="w-6 h-6" />
            </Button>

            {/* Plate Counter */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-3 py-1 rounded-full text-sm">
              {currentIndex + 1} / {plates.length}
            </div>

            {/* Selection Badge */}
            {selectedPlates.has(currentPlate.id) && (
              <div className="absolute top-4 right-4 bg-purple-600 text-white rounded-full p-2">
                <Check className="w-6 h-6" />
              </div>
            )}
          </div>

          {/* Carousel Controls */}
          <div className="flex gap-2 mt-4">
            <Button
              onClick={() => togglePlate(currentPlate.id)}
              variant={selectedPlates.has(currentPlate.id) ? 'default' : 'outline'}
              className={selectedPlates.has(currentPlate.id) ? 'bg-purple-600' : ''}
            >
              {selectedPlates.has(currentPlate.id) ? 'Selected' : 'Select This Plate'}
            </Button>
            <Button
              onClick={() => setZoomedPlate(currentPlate)}
              variant="outline"
            >
              <ZoomIn className="w-4 h-4 mr-2" /> Zoom on Callouts
            </Button>
            <Button
              onClick={() => setDetailView(currentPlate)}
              variant="ghost"
            >
              <Info className="w-4 h-4 mr-2" /> Full Details
            </Button>
          </div>
        </div>

        {/* Required Provenance Information */}
        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-bold text-lg mb-4 text-purple-900">Plate Information</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-semibold text-gray-700">Artist</p>
                <p className="text-gray-900">{currentPlate.artist}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Plate Number</p>
                <p className="text-gray-900">{currentPlate.plate_number}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Year Range</p>
                <p className="text-gray-900">{currentPlate.year_range}</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700">Source</p>
                <p className="text-gray-900">{currentPlate.source}</p>
              </div>
              {currentPlate.source_url && (
                <div>
                  <a
                    href={currentPlate.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-800 underline"
                  >
                    View Original →
                  </a>
                </div>
              )}
            </div>
          </Card>

          {/* Thumbnail Grid of All Plates */}
          <Card className="p-4">
            <h4 className="font-semibold mb-3">All Plates ({plates.length})</h4>
            <div className="grid grid-cols-3 gap-2">
              {plates.map((plate, idx) => {
                const isSelected = selectedPlates.has(plate.id);
                const isCurrent = idx === currentIndex;
                
                return (
                  <div
                    key={plate.id}
                    className={`relative cursor-pointer border-2 rounded overflow-hidden ${
                      isCurrent ? 'border-blue-500' : isSelected ? 'border-purple-600' : 'border-gray-300'
                    }`}
                    onClick={() => setCurrentIndex(idx)}
                  >
                    <img
                      src={plate.url}
                      alt={`Plate ${idx + 1}`}
                      className="w-full aspect-square object-cover"
                    />
                    {isSelected && (
                      <div className="absolute top-1 right-1 bg-purple-600 text-white rounded-full p-0.5">
                        <Check className="w-3 h-3" />
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
          Continue with {selectedPlates.size} plate{selectedPlates.size !== 1 ? 's' : ''}
        </Button>
      </div>

      {/* Zoom Modal */}
      <Dialog open={zoomedPlate !== null} onOpenChange={() => setZoomedPlate(null)}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] overflow-auto p-0">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle>Zoom View - Examine Details</DialogTitle>
          </DialogHeader>
          {zoomedPlate && (
            <div className="p-6">
              <div className="mb-4 flex gap-2">
                <Button onClick={() => setZoomLevel(1)} variant={zoomLevel === 1 ? 'default' : 'outline'} size="sm">
                  100%
                </Button>
                <Button onClick={() => setZoomLevel(1.5)} variant={zoomLevel === 1.5 ? 'default' : 'outline'} size="sm">
                  150%
                </Button>
                <Button onClick={() => setZoomLevel(2)} variant={zoomLevel === 2 ? 'default' : 'outline'} size="sm">
                  200%
                </Button>
                <Button onClick={() => setZoomLevel(3)} variant={zoomLevel === 3 ? 'default' : 'outline'} size="sm">
                  300%
                </Button>
              </div>
              <div className="overflow-auto border rounded-lg" style={{ maxHeight: '70vh' }}>
                <img
                  src={zoomedPlate.url}
                  alt="Zoomed plate"
                  style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}
                  className="max-w-none"
                />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailView !== null} onOpenChange={() => setDetailView(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Botanical Plate Details</DialogTitle>
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
                  <p className="font-semibold text-gray-700">Artist</p>
                  <p className="text-gray-900">{detailView.artist}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Plate Number</p>
                  <p className="text-gray-900">{detailView.plate_number}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Year Range</p>
                  <p className="text-gray-900">{detailView.year_range}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Source</p>
                  <p className="text-gray-900">{detailView.source}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
