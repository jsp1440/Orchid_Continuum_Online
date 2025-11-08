import { TraitImageMetadata } from '@/types/bloombuilder';
import { Button } from '@/components/ui/button';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Check, Info, Plus } from 'lucide-react';

interface ImageGalleryProps {
  images: TraitImageMetadata[];
  onSelectImage: (imageUrl: string) => void;
  selectedImageUrl?: string;
  comparisonMode?: boolean;
  selectedForComparison?: string[];
  onToggleComparison?: (imageId: string) => void;
}

export function ImageGallery({ 
  images, 
  onSelectImage, 
  selectedImageUrl,
  comparisonMode = false,
  selectedForComparison = [],
  onToggleComparison
}: ImageGalleryProps) {
  const isSelected = (imageId: string) => selectedForComparison.includes(imageId);

  return (
    <div className="grid grid-cols-2 gap-2">
      {images.map((image) => (
        <HoverCard key={image.id} openDelay={200}>
          <HoverCardTrigger asChild>
            <div className="relative group">
              <div className="relative w-full h-24 rounded overflow-hidden bg-muted border-2 border-transparent hover:border-primary transition-colors cursor-pointer">
                <img
                  src={image.url}
                  alt={image.name}
                  className="w-full h-full object-cover"
                  onClick={() => comparisonMode ? onToggleComparison?.(image.id) : onSelectImage(image.url)}
                />
                {!comparisonMode && selectedImageUrl === image.url && (
                  <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                    <Check className="h-6 w-6 text-primary" />
                  </div>
                )}
                {comparisonMode && isSelected(image.id) && (
                  <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                    <Check className="h-6 w-6 text-primary" />
                  </div>
                )}
                {comparisonMode && !isSelected(image.id) && (
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 flex items-center justify-center transition-colors">
                    <Plus className="h-6 w-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                )}
                <div className="absolute top-1 right-1 bg-background/80 rounded-full p-1">
                  <Info className="h-3 w-3 text-muted-foreground" />
                </div>
              </div>
              <p className="text-xs mt-1 truncate">{image.name}</p>
            </div>
          </HoverCardTrigger>
          <HoverCardContent className="w-80" side="left">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">{image.name}</h4>
              {image.description && (
                <p className="text-xs text-muted-foreground">{image.description}</p>
              )}
              {image.characteristics && (
                <div>
                  <p className="text-xs font-medium">Characteristics:</p>
                  <p className="text-xs text-muted-foreground">{image.characteristics}</p>
                </div>
              )}
              {image.pollinatorType && (
                <div>
                  <p className="text-xs font-medium">Pollinators:</p>
                  <p className="text-xs text-muted-foreground">{image.pollinatorType}</p>
                </div>
              )}
              {image.evolutionaryNotes && (
                <div>
                  <p className="text-xs font-medium">Evolutionary Notes:</p>
                  <p className="text-xs text-muted-foreground">{image.evolutionaryNotes}</p>
                </div>
              )}
            </div>
          </HoverCardContent>
        </HoverCard>
      ))}
    </div>
  );
}

