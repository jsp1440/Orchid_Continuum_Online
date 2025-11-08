import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Check, ZoomIn, Info } from 'lucide-react';
import { Species } from '@/types/bloombuilder';
import { api } from '@/services/api';

interface Photo {
  id: string;
  url: string;
  photographer: string;
  license: string;
  source: string;
}

interface PhotoComparisonProps {
  species: Species;
  onComplete: (selectedPhotos: string[], startingPhoto: string) => void;
}

export function PhotoComparison({ species, onComplete }: PhotoComparisonProps) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [selectedPhotos, setSelectedPhotos] = useState<Set<string>>(new Set());
  const [startingPhoto, setStartingPhoto] = useState<string | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [metadataView, setMetadataView] = useState<Photo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch photos for this species
    const speciesId = parseInt(species.id);
    api.getSpeciesDetails(speciesId).then(data => {
      const livingPhotos = data.images.living_photos.map((img: any) => ({
        id: img.id.toString(),
        url: img.url,
        photographer: img.photographer || 'Unknown',
        license: img.license || 'Unknown',
        source: img.source || 'Unknown'
      }));
      setPhotos(livingPhotos);
      setLoading(false);
    }).catch(err => {
      console.error('Failed to load photos:', err);
      setLoading(false);
    });
  }, [species]);

  const togglePhoto = (photoId: string) => {
    const newSelected = new Set(selectedPhotos);
    if (newSelected.has(photoId)) {
      newSelected.delete(photoId);
      if (startingPhoto === photoId) {
        setStartingPhoto(null);
      }
    } else {
      newSelected.add(photoId);
    }
    setSelectedPhotos(newSelected);
  };

  const handleSetStarting = (photoId: string) => {
    if (!selectedPhotos.has(photoId)) {
      togglePhoto(photoId);
    }
    setStartingPhoto(photoId);
  };

  const handleContinue = () => {
    if (selectedPhotos.size > 0 && startingPhoto) {
      onComplete(Array.from(selectedPhotos), startingPhoto);
    }
  };

  const selectedArray = Array.from(selectedPhotos);
  const canContinue = selectedPhotos.size > 0 && startingPhoto !== null;

  if (loading) {
    return <div className="p-8 text-center">Loading photos...</div>;
  }

  if (photos.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-600 mb-4">No photos available for this species yet.</p>
        <Button onClick={() => onComplete([], '')}>Continue Anyway</Button>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Photo Comparison</h2>
        <p className="text-gray-600 mb-4">
          Select multiple photos to compare. Choose one as your "Starting Photo" to validate.
        </p>
        <div className="flex gap-4 items-center">
          <Badge variant="outline" className="text-base">
            {selectedPhotos.size} photo{selectedPhotos.size !== 1 ? 's' : ''} selected
          </Badge>
          {startingPhoto && (
            <Badge variant="default" className="bg-purple-600 text-base">
              Starting Photo Set
            </Badge>
          )}
          {selectedArray.length > 1 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCompareMode(true)}
            >
              <ZoomIn className="w-4 h-4 mr-2" />
              Side-by-Side Compare
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
        {photos.map((photo) => {
          const isSelected = selectedPhotos.has(photo.id);
          const isStarting = startingPhoto === photo.id;
          
          return (
            <Card
              key={photo.id}
              className={`overflow-hidden cursor-pointer transition-all ${
                isSelected ? 'ring-2 ring-purple-600' : ''
              } ${isStarting ? 'ring-4 ring-green-600' : ''}`}
              onClick={() => togglePhoto(photo.id)}
            >
              <div className="relative aspect-square">
                <img
                  src={photo.url}
                  alt={`Photo by ${photo.photographer}`}
                  className="w-full h-full object-cover"
                />
                {isSelected && (
                  <div className="absolute top-2 right-2 bg-purple-600 text-white rounded-full p-1">
                    <Check className="w-4 h-4" />
                  </div>
                )}
                {isStarting && (
                  <div className="absolute top-2 left-2 bg-green-600 text-white text-xs font-bold px-2 py-1 rounded">
                    STARTING
                  </div>
                )}
              </div>
              <div className="p-3 space-y-2">
                <p className="text-xs text-gray-600 truncate">
                  📷 {photo.photographer}
                </p>
                {isSelected && !isStarting && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSetStarting(photo.id);
                    }}
                  >
                    Set as Starting Photo
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  className="w-full text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMetadataView(photo);
                  }}
                >
                  <Info className="w-3 h-3 mr-1" /> View EXIF
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="flex justify-end">
        <Button
          onClick={handleContinue}
          disabled={!canContinue}
          className="bg-purple-600 hover:bg-purple-700"
        >
          Continue with {selectedPhotos.size} photo{selectedPhotos.size !== 1 ? 's' : ''}
        </Button>
      </div>

      {/* Side-by-Side Comparison Modal */}
      <Dialog open={compareMode} onOpenChange={setCompareMode}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Side-by-Side Comparison</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            {selectedArray.slice(0, 4).map((photoId) => {
              const photo = photos.find(p => p.id === photoId);
              if (!photo) return null;
              
              return (
                <div key={photoId} className="space-y-2">
                  <img
                    src={photo.url}
                    alt={`Photo by ${photo.photographer}`}
                    className="w-full rounded-lg"
                  />
                  <p className="text-sm text-gray-600">
                    📷 {photo.photographer}
                  </p>
                </div>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>

      {/* Metadata/EXIF Modal */}
      <Dialog open={metadataView !== null} onOpenChange={() => setMetadataView(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Photo Metadata</DialogTitle>
          </DialogHeader>
          {metadataView && (
            <div className="space-y-3">
              <img
                src={metadataView.url}
                alt="Preview"
                className="w-full rounded-lg"
              />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-semibold text-gray-700">Photographer</p>
                  <p className="text-gray-600">{metadataView.photographer}</p>
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Source</p>
                  <p className="text-gray-600">{metadataView.source}</p>
                </div>
                <div className="col-span-2">
                  <p className="font-semibold text-gray-700">License</p>
                  <p className="text-gray-600">{metadataView.license}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
