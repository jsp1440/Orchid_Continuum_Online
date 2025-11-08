import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tag, Grid, Eye, EyeOff, Info, Plus, X } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface Label {
  id: string;
  structure: string;
  x: number;
  y: number;
  notes: string;
  isPrePlaced: boolean;
}

interface LabelingInterfaceProps {
  species: Species;
  selectedHerbarium: string[];
  selectedPlates: string[];
  onComplete: (labels: any[]) => void;
  onBack: () => void;
}

const REQUIRED_STRUCTURES = [
  'Column',
  'Labellum (Lip)',
  'Petals',
  'Sepals',
  'Spur/Mentum',
  'Pollinia'
];

const OPTIONAL_STRUCTURES = [
  'Anther',
  'Stigma',
  'Rostellum',
  'Ovary',
  'Bract',
  'Pedicel',
  'Callus',
  'Crest',
  'Column foot',
  'Viscidium',
  'Other (specify in notes)'
];

export function LabelingInterface({ species, selectedHerbarium, selectedPlates, onComplete, onBack }: LabelingInterfaceProps) {
  const [currentView, setCurrentView] = useState<'herbarium' | 'plate'>('herbarium');
  const [herbariumLabels, setHerbariumLabels] = useState<Label[]>([]);
  const [plateLabels, setPlateLabels] = useState<Label[]>([]);
  const [showPreLabels, setShowPreLabels] = useState(true);
  const [gridSnap, setGridSnap] = useState(false);
  const [glossaryTerm, setGlossaryTerm] = useState<string | null>(null);
  const [addingLabel, setAddingLabel] = useState(false);
  const [selectedStructure, setSelectedStructure] = useState('');
  const [labelNotes, setLabelNotes] = useState('');
  const [herbariumImage, setHerbariumImage] = useState('');
  const [plateImage, setPlateImage] = useState('');

  useEffect(() => {
    // Initialize with pre-placed labels for required structures
    const prePlaced: Label[] = REQUIRED_STRUCTURES.map((structure, idx) => ({
      id: `pre-${idx}`,
      structure,
      x: 20 + (idx % 3) * 30,
      y: 20 + Math.floor(idx / 3) * 30,
      notes: '',
      isPrePlaced: true
    }));
    setHerbariumLabels(prePlaced);
    setPlateLabels([...prePlaced]); // Start with same positions for plate
  }, []);

  const handleImageClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!addingLabel || !selectedStructure) return;

    const rect = e.currentTarget.getBoundingClientRect();
    let x = ((e.clientX - rect.left) / rect.width) * 100;
    let y = ((e.clientY - rect.top) / rect.height) * 100;

    // Grid snap if enabled
    if (gridSnap) {
      x = Math.round(x / 5) * 5;
      y = Math.round(y / 5) * 5;
    }

    const newLabel: Label = {
      id: `custom-${Date.now()}`,
      structure: selectedStructure,
      x,
      y,
      notes: labelNotes,
      isPrePlaced: false
    };

    if (currentView === 'herbarium') {
      setHerbariumLabels([...herbariumLabels, newLabel]);
    } else {
      setPlateLabels([...plateLabels, newLabel]);
    }

    setAddingLabel(false);
    setSelectedStructure('');
    setLabelNotes('');
  };

  const removeLabel = (labelId: string) => {
    if (currentView === 'herbarium') {
      setHerbariumLabels(herbariumLabels.filter(l => l.id !== labelId));
    } else {
      setPlateLabels(plateLabels.filter(l => l.id !== labelId));
    }
  };

  const updateLabelNotes = (labelId: string, notes: string) => {
    if (currentView === 'herbarium') {
      setHerbariumLabels(herbariumLabels.map(l => 
        l.id === labelId ? { ...l, notes } : l
      ));
    } else {
      setPlateLabels(plateLabels.map(l => 
        l.id === labelId ? { ...l, notes } : l
      ));
    }
  };

  const handleContinue = () => {
    onComplete([
      ...herbariumLabels.map(l => ({ ...l, view: 'herbarium' })),
      ...plateLabels.map(l => ({ ...l, view: 'plate' }))
    ]);
  };

  const currentLabels = currentView === 'herbarium' ? herbariumLabels : plateLabels;
  const currentImage = currentView === 'herbarium' ? herbariumImage : plateImage;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Labeling Interface</h2>
        <p className="text-gray-600 mb-4">
          Click on the images to label orchid structures. Required structures are pre-placed - adjust their positions as needed.
        </p>
        <div className="flex gap-4 items-center flex-wrap">
          <div className="flex gap-2">
            <Button
              variant={currentView === 'herbarium' ? 'default' : 'outline'}
              onClick={() => setCurrentView('herbarium')}
              className={currentView === 'herbarium' ? 'bg-purple-600' : ''}
            >
              Herbarium View
            </Button>
            <Button
              variant={currentView === 'plate' ? 'default' : 'outline'}
              onClick={() => setCurrentView('plate')}
              className={currentView === 'plate' ? 'bg-purple-600' : ''}
            >
              Botanical Plate View
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Switch checked={showPreLabels} onCheckedChange={setShowPreLabels} />
            <span className="text-sm">{showPreLabels ? <Eye className="inline w-4 h-4" /> : <EyeOff className="inline w-4 h-4" />} Pre-labels</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Switch checked={gridSnap} onCheckedChange={setGridSnap} />
            <span className="text-sm"><Grid className="inline w-4 h-4" /> Grid Snap</span>
          </div>

          <Badge variant="outline" className="text-base">
            {currentLabels.length} label{currentLabels.length !== 1 ? 's' : ''} placed
          </Badge>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Image Canvas */}
        <div className="lg:col-span-2">
          <Card className="overflow-hidden">
            <div 
              className={`relative bg-gray-100 aspect-[4/3] ${addingLabel ? 'cursor-crosshair' : ''}`}
              onClick={handleImageClick}
            >
              {/* Placeholder image - in real app would show actual herbarium/plate */}
              <div className="absolute inset-0 flex items-center justify-center bg-gray-200">
                <p className="text-gray-500">
                  {currentView === 'herbarium' ? 'Herbarium Sheet' : 'Botanical Plate'} Image
                </p>
              </div>

              {/* Labels */}
              {currentLabels.map((label) => {
                if (!showPreLabels && label.isPrePlaced) return null;
                
                return (
                  <div
                    key={label.id}
                    className="absolute"
                    style={{
                      left: `${label.x}%`,
                      top: `${label.y}%`,
                      transform: 'translate(-50%, -50%)'
                    }}
                  >
                    <div className={`flex items-center gap-1 ${label.isPrePlaced ? 'bg-yellow-500' : 'bg-purple-600'} text-white px-2 py-1 rounded-lg text-xs font-semibold shadow-lg`}>
                      <Tag className="w-3 h-3" />
                      <span>{label.structure}</span>
                      {!label.isPrePlaced && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeLabel(label.id);
                          }}
                          className="ml-1 hover:bg-white/20 rounded"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                    <div className={`absolute top-full left-1/2 -translate-x-1/2 w-0.5 h-4 ${label.isPrePlaced ? 'bg-yellow-500' : 'bg-purple-600'}`}></div>
                    <div className={`absolute top-full left-1/2 -translate-x-1/2 mt-3 w-2 h-2 rounded-full ${label.isPrePlaced ? 'bg-yellow-500' : 'bg-purple-600'}`}></div>
                  </div>
                );
              })}

              {/* Grid overlay when snap enabled */}
              {gridSnap && (
                <div className="absolute inset-0 pointer-events-none">
                  <svg width="100%" height="100%" className="opacity-20">
                    <defs>
                      <pattern id="grid" width="5%" height="5%" patternUnits="userSpaceOnUse">
                        <path d="M 0 0 L 0 100 M 0 0 L 100 0" fill="none" stroke="gray" strokeWidth="0.5"/>
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />
                  </svg>
                </div>
              )}
            </div>
          </Card>

          {addingLabel && (
            <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                <Info className="inline w-4 h-4 mr-1" />
                Click anywhere on the image to place the "{selectedStructure}" label
              </p>
            </div>
          )}
        </div>

        {/* Label Controls */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="font-bold mb-3">Required Structures</h3>
            <div className="space-y-2 text-sm">
              {REQUIRED_STRUCTURES.map(structure => {
                const hasLabel = currentLabels.some(l => l.structure === structure);
                return (
                  <div key={structure} className="flex items-center justify-between">
                    <button
                      className="text-purple-600 hover:text-purple-800 underline text-left"
                      onClick={() => setGlossaryTerm(structure)}
                    >
                      {structure}
                    </button>
                    {hasLabel && <Badge variant="success" size="sm">✓</Badge>}
                  </div>
                );
              })}
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="font-bold mb-3">Add Optional Label</h3>
            <select
              className="w-full mb-2 p-2 border rounded"
              value={selectedStructure}
              onChange={(e) => setSelectedStructure(e.target.value)}
            >
              <option value="">Select structure...</option>
              {OPTIONAL_STRUCTURES.map(struct => (
                <option key={struct} value={struct}>{struct}</option>
              ))}
            </select>
            
            <textarea
              className="w-full mb-2 p-2 border rounded text-sm"
              placeholder="Optional notes..."
              value={labelNotes}
              onChange={(e) => setLabelNotes(e.target.value)}
              rows={2}
            />

            <Button
              onClick={() => setAddingLabel(true)}
              disabled={!selectedStructure}
              className="w-full bg-purple-600"
              size="sm"
            >
              <Plus className="w-4 h-4 mr-2" /> Place Label
            </Button>
          </Card>

          <Card className="p-4">
            <h3 className="font-bold mb-3">Label Notes</h3>
            <div className="space-y-2 text-xs max-h-48 overflow-y-auto">
              {currentLabels.map(label => (
                <div key={label.id} className="border-b pb-2">
                  <p className="font-semibold text-purple-900">{label.structure}</p>
                  <input
                    type="text"
                    placeholder="Add notes..."
                    value={label.notes}
                    onChange={(e) => updateLabelNotes(label.id, e.target.value)}
                    className="w-full mt-1 p-1 border rounded text-xs"
                  />
                </div>
              ))}
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
          Continue to Dichotomous Key
        </Button>
      </div>

      {/* Glossary Modal */}
      <Dialog open={glossaryTerm !== null} onOpenChange={() => setGlossaryTerm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{glossaryTerm}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-700">
              Definition and micro-diagram for <strong>{glossaryTerm}</strong> would appear here.
            </p>
            <div className="bg-gray-100 h-40 rounded flex items-center justify-center">
              <p className="text-gray-500 text-sm">Micro-diagram placeholder</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
