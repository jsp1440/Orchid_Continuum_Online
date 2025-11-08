import { Canvas } from './Canvas';
import { ToolPanel } from './ToolPanel';
import { Species } from '@/types/bloombuilder';

interface WorkbenchProps {
  imageUrl: string;
  onSave: () => void;
  species?: Species | null;
}

export function Workbench({ imageUrl, onSave, species }: WorkbenchProps) {
  const handleStyleChange = (style: string) => {
    console.log('Style changed to:', style);
  };

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-[1fr,400px]">
      <Canvas imageUrl={imageUrl} species={species} />
      <ToolPanel onStyleChange={handleStyleChange} onSave={onSave} />
    </div>
  );
}

