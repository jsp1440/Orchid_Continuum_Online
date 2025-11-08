import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAppContext, SpurLength, PetalColor, TraitKey } from '@/contexts/AppContext';
import { Upload, Image as ImageIcon, X, Filter } from 'lucide-react';
import { traitGalleryImages } from '@/data/images';
import { ImageGallery } from './ImageGallery';
import { ComparisonView } from './ComparisonView';


export function TraitImageLibrary() {
  const { traitImageMappings, setTraitImageMapping } = useAppContext();
  const [selectedTrait, setSelectedTrait] = useState<TraitKey | null>(null);
  const [spurFilter, setSpurFilter] = useState<SpurLength | 'all'>('all');
  const [colorFilter, setColorFilter] = useState<PetalColor | 'all'>('all');
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);


  const spurLengths: SpurLength[] = ['short', 'long'];
  const petalColors: PetalColor[] = ['pink', 'white', 'yellow'];

  const traitCombinations: TraitKey[] = spurLengths.flatMap(spur =>
    petalColors.map(color => `${spur}-${color}` as TraitKey)
  );

  const filteredGalleryImages = traitGalleryImages.filter(img => {
    if (spurFilter !== 'all' && img.spurLength !== spurFilter) return false;
    if (colorFilter !== 'all' && img.petalColor !== colorFilter) return false;
    return true;
  });

  const handleImageUpload = (traitKey: TraitKey, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const imageUrl = e.target?.result as string;
      setTraitImageMapping(traitKey, imageUrl);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = (traitKey: TraitKey) => {
    setTraitImageMapping(traitKey, '');
  };

  const handleGallerySelect = (traitKey: TraitKey, imageUrl: string) => {
    setTraitImageMapping(traitKey, imageUrl);
    setSelectedTrait(null);
  };


  const handleToggleComparison = (imageId: string) => {
    setComparisonIds(prev => 
      prev.includes(imageId) 
        ? prev.filter(id => id !== imageId)
        : [...prev, imageId]
    );
  };

  const handleRemoveFromComparison = (imageId: string) => {
    setComparisonIds(prev => prev.filter(id => id !== imageId));
  };

  const handleClearComparison = () => {
    setComparisonIds([]);
  };

  const selectedComparisonImages = traitGalleryImages.filter(img => 
    comparisonIds.includes(img.id)
  );

  return (
    <Card className="p-4">
      <h3 className="font-semibold text-sm mb-3">Trait Image Library</h3>
      <p className="text-xs text-muted-foreground mb-4">
        Assign images to each trait combination for crossfade effects.
      </p>

      <Tabs defaultValue="manage" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="manage">Manage</TabsTrigger>
          <TabsTrigger value="gallery">Gallery</TabsTrigger>
          <TabsTrigger value="compare">
            Compare {comparisonIds.length > 0 && `(${comparisonIds.length})`}
          </TabsTrigger>
        </TabsList>


        <TabsContent value="manage" className="space-y-3">
          {traitCombinations.map(traitKey => {
            const [spur, color] = traitKey.split('-');
            const hasImage = !!traitImageMappings[traitKey];

            return (
              <div key={traitKey} className="border rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-medium capitalize">
                    {spur} Spur • {color}
                  </Label>
                  {hasImage && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveImage(traitKey)}
                      className="h-6 w-6 p-0"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>

                {hasImage && (
                  <div className="relative w-full h-20 rounded overflow-hidden bg-muted">
                    <img
                      src={traitImageMappings[traitKey]}
                      alt={`${traitKey}`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedTrait(traitKey)}
                    className="flex-1 h-8 text-xs"
                  >
                    <ImageIcon className="h-3 w-3 mr-1" />
                    Gallery
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => document.getElementById(`upload-${traitKey}`)?.click()}
                    className="flex-1 h-8 text-xs"
                  >
                    <Upload className="h-3 w-3 mr-1" />
                    Upload
                  </Button>
                  <input
                    id={`upload-${traitKey}`}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleImageUpload(traitKey, e)}
                  />
                </div>
              </div>
            );
          })}
        </TabsContent>

        <TabsContent value="gallery" className="space-y-3">
          {selectedTrait ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-medium capitalize">
                  Select for: {selectedTrait.replace('-', ' spur • ')}
                </Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedTrait(null)}
                  className="h-6 text-xs"
                >
                  Back
                </Button>
              </div>
              <ImageGallery
                images={filteredGalleryImages}
                onSelectImage={(url) => handleGallerySelect(selectedTrait, url)}
                selectedImageUrl={traitImageMappings[selectedTrait]}
              />
            </div>
          ) : (
            <div>
              <div className="flex gap-2 mb-3">
                <Select value={spurFilter} onValueChange={(v) => setSpurFilter(v as any)}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Spurs</SelectItem>
                    <SelectItem value="short">Short</SelectItem>
                    <SelectItem value="long">Long</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={colorFilter} onValueChange={(v) => setColorFilter(v as any)}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Colors</SelectItem>
                    <SelectItem value="pink">Pink</SelectItem>
                    <SelectItem value="white">White</SelectItem>
                    <SelectItem value="yellow">Yellow</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Select a trait combination from the Manage tab to assign an image.
              </p>
              <ImageGallery
                images={filteredGalleryImages}
                onSelectImage={() => {}}
              />
            </div>
          )}
        </TabsContent>

        <TabsContent value="compare" className="space-y-3">
          <div className="space-y-3">
            <div className="flex gap-2 mb-3">
              <Select value={spurFilter} onValueChange={(v) => setSpurFilter(v as any)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Spurs</SelectItem>
                  <SelectItem value="short">Short</SelectItem>
                  <SelectItem value="long">Long</SelectItem>
                </SelectContent>
              </Select>
              <Select value={colorFilter} onValueChange={(v) => setColorFilter(v as any)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Colors</SelectItem>
                  <SelectItem value="pink">Pink</SelectItem>
                  <SelectItem value="white">White</SelectItem>
                  <SelectItem value="yellow">Yellow</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <p className="text-xs text-muted-foreground mb-3">
              Click on images to add them to comparison. Selected images will appear in the comparison table below.
            </p>

            <ImageGallery
              images={filteredGalleryImages}
              onSelectImage={() => {}}
              comparisonMode={true}
              selectedForComparison={comparisonIds}
              onToggleComparison={handleToggleComparison}
            />

            {comparisonIds.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <ComparisonView
                  selectedImages={selectedComparisonImages}
                  onRemoveImage={handleRemoveFromComparison}
                  onClearAll={handleClearComparison}
                />
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
}
