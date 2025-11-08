import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Pen, Square, Circle, ArrowRight, Type, Eraser, Undo, Redo, Trash2, Download, Save, FolderOpen } from 'lucide-react';
import { ExportSettingsDropdown } from './ExportSettingsDropdown';



interface CanvasToolbarProps {
  activeTool: string;
  onToolChange: (tool: string) => void;
  color: string;
  onColorChange: (color: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;
  onDownload: () => void;
  onExport: (settings: { format: 'png' | 'jpg' | 'svg'; quality: number; multiplier: number }) => void;
  onSaveProject: () => void;
  onLoadProject: () => void;
}



const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF'];

export function CanvasToolbar({ activeTool, onToolChange, color, onColorChange, onUndo, onRedo, onClear, onDownload, onExport, onSaveProject, onLoadProject }: CanvasToolbarProps) {


  return (
    <div className="flex items-center gap-2 p-3 bg-white border-b">
      <Button
        variant={activeTool === 'pen' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('pen')}
      >
        <Pen className="h-4 w-4" />
      </Button>
      <Button
        variant={activeTool === 'rect' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('rect')}
      >
        <Square className="h-4 w-4" />
      </Button>
      <Button
        variant={activeTool === 'circle' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('circle')}
      >
        <Circle className="h-4 w-4" />
      </Button>
      <Button
        variant={activeTool === 'arrow' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('arrow')}
      >
        <ArrowRight className="h-4 w-4" />
      </Button>
      <Button
        variant={activeTool === 'text' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('text')}
      >
        <Type className="h-4 w-4" />
      </Button>
      <Button
        variant={activeTool === 'eraser' ? 'default' : 'outline'}
        size="sm"
        onClick={() => onToolChange('eraser')}
      >
        <Eraser className="h-4 w-4" />
      </Button>
      
      <Separator orientation="vertical" className="h-8" />
      
      <div className="flex gap-1">
        {colors.map((c) => (
          <button
            key={c}
            className={`w-6 h-6 rounded border-2 ${color === c ? 'border-gray-900' : 'border-gray-300'}`}
            style={{ backgroundColor: c }}
            onClick={() => onColorChange(c)}
          />
        ))}
      </div>
      
      <Separator orientation="vertical" className="h-8" />
      
      <Button variant="outline" size="sm" onClick={onUndo}>
        <Undo className="h-4 w-4" />
      </Button>
      <Button variant="outline" size="sm" onClick={onRedo}>
        <Redo className="h-4 w-4" />
      </Button>
      <Button variant="outline" size="sm" onClick={onClear}>
        <Trash2 className="h-4 w-4" />
      </Button>
      
      <Separator orientation="vertical" className="h-8" />
      
      <div className="flex gap-1">
        <Button variant="outline" size="sm" onClick={onSaveProject} className="bg-blue-600 hover:bg-blue-700 text-white">
          <Save className="h-4 w-4 mr-1" />
          Save Project
        </Button>
        <Button variant="outline" size="sm" onClick={onLoadProject}>
          <FolderOpen className="h-4 w-4 mr-1" />
          Load Project
        </Button>
      </div>

      <Separator orientation="vertical" className="h-8" />
      
      <div className="flex gap-1">
        <Button variant="default" size="sm" onClick={onDownload} className="bg-green-600 hover:bg-green-700">
          <Download className="h-4 w-4 mr-1" />
          Download
        </Button>
        <ExportSettingsDropdown onExport={onExport} />
      </div>

    </div>
  );
}
