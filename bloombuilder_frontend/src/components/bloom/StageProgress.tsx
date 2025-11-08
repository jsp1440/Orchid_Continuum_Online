import { Stage, STAGE_INFO } from '@/types/bloombuilder';
import { Check } from 'lucide-react';

interface StageProgressProps {
  currentStage: Stage;
  completedStages: Stage[];
}

export function StageProgress({ currentStage, completedStages }: StageProgressProps) {
  const allStages: Stage[] = [
    'species', 'photo', 'herbarium', 'plate', 'labeling', 
    'key', 'validate', 'traits', 'assemble', 'export'
  ];

  const currentStageNum = STAGE_INFO[currentStage].number;

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-2">
          <h2 className="text-lg font-semibold text-purple-900">
            Stage {currentStageNum}/10: {STAGE_INFO[currentStage].title}
          </h2>
          <p className="text-sm text-gray-600">{STAGE_INFO[currentStage].description}</p>
        </div>
        
        <div className="flex items-center gap-2 mt-4">
          {allStages.map((stage, index) => {
            const stageNum = index + 1;
            const isCompleted = completedStages.includes(stage);
            const isCurrent = stage === currentStage;
            
            return (
              <div key={stage} className="flex items-center">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
                    ${isCompleted ? 'bg-purple-600 text-white' : ''}
                    ${isCurrent && !isCompleted ? 'bg-purple-200 text-purple-900 ring-2 ring-purple-600' : ''}
                    ${!isCompleted && !isCurrent ? 'bg-gray-200 text-gray-500' : ''}
                  `}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : stageNum}
                </div>
                {index < allStages.length - 1 && (
                  <div 
                    className={`w-8 h-0.5 ${isCompleted ? 'bg-purple-600' : 'bg-gray-200'}`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
