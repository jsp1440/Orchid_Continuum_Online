import { ImageMetadata } from '@/types/bloombuilder';
import { Card } from '@/components/ui/card';
import { Calendar, MapPin, User, Building2 } from 'lucide-react';

interface ImageCardProps {
  image: ImageMetadata;
  selected?: boolean;
  onClick: () => void;
}

export function ImageCard({ image, selected, onClick }: ImageCardProps) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-lg ${
        selected ? 'ring-2 ring-green-600' : ''
      }`}
      onClick={onClick}
    >
      <div className="aspect-[4/3] overflow-hidden rounded-t-lg">
        <img
          src={image.url}
          alt="Orchid specimen"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="p-3 space-y-2 text-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Calendar className="w-4 h-4" />
          <span>{image.date}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <MapPin className="w-4 h-4" />
          <span>{image.location}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <User className="w-4 h-4" />
          <span>{image.contributor}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <Building2 className="w-4 h-4" />
          <span className="text-xs">{image.institution}</span>
        </div>
      </div>
    </Card>
  );
}
