import { useEffect, useRef, useState } from 'react';
import { fabric } from 'fabric';
import { CanvasToolbar } from './CanvasToolbar';
import { setupShapeDrawing } from '@/lib/fabricHelpers';
import { Species } from '@/types/bloombuilder';
import { useAppContext } from '@/contexts/AppContext';
import { crossfadeToLayer } from './CanvasLayers';

interface CanvasProps {
  imageUrl: string;
  species?: Species | null;
}

export function Canvas({ imageUrl, species }: CanvasProps) {
  const { spurLength, petalColor, getTraitImageUrl } = useAppContext();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricCanvasRef = useRef<fabric.Canvas | null>(null);
  const currentLayerRef = useRef<fabric.Image | null>(null);
  const [activeTool, setActiveTool] = useState('pen');
  const [color, setColor] = useState('#000000');
  const historyRef = useRef<any[]>([]);
  const historyStepRef = useRef(0);

  const getTraitImageUrlForCanvas = () => {
    const traitImageUrl = getTraitImageUrl(spurLength, petalColor);
    // If a trait-specific image is set, use it; otherwise fall back to base image
    return traitImageUrl || imageUrl;
  };




  // Initialize canvas with base image
  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = new fabric.Canvas(canvasRef.current, {
      width: 800,
      height: 600,
      backgroundColor: '#f8fafc',
    });
    fabricCanvasRef.current = canvas;

    // Load initial image as a layer
    fabric.Image.fromURL(imageUrl, (img) => {
      const scale = Math.min(800 / (img.width || 1), 600 / (img.height || 1)) * 0.9;
      img.scale(scale);
      img.set({ 
        selectable: false, 
        evented: false,
        originX: 'center',
        originY: 'center',
        left: 400,
        top: 300,
      });
      canvas.add(img);
      currentLayerRef.current = img;
      canvas.renderAll();
    });

    saveHistory();
    return () => canvas.dispose();
  }, [imageUrl]);

  // Watch for trait changes and trigger crossfade
  useEffect(() => {
    const canvas = fabricCanvasRef.current;
    if (!canvas || !currentLayerRef.current) return;

    const targetUrl = getTraitImageUrlForCanvas();

    
    // Trigger crossfade animation
    crossfadeToLayer(canvas, currentLayerRef.current, targetUrl, (newLayer) => {
      currentLayerRef.current = newLayer;
      saveHistory();
    });
  }, [spurLength, petalColor]);


  useEffect(() => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) return;

    canvas.isDrawingMode = activeTool === 'pen';
    if (canvas.freeDrawingBrush) {
      canvas.freeDrawingBrush.color = color;
      canvas.freeDrawingBrush.width = 3;
    }

    if (activeTool === 'eraser') {
      canvas.isDrawingMode = true;
      if (canvas.freeDrawingBrush) {
        canvas.freeDrawingBrush.color = '#f8fafc';
        canvas.freeDrawingBrush.width = 20;
      }
    }

    const handleTextAdd = (e: fabric.IEvent) => {
      if (activeTool === 'text') {
        const pointer = canvas.getPointer(e.e);
        const text = new fabric.IText('Label', {
          left: pointer.x,
          top: pointer.y,
          fill: color,
          fontSize: 20,
          fontFamily: 'Arial',
        });
        canvas.add(text);
        saveHistory();
      }
    };

    const handlePathCreated = () => {
      if (activeTool === 'pen' || activeTool === 'eraser') {
        saveHistory();
      }
    };

    canvas.on('mouse:down', handleTextAdd);
    canvas.on('path:created', handlePathCreated);

    const cleanup = ['rect', 'circle', 'arrow'].includes(activeTool)
      ? setupShapeDrawing(canvas, activeTool, color, saveHistory)
      : undefined;

    return () => {
      canvas.off('mouse:down', handleTextAdd);
      canvas.off('path:created', handlePathCreated);
      cleanup?.();
    };
  }, [activeTool, color]);

  const saveHistory = () => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) return;
    historyRef.current = historyRef.current.slice(0, historyStepRef.current + 1);
    historyRef.current.push(JSON.stringify(canvas.toJSON()));
    historyStepRef.current++;
  };

  const handleUndo = () => {
    if (historyStepRef.current > 0) {
      historyStepRef.current--;
      const canvas = fabricCanvasRef.current;
      canvas?.loadFromJSON(historyRef.current[historyStepRef.current], canvas.renderAll.bind(canvas));
    }
  };

  const handleRedo = () => {
    if (historyStepRef.current < historyRef.current.length - 1) {
      historyStepRef.current++;
      const canvas = fabricCanvasRef.current;
      canvas?.loadFromJSON(historyRef.current[historyStepRef.current], canvas.renderAll.bind(canvas));
    }
  };

  const handleClear = () => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) return;
    canvas.getObjects().forEach((obj) => {
      if (obj !== canvas.backgroundImage) {
        canvas.remove(obj);
      }
    });
    canvas.renderAll();
    saveHistory();
  };

  const handleDownload = () => {
    handleExport({ format: 'png', quality: 1, multiplier: 2 });
  };

  const handleExport = ({ format, quality, multiplier }: { format: 'png' | 'jpg' | 'svg'; quality: number; multiplier: number }) => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) return;

    if (format === 'svg') {
      // Export as SVG
      const svgData = canvas.toSVG();
      const blob = new Blob([svgData], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.download = `orchid-annotation-${Date.now()}.svg`;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } else {
      // Export as PNG or JPG
      const dataURL = canvas.toDataURL({
        format: format === 'jpg' ? 'jpeg' : 'png',
        quality: quality,
        multiplier: multiplier,
      });

      const link = document.createElement('a');
      link.download = `orchid-annotation-${Date.now()}.${format}`;
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleSaveProject = () => {
    const canvas = fabricCanvasRef.current;
    if (!canvas) return;

    const projectData = {
      version: '1.0',
      createdAt: new Date().toISOString(),
      species: species ? {
        id: species.id,
        commonName: species.commonName,
        scientificName: species.scientificName,
      } : null,
      imageUrl,
      canvasState: canvas.toJSON(),
      settings: {
        activeTool,
        color,
      },
    };

    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const filename = species 
      ? `${species.commonName.replace(/\s+/g, '-').toLowerCase()}-project-${Date.now()}.json`
      : `orchid-project-${Date.now()}.json`;
    link.download = filename;
    link.href = url;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleLoadProject = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const projectData = JSON.parse(event.target?.result as string);
          const canvas = fabricCanvasRef.current;
          if (!canvas) return;

          // Load canvas state
          canvas.loadFromJSON(projectData.canvasState, () => {
            canvas.renderAll();
            saveHistory();
          });

          // Restore settings
          if (projectData.settings) {
            setActiveTool(projectData.settings.activeTool || 'pen');
            setColor(projectData.settings.color || '#000000');
          }
        } catch (error) {
          console.error('Error loading project:', error);
          alert('Failed to load project file. Please ensure it is a valid BloomBuilder project.');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };



  return (
    <div className="h-full flex flex-col bg-slate-50">
      <CanvasToolbar
        activeTool={activeTool}
        onToolChange={setActiveTool}
        color={color}
        onColorChange={setColor}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onClear={handleClear}
        onDownload={handleDownload}
        onExport={handleExport}
        onSaveProject={handleSaveProject}
        onLoadProject={handleLoadProject}
      />


      <div className="flex-1 flex items-center justify-center p-8 relative">
        <canvas ref={canvasRef} className="border-2 border-gray-300 rounded-lg shadow-lg" />
        
        {/* Trait State Indicator */}
        <div className="absolute bottom-12 right-12 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 border border-gray-200">
          <div className="text-xs font-medium text-gray-600 mb-1">Current Traits</div>
          <div className="flex gap-3 text-xs">
            <div>
              <span className="text-gray-500">Spur:</span>{' '}
              <span className="font-semibold text-gray-900 uppercase">{spurLength}</span>
            </div>
            <div className="border-l border-gray-300 pl-3">
              <span className="text-gray-500">Color:</span>{' '}
              <span className="font-semibold text-gray-900 capitalize">{petalColor}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
