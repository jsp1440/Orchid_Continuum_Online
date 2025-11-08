import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { X, ArrowRight, ArrowLeft } from 'lucide-react';
import { StageProgress } from './StageProgress';
import { SpeciesSelection } from './SpeciesSelection';
import { PhotoComparison } from './PhotoComparison';
import { HerbariumSelection } from './HerbariumSelection';
import { BotanicalPlateSelection } from './BotanicalPlateSelection';
import { LabelingInterface } from './LabelingInterface';
import { DichotomousKey } from './DichotomousKey';
import { ValidateCorrect } from './ValidateCorrect';
import { TraitToggles } from './TraitToggles';
import { AssembleBloom } from './AssembleBloom';
import { ExportSave } from './ExportSave';
import { Stage, Species } from '@/types/bloombuilder';

const LOGO_URL = 'https://d64gsuwffb70l.cloudfront.net/690834181f0df3feae691840_1762145786266_9bf02efb.webp';

interface WorkflowData {
  species: Species | null;
  selectedPhotos: string[];
  startingPhoto?: string;
  selectedHerbarium: string[];
  selectedPlates: string[];
  labels: any[];
  keyPath: any[];
  validations: any[];
  traits: any[];
}

export function BloomBuilderWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [showIntro, setShowIntro] = useState(true);
  const [stage, setStage] = useState<Stage>('species');
  const [completedStages, setCompletedStages] = useState<Stage[]>([]);
  const [workflowData, setWorkflowData] = useState<WorkflowData>({
    species: null,
    selectedPhotos: [],
    selectedHerbarium: [],
    selectedPlates: [],
    labels: [],
    keyPath: [],
    validations: [],
    traits: []
  });

  const handleSpeciesSelect = (species: Species) => {
    setWorkflowData(prev => ({ ...prev, species }));
    markStageComplete('species');
    setStage('photo');
  };

  const handlePhotoComplete = (selectedPhotos: string[], startingPhoto: string) => {
    setWorkflowData(prev => ({ ...prev, selectedPhotos, startingPhoto }));
    markStageComplete('photo');
    setStage('herbarium');
  };

  const handleHerbariumComplete = (selectedHerbarium: string[]) => {
    setWorkflowData(prev => ({ ...prev, selectedHerbarium }));
    markStageComplete('herbarium');
    setStage('plate');
  };

  const handlePlateComplete = (selectedPlates: string[]) => {
    setWorkflowData(prev => ({ ...prev, selectedPlates }));
    markStageComplete('plate');
    setStage('labeling');
  };

  const handleLabelingComplete = (labels: any[]) => {
    setWorkflowData(prev => ({ ...prev, labels }));
    markStageComplete('labeling');
    setStage('key');
  };

  const handleKeyComplete = (keyPath: any[]) => {
    setWorkflowData(prev => ({ ...prev, keyPath }));
    markStageComplete('key');
    setStage('validate');
  };

  const handleValidationComplete = (validations: any[]) => {
    setWorkflowData(prev => ({ ...prev, validations }));
    markStageComplete('validate');
    setStage('traits');
  };

  const handleTraitsComplete = (traits: any[]) => {
    setWorkflowData(prev => ({ ...prev, traits }));
    markStageComplete('traits');
    setStage('assemble');
  };

  const handleAssembleComplete = () => {
    markStageComplete('assemble');
    setStage('export');
  };

  const handleExportComplete = () => {
    markStageComplete('export');
    // Session complete
    alert('BloomBuilder session complete! Thank you for contributing to The Orchid Continuum.');
    handleClose();
  };

  const markStageComplete = (completedStage: Stage) => {
    if (!completedStages.includes(completedStage)) {
      setCompletedStages(prev => [...prev, completedStage]);
    }
  };

  const goToNextStage = () => {
    const stages: Stage[] = [
      'species', 'photo', 'herbarium', 'plate', 'labeling',
      'key', 'validate', 'traits', 'assemble', 'export'
    ];
    const currentIndex = stages.indexOf(stage);
    if (currentIndex < stages.length - 1) {
      setStage(stages[currentIndex + 1]);
    }
  };

  const goToPrevStage = () => {
    const stages: Stage[] = [
      'species', 'photo', 'herbarium', 'plate', 'labeling',
      'key', 'validate', 'traits', 'assemble', 'export'
    ];
    const currentIndex = stages.indexOf(stage);
    if (currentIndex > 0) {
      setStage(stages[currentIndex - 1]);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setShowIntro(true);
    setStage('species');
    setCompletedStages([]);
    setWorkflowData({
      species: null,
      selectedPhotos: [],
      selectedHerbarium: [],
      selectedPlates: [],
      labels: [],
      keyPath: [],
      validations: [],
      traits: []
    });
  };

  return (
    <>
      <Card className="p-6 max-w-sm cursor-pointer hover:shadow-lg transition-shadow bg-gradient-to-br from-purple-50 to-white border-purple-200" onClick={() => setIsOpen(true)}>
        <div className="flex items-center gap-4">
          <img src={LOGO_URL} alt="Orchid Continuum" className="w-16 h-16 rounded-lg" />
          <div>
            <h3 className="font-semibold text-lg text-purple-900">BloomBuilder</h3>
            <p className="text-sm text-purple-700">Practice real orchid taxonomy — learn, validate, and contribute</p>
          </div>
        </div>
      </Card>


      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0 overflow-hidden flex flex-col">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4 z-50"
            onClick={handleClose}
          >
            <X className="w-4 h-4" />
          </Button>

          <StageProgress currentStage={stage} completedStages={completedStages} />

          <div className="flex-1 overflow-y-auto">
            {showIntro && (
              <div className="p-8 max-w-4xl mx-auto">
                <div className="bg-gradient-to-br from-purple-600 to-purple-800 text-white rounded-2xl p-8 mb-8 text-center">
                  <h1 className="text-4xl font-bold mb-3">BloomBuilder</h1>
                  <p className="text-xl mb-2 text-purple-100">Practice real orchid taxonomy — learn, validate, and contribute.</p>
                  <p className="text-purple-100 max-w-2xl mx-auto leading-relaxed">
                    Built on <strong>The Orchid Continuum</strong>, BloomBuilder guides you from authentic herbarium sheets to verified identifications.
                    Use dichotomous keys and glossary terms, compare with historical plates, explore phenotypic traits, and add your observations.
                  </p>
                </div>

                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-purple-900 mb-4">How BloomBuilder Works</h2>
                  <div className="space-y-3">
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">1.</span>
                      <div><strong>Select a species</strong> → authentic herbarium sheets anchor your study.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">2.</span>
                      <div><strong>Observe & compare</strong> → inspect high-resolution images against historical plates.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">3.</span>
                      <div><strong>Identify & label</strong> → apply dichotomous keys and orchid terminology.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">4.</span>
                      <div><strong>Verify through traits</strong> → consult the Trait Databank for diagnostic matches.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">5.</span>
                      <div><strong>Add notes</strong> → record insights, hypotheses, and pollinator-linked observations.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">6.</span>
                      <div><strong>Explore adaptation</strong> → relate structures to pollination, habitat, and survival.</div>
                    </div>
                    <div className="flex gap-3 items-start border-l-4 border-purple-300 pl-4 py-2">
                      <span className="font-bold text-purple-600">7.</span>
                      <div><strong>Create & contribute</strong> → generate a final composite and add it to the Continuum.</div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-center gap-4">
                  <Button 
                    size="lg"
                    className="bg-purple-600 hover:bg-purple-700 text-white px-8"
                    onClick={() => setShowIntro(false)}
                  >
                    Start a Session <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </div>
              </div>
            )}
            
            {!showIntro && stage === 'species' && (
              <SpeciesSelection onSelect={handleSpeciesSelect} />
            )}
            {!showIntro && stage === 'photo' && workflowData.species && (
              <PhotoComparison 
                species={workflowData.species} 
                onComplete={handlePhotoComplete}
              />
            )}
            {!showIntro && stage === 'herbarium' && workflowData.species && (
              <HerbariumSelection 
                species={workflowData.species} 
                onComplete={handleHerbariumComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'plate' && workflowData.species && (
              <BotanicalPlateSelection 
                species={workflowData.species} 
                onComplete={handlePlateComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'labeling' && workflowData.species && (
              <LabelingInterface 
                species={workflowData.species} 
                selectedHerbarium={workflowData.selectedHerbarium}
                selectedPlates={workflowData.selectedPlates}
                onComplete={handleLabelingComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'key' && workflowData.species && (
              <DichotomousKey 
                species={workflowData.species}
                onComplete={handleKeyComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'validate' && workflowData.species && (
              <ValidateCorrect 
                species={workflowData.species}
                labels={workflowData.labels}
                keyPath={workflowData.keyPath}
                onComplete={handleValidationComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'traits' && workflowData.species && (
              <TraitToggles 
                species={workflowData.species}
                onComplete={handleTraitsComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'assemble' && workflowData.species && (
              <AssembleBloom 
                species={workflowData.species}
                onComplete={handleAssembleComplete}
                onBack={goToPrevStage}
              />
            )}
            {!showIntro && stage === 'export' && workflowData.species && (
              <ExportSave 
                species={workflowData.species}
                workflowData={workflowData}
                onComplete={handleExportComplete}
                onBack={goToPrevStage}
              />
            )}
          </div>

          <div className="border-t p-4 flex justify-between bg-gray-50">
            <Button 
              variant="outline" 
              onClick={goToPrevStage}
              disabled={stage === 'species'}
            >
              <ArrowLeft className="mr-2 w-4 h-4" /> Back
            </Button>
            <Button 
              onClick={goToNextStage}
              disabled={stage === 'export'}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {stage === 'export' ? 'Complete' : 'Continue'} <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
