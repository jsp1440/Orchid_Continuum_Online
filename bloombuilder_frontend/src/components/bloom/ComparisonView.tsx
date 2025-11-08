import { TraitImageMetadata } from '@/types/bloombuilder';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, Download, FileText } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { exportComparisonToPDF, exportComparisonToCSV } from '@/lib/exportHelpers';
import { useState } from 'react';


interface ComparisonViewProps {
  selectedImages: TraitImageMetadata[];
  onRemoveImage: (imageId: string) => void;
  onClearAll: () => void;
}

export function ComparisonView({ selectedImages, onRemoveImage, onClearAll }: ComparisonViewProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      await exportComparisonToPDF(selectedImages);
    } catch (error) {
      console.error('Error exporting PDF:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportCSV = () => {
    try {
      exportComparisonToCSV(selectedImages);
    } catch (error) {
      console.error('Error exporting CSV:', error);
    }
  };

  if (selectedImages.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        Select 2 or more images from the gallery to compare their traits and evolutionary adaptations.
      </div>
    );
  }

  // Helper to check if values differ across selected images
  const hasDifference = (field: keyof TraitImageMetadata) => {
    const values = selectedImages.map(img => img[field]);
    return new Set(values).size > 1;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h4 className="text-sm font-semibold">Comparing {selectedImages.length} Orchids</h4>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleExportPDF}
            disabled={isExporting}
            className="h-7 text-xs"
          >
            <Download className="h-3 w-3 mr-1" />
            Export PDF
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleExportCSV}
            className="h-7 text-xs"
          >
            <FileText className="h-3 w-3 mr-1" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={onClearAll} className="h-7 text-xs">
            Clear All
          </Button>
        </div>
      </div>


      {/* Image Previews */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {selectedImages.map((image) => (
          <div key={image.id} className="relative group">
            <img
              src={image.url}
              alt={image.name}
              className="w-full h-24 object-cover rounded border"
            />
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onRemoveImage(image.id)}
              className="absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X className="h-3 w-3" />
            </Button>
            <p className="text-xs mt-1 truncate">{image.name}</p>
          </div>
        ))}
      </div>

      {/* Comparison Table */}
      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-32">Trait</TableHead>
              {selectedImages.map((image) => (
                <TableHead key={image.id} className="text-xs">{image.name}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow className={hasDifference('spurLength') ? 'bg-yellow-50 dark:bg-yellow-950/20' : ''}>
              <TableCell className="font-medium text-xs">Spur Length</TableCell>
              {selectedImages.map((image) => (
                <TableCell key={image.id} className="text-xs capitalize">{image.spurLength}</TableCell>
              ))}
            </TableRow>
            <TableRow className={hasDifference('petalColor') ? 'bg-yellow-50 dark:bg-yellow-950/20' : ''}>
              <TableCell className="font-medium text-xs">Petal Color</TableCell>
              {selectedImages.map((image) => (
                <TableCell key={image.id} className="text-xs capitalize">{image.petalColor}</TableCell>
              ))}
            </TableRow>
            <TableRow className={hasDifference('characteristics') ? 'bg-yellow-50 dark:bg-yellow-950/20' : ''}>
              <TableCell className="font-medium text-xs">Characteristics</TableCell>
              {selectedImages.map((image) => (
                <TableCell key={image.id} className="text-xs">{image.characteristics || 'N/A'}</TableCell>
              ))}
            </TableRow>
            <TableRow className={hasDifference('pollinatorType') ? 'bg-yellow-50 dark:bg-yellow-950/20' : ''}>
              <TableCell className="font-medium text-xs">Pollinator Type</TableCell>
              {selectedImages.map((image) => (
                <TableCell key={image.id} className="text-xs">{image.pollinatorType || 'N/A'}</TableCell>
              ))}
            </TableRow>
            <TableRow className={hasDifference('evolutionaryNotes') ? 'bg-yellow-50 dark:bg-yellow-950/20' : ''}>
              <TableCell className="font-medium text-xs">Evolutionary Notes</TableCell>
              {selectedImages.map((image) => (
                <TableCell key={image.id} className="text-xs">{image.evolutionaryNotes || 'N/A'}</TableCell>
              ))}
            </TableRow>
          </TableBody>
        </Table>
      </Card>

      <div className="text-xs text-muted-foreground">
        <p>💡 Rows with yellow highlighting indicate differences between the selected orchids.</p>
      </div>
    </div>
  );
}
