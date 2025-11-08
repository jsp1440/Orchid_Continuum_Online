import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { ChevronDown } from 'lucide-react';

interface ExportSettings {
  format: 'png' | 'jpg' | 'svg';
  quality: number;
  multiplier: number;
}

interface ExportSettingsDropdownProps {
  onExport: (settings: ExportSettings) => void;
}

export function ExportSettingsDropdown({ onExport }: ExportSettingsDropdownProps) {
  const [format, setFormat] = useState<'png' | 'jpg' | 'svg'>('png');
  const [quality, setQuality] = useState(90);
  const [multiplier, setMultiplier] = useState(2);
  const [open, setOpen] = useState(false);

  const handleExport = () => {
    onExport({ format, quality: quality / 100, multiplier });
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <ChevronDown className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72">
        <div className="space-y-4">
          <div>
            <Label className="text-sm font-semibold">Format</Label>
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as any)} className="mt-2">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="png" id="png" />
                <Label htmlFor="png" className="font-normal">PNG (Lossless)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="jpg" id="jpg" />
                <Label htmlFor="jpg" className="font-normal">JPG (Compressed)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="svg" id="svg" />
                <Label htmlFor="svg" className="font-normal">SVG (Vector)</Label>
              </div>
            </RadioGroup>
          </div>

          {format === 'jpg' && (
            <div>
              <Label className="text-sm font-semibold">Quality: {quality}%</Label>
              <Slider value={[quality]} onValueChange={(v) => setQuality(v[0])} min={1} max={100} step={1} className="mt-2" />
            </div>
          )}

          <div>
            <Label className="text-sm font-semibold">Resolution</Label>
            <RadioGroup value={multiplier.toString()} onValueChange={(v) => setMultiplier(Number(v))} className="mt-2">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="1" id="1x" />
                <Label htmlFor="1x" className="font-normal">1x (Web)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="2" id="2x" />
                <Label htmlFor="2x" className="font-normal">2x (Standard)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="4" id="4x" />
                <Label htmlFor="4x" className="font-normal">4x (Print)</Label>
              </div>
            </RadioGroup>
          </div>

          <Button onClick={handleExport} className="w-full bg-green-600 hover:bg-green-700">
            Export
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
