import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X, AlertCircle, FileText } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface Validation {
  id: string;
  item: string;
  type: 'term' | 'figure';
  status: 'validated' | 'needs_correction' | 'pending';
  correction?: string;
  validator?: string;
  timestamp?: string;
}

interface ValidateCorrectProps {
  species: Species;
  labels: any[];
  keyPath: any[];
  onComplete: (validations: any[]) => void;
  onBack: () => void;
}

export function ValidateCorrect({ species, labels, keyPath, onComplete, onBack }: ValidateCorrectProps) {
  const [validations, setValidations] = useState<Validation[]>([
    // Sample validations - in real app, these would be generated from labels and key path
    { id: '1', item: 'Column label', type: 'term', status: 'pending' },
    { id: '2', item: 'Labellum label', type: 'term', status: 'pending' },
    { id: '3', item: 'Herbarium sheet selection', type: 'figure', status: 'pending' },
    { id: '4', item: 'Botanical plate selection', type: 'figure', status: 'pending' },
    { id: '5', item: 'Dichotomous key path', type: 'term', status: 'pending' },
  ]);
  
  const [activeValidation, setActiveValidation] = useState<string | null>(null);
  const [correctionNote, setCorrectionNote] = useState('');
  const [validatorName, setValidatorName] = useState('');

  const handleValidate = (id: string, isValid: boolean) => {
    if (isValid) {
      setValidations(validations.map(v => 
        v.id === id 
          ? { ...v, status: 'validated', validator: validatorName || 'Anonymous', timestamp: new Date().toISOString() } 
          : v
      ));
      setActiveValidation(null);
    } else {
      setActiveValidation(id);
    }
  };

  const handleCorrection = (id: string) => {
    if (!correctionNote.trim()) {
      alert('Please provide a correction note');
      return;
    }

    setValidations(validations.map(v => 
      v.id === id 
        ? { 
            ...v, 
            status: 'needs_correction', 
            correction: correctionNote,
            validator: validatorName || 'Anonymous',
            timestamp: new Date().toISOString()
          } 
        : v
    ));
    
    setCorrectionNote('');
    setActiveValidation(null);
  };

  const handleContinue = () => {
    const allValidated = validations.every(v => v.status !== 'pending');
    if (!allValidated) {
      alert('Please validate all items before continuing');
      return;
    }
    onComplete(validations);
  };

  const stats = {
    validated: validations.filter(v => v.status === 'validated').length,
    corrections: validations.filter(v => v.status === 'needs_correction').length,
    pending: validations.filter(v => v.status === 'pending').length
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Validate & Correct</h2>
        <p className="text-gray-600 mb-4">
          Two-level validation: Review each labeled term AND each figure. All corrections require notes for the audit trail.
        </p>
        <div className="flex gap-4 items-center flex-wrap">
          <Badge variant="success" className="text-base">
            {stats.validated} Validated
          </Badge>
          <Badge variant="warning" className="text-base">
            {stats.corrections} Corrections
          </Badge>
          <Badge variant="outline" className="text-base">
            {stats.pending} Pending
          </Badge>
        </div>
      </div>

      {/* Validator Info */}
      <Card className="p-4 mb-6 bg-purple-50">
        <label className="block text-sm font-semibold mb-2 text-purple-900">
          Your Name (Optional - for audit trail)
        </label>
        <input
          type="text"
          placeholder="Enter your name or remain anonymous"
          value={validatorName}
          onChange={(e) => setValidatorName(e.target.value)}
          className="w-full max-w-md p-2 border rounded"
        />
      </Card>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Per-Term Validations */}
        <div>
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Term-Level Validation
          </h3>
          <div className="space-y-3">
            {validations.filter(v => v.type === 'term').map(validation => (
              <Card key={validation.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold">{validation.item}</p>
                    <p className="text-xs text-gray-500">Type: {validation.type}</p>
                  </div>
                  <Badge 
                    variant={
                      validation.status === 'validated' ? 'success' :
                      validation.status === 'needs_correction' ? 'warning' :
                      'outline'
                    }
                  >
                    {validation.status === 'validated' ? '✓ Validated' :
                     validation.status === 'needs_correction' ? '⚠ Needs Fix' :
                     'Pending'}
                  </Badge>
                </div>

                {validation.status === 'pending' && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleValidate(validation.id, true)}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      <Check className="w-4 h-4 mr-1" /> Validated
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleValidate(validation.id, false)}
                      className="flex-1 border-orange-600 text-orange-600 hover:bg-orange-50"
                    >
                      <X className="w-4 h-4 mr-1" /> Needs Correction
                    </Button>
                  </div>
                )}

                {activeValidation === validation.id && (
                  <div className="mt-3 pt-3 border-t">
                    <label className="block text-sm font-semibold mb-2">
                      Correction Note (Required)
                    </label>
                    <textarea
                      placeholder="Describe what needs to be corrected and why..."
                      value={correctionNote}
                      onChange={(e) => setCorrectionNote(e.target.value)}
                      className="w-full p-2 border rounded text-sm"
                      rows={3}
                    />
                    <div className="flex gap-2 mt-2">
                      <Button
                        size="sm"
                        onClick={() => handleCorrection(validation.id)}
                        className="bg-orange-600 hover:bg-orange-700"
                      >
                        Submit Correction
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setActiveValidation(null);
                          setCorrectionNote('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {validation.correction && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="font-semibold text-orange-900">Correction Note:</p>
                    <p className="text-gray-700 italic">{validation.correction}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      By: {validation.validator} | {validation.timestamp && new Date(validation.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}

                {validation.status === 'validated' && validation.validator && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="text-green-700">
                      <Check className="inline w-4 h-4 mr-1" />
                      Validated by: {validation.validator}
                    </p>
                    <p className="text-xs text-gray-500">
                      {validation.timestamp && new Date(validation.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>

        {/* Per-Figure Validations */}
        <div>
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-purple-600" />
            Figure-Level Validation
          </h3>
          <div className="space-y-3">
            {validations.filter(v => v.type === 'figure').map(validation => (
              <Card key={validation.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold">{validation.item}</p>
                    <p className="text-xs text-gray-500">Type: {validation.type}</p>
                  </div>
                  <Badge 
                    variant={
                      validation.status === 'validated' ? 'success' :
                      validation.status === 'needs_correction' ? 'warning' :
                      'outline'
                    }
                  >
                    {validation.status === 'validated' ? '✓ Validated' :
                     validation.status === 'needs_correction' ? '⚠ Needs Fix' :
                     'Pending'}
                  </Badge>
                </div>

                {validation.status === 'pending' && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleValidate(validation.id, true)}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      <Check className="w-4 h-4 mr-1" /> Validated
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleValidate(validation.id, false)}
                      className="flex-1 border-orange-600 text-orange-600 hover:bg-orange-50"
                    >
                      <X className="w-4 h-4 mr-1" /> Needs Correction
                    </Button>
                  </div>
                )}

                {activeValidation === validation.id && (
                  <div className="mt-3 pt-3 border-t">
                    <label className="block text-sm font-semibold mb-2">
                      Correction Note (Required)
                    </label>
                    <textarea
                      placeholder="Describe what needs to be corrected and why..."
                      value={correctionNote}
                      onChange={(e) => setCorrectionNote(e.target.value)}
                      className="w-full p-2 border rounded text-sm"
                      rows={3}
                    />
                    <div className="flex gap-2 mt-2">
                      <Button
                        size="sm"
                        onClick={() => handleCorrection(validation.id)}
                        className="bg-orange-600 hover:bg-orange-700"
                      >
                        Submit Correction
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setActiveValidation(null);
                          setCorrectionNote('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {validation.correction && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="font-semibold text-orange-900">Correction Note:</p>
                    <p className="text-gray-700 italic">{validation.correction}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      By: {validation.validator} | {validation.timestamp && new Date(validation.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}

                {validation.status === 'validated' && validation.validator && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="text-green-700">
                      <Check className="inline w-4 h-4 mr-1" />
                      Validated by: {validation.validator}
                    </p>
                    <p className="text-xs text-gray-500">
                      {validation.timestamp && new Date(validation.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Trail Summary */}
      <Card className="p-6 mb-8 bg-gray-50">
        <h3 className="font-bold mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Audit Trail Summary
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="font-semibold text-gray-700">Total Items</p>
            <p className="text-2xl font-bold text-purple-600">{validations.length}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-700">Validated</p>
            <p className="text-2xl font-bold text-green-600">{stats.validated}</p>
          </div>
          <div>
            <p className="font-semibold text-gray-700">Corrections Needed</p>
            <p className="text-2xl font-bold text-orange-600">{stats.corrections}</p>
          </div>
        </div>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={handleContinue}
          className="bg-purple-600 hover:bg-purple-700"
          disabled={stats.pending > 0}
        >
          Continue to Trait Toggles
        </Button>
      </div>
    </div>
  );
}
