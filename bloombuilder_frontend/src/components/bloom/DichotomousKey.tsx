import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ChevronRight, Check, Info, Book } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface KeyStep {
  id: string;
  question: string;
  optionA: string;
  optionB: string;
  glossaryTerms: string[];
  nextStepA?: string;
  nextStepB?: string;
}

interface DichotomousKeyProps {
  species: Species;
  onComplete: (keyPath: any[]) => void;
  onBack: () => void;
}

export function DichotomousKey({ species, onComplete, onBack }: DichotomousKeyProps) {
  const [currentStep, setCurrentStep] = useState('1');
  const [keyPath, setKeyPath] = useState<any[]>([]);
  const [glossaryTerm, setGlossaryTerm] = useState<string | null>(null);
  const [showPath, setShowPath] = useState(true);
  const [keySteps, setKeySteps] = useState<Record<string, KeyStep>>({});

  useEffect(() => {
    // Initialize with sample key for demonstration
    // In real app, this would load from API based on species
    const sampleKey: Record<string, KeyStep> = {
      '1': {
        id: '1',
        question: 'Does the flower have a distinct spur or mentum?',
        optionA: 'Spur or mentum present',
        optionB: 'No spur or mentum',
        glossaryTerms: ['Spur', 'Mentum'],
        nextStepA: '2',
        nextStepB: '3'
      },
      '2': {
        id: '2',
        question: 'Is the labellum (lip) fringed or lobed?',
        optionA: 'Labellum fringed',
        optionB: 'Labellum entire or slightly lobed',
        glossaryTerms: ['Labellum', 'Fringed', 'Lobed'],
        nextStepA: '4',
        nextStepB: '5'
      },
      '3': {
        id: '3',
        question: 'Are the petals fused to form a hood over the column?',
        optionA: 'Petals form hood',
        optionB: 'Petals separate',
        glossaryTerms: ['Petals', 'Column', 'Hood'],
        nextStepA: '6',
        nextStepB: '7'
      },
      '4': {
        id: '4',
        question: 'Identification reached: Platanthera species',
        optionA: 'Confirm identification',
        optionB: 'Review path',
        glossaryTerms: [],
        nextStepA: undefined,
        nextStepB: '1'
      },
      '5': {
        id: '5',
        question: `Identification reached: ${species.scientificName}`,
        optionA: 'Confirm identification',
        optionB: 'Review path',
        glossaryTerms: [],
        nextStepA: undefined,
        nextStepB: '1'
      },
      '6': {
        id: '6',
        question: 'Identification reached: Cypripedium species',
        optionA: 'Confirm identification',
        optionB: 'Review path',
        glossaryTerms: [],
        nextStepA: undefined,
        nextStepB: '1'
      },
      '7': {
        id: '7',
        question: `Identification reached: ${species.scientificName}`,
        optionA: 'Confirm identification',
        optionB: 'Review path',
        glossaryTerms: [],
        nextStepA: undefined,
        nextStepB: '1'
      }
    };
    
    setKeySteps(sampleKey);
  }, [species]);

  const handleChoice = (choice: 'A' | 'B') => {
    const step = keySteps[currentStep];
    if (!step) return;

    const pathEntry = {
      stepId: currentStep,
      question: step.question,
      choice: choice === 'A' ? step.optionA : step.optionB,
      choiceLetter: choice
    };

    setKeyPath([...keyPath, pathEntry]);

    const nextStepId = choice === 'A' ? step.nextStepA : step.nextStepB;
    
    if (nextStepId) {
      setCurrentStep(nextStepId);
    } else {
      // Reached end - complete
      setTimeout(() => {
        onComplete([...keyPath, pathEntry]);
      }, 500);
    }
  };

  const goToStep = (stepId: string) => {
    const stepIndex = keyPath.findIndex(p => p.stepId === stepId);
    if (stepIndex >= 0) {
      setKeyPath(keyPath.slice(0, stepIndex));
      setCurrentStep(stepId);
    }
  };

  const currentStepData = keySteps[currentStep];
  const isTerminal = currentStepData && !currentStepData.nextStepA;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Dichotomous Key</h2>
        <p className="text-gray-600 mb-4">
          Follow the taxonomic key to verify the species identification. Click glossary terms for definitions.
        </p>
        <div className="flex gap-4 items-center">
          <Badge variant="outline" className="text-base">
            Step {currentStep} of key
          </Badge>
          <Badge variant={isTerminal ? 'success' : 'info'} className="text-base">
            {keyPath.length} decision{keyPath.length !== 1 ? 's' : ''} made
          </Badge>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Current Key Step */}
        <div className="lg:col-span-2">
          {currentStepData && (
            <Card className="p-6">
              <div className="mb-6">
                <div className="flex items-start gap-3">
                  <Book className="w-6 h-6 text-purple-600 mt-1" />
                  <div>
                    <h3 className="text-lg font-bold mb-2 text-purple-900">
                      Step {currentStep}
                    </h3>
                    <p className="text-gray-900 text-lg leading-relaxed">
                      {currentStepData.question}
                    </p>
                  </div>
                </div>
                
                {currentStepData.glossaryTerms.length > 0 && (
                  <div className="mt-4 p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm font-semibold text-purple-900 mb-2">Glossary Terms:</p>
                    <div className="flex flex-wrap gap-2">
                      {currentStepData.glossaryTerms.map(term => (
                        <button
                          key={term}
                          onClick={() => setGlossaryTerm(term)}
                          className="text-sm bg-white border border-purple-300 text-purple-700 px-3 py-1 rounded-full hover:bg-purple-100"
                        >
                          <Info className="inline w-3 h-3 mr-1" />
                          {term}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <Button
                  onClick={() => handleChoice('A')}
                  className="w-full justify-start text-left h-auto py-4 bg-purple-600 hover:bg-purple-700"
                  disabled={isTerminal && currentStepData.optionA === 'Confirm identification'}
                >
                  <span className="font-bold mr-3">A.</span>
                  <span className="flex-1">{currentStepData.optionA}</span>
                  {!isTerminal && <ChevronRight className="w-5 h-5" />}
                  {isTerminal && currentStepData.optionA === 'Confirm identification' && <Check className="w-5 h-5" />}
                </Button>

                <Button
                  onClick={() => handleChoice('B')}
                  variant="outline"
                  className="w-full justify-start text-left h-auto py-4 border-2 border-purple-600 hover:bg-purple-50"
                >
                  <span className="font-bold mr-3">B.</span>
                  <span className="flex-1">{currentStepData.optionB}</span>
                  {!isTerminal && <ChevronRight className="w-5 h-5" />}
                  {isTerminal && currentStepData.optionB === 'Review path' && <span className="text-sm">↺</span>}
                </Button>
              </div>

              {isTerminal && (
                <div className="mt-6 p-4 bg-green-50 border-2 border-green-500 rounded-lg">
                  <p className="text-green-900 font-semibold text-center">
                    <Check className="inline w-5 h-5 mr-2" />
                    You've reached a terminal identification!
                  </p>
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Key Path Tracker */}
        <div>
          <Card className="p-4 sticky top-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold">Decision Path</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPath(!showPath)}
              >
                {showPath ? 'Hide' : 'Show'}
              </Button>
            </div>
            
            {showPath && (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {keyPath.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No decisions yet</p>
                )}
                
                {keyPath.map((entry, idx) => (
                  <div key={idx} className="text-sm border-l-2 border-purple-600 pl-3 py-2">
                    <button
                      onClick={() => goToStep(entry.stepId)}
                      className="text-left hover:text-purple-600"
                    >
                      <p className="font-semibold text-xs text-gray-600">Step {entry.stepId}</p>
                      <p className="text-purple-900">{entry.choiceLetter}. {entry.choice}</p>
                    </button>
                  </div>
                ))}

                {isTerminal && (
                  <div className="mt-4 pt-4 border-t">
                    <Badge variant="success" className="w-full justify-center">
                      Path Complete
                    </Badge>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={() => onComplete(keyPath)}
          className="bg-purple-600 hover:bg-purple-700"
          disabled={!isTerminal}
        >
          Continue to Validation
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
              Definition and micro-diagram for <strong>{glossaryTerm}</strong> would appear here from the glossary database.
            </p>
            <div className="bg-gray-100 h-48 rounded flex items-center justify-center">
              <p className="text-gray-500 text-sm">Micro-diagram placeholder</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
