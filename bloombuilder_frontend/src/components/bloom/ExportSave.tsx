import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, Save, FileImage, Award, Users } from 'lucide-react';
import { Species } from '@/types/bloombuilder';

interface ExportSaveProps {
  species: Species;
  workflowData: any;
  onComplete: () => void;
  onBack: () => void;
}

export function ExportSave({ species, workflowData, onComplete, onBack }: ExportSaveProps) {
  const [exportFormat, setExportFormat] = useState<'png' | 'jpg'>('png');
  const [includeAudit, setIncludeAudit] = useState(true);
  const [includeCredits, setIncludeCredits] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const handleExport = () => {
    // In real app, this would generate actual image with html2canvas or similar
    setExportSuccess(true);
    setTimeout(() => setExportSuccess(false), 3000);
  };

  const handleSave = () => {
    setSaving(true);
    
    // Simulate API call to save validation record
    setTimeout(() => {
      setSaving(false);
      alert('Validation record saved successfully!');
    }, 1500);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Export & Save</h2>
        <p className="text-gray-600 mb-4">
          Export your assembled bloom with audit trail and contributor credits. Save your validation record to the Verified Orchid Directory.
        </p>
        {exportSuccess && (
          <Badge variant="success" className="text-base">
            <Download className="w-4 h-4 mr-2" />
            Export Complete!
          </Badge>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Preview */}
        <div>
          <Card className="p-6">
            <h3 className="font-bold mb-4">Export Preview</h3>
            <div className="bg-gradient-to-br from-purple-50 to-white rounded-lg p-8 border-2 border-purple-200">
              {/* Main Image */}
              <div className="bg-white rounded-lg p-4 mb-4 shadow-lg">
                <div className="aspect-square bg-gray-100 rounded flex items-center justify-center mb-3">
                  <svg width="200" height="200" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="15" fill="#FFD700" />
                    {[0, 60, 120, 180, 240, 300].map((angle, i) => (
                      <ellipse
                        key={i}
                        cx="100"
                        cy="50"
                        rx="20"
                        ry="40"
                        fill="#E6B3FF"
                        transform={`rotate(${angle} 100 100)`}
                      />
                    ))}
                  </svg>
                </div>
                
                <div className="text-center">
                  <p className="font-bold text-lg text-purple-900">
                    {species.scientificName}
                  </p>
                  <p className="text-sm text-gray-600">
                    {species.commonName || 'Orchidaceae'}
                  </p>
                </div>
              </div>

              {/* Audit Trail */}
              {includeAudit && (
                <div className="bg-white rounded-lg p-3 mb-3 text-xs">
                  <p className="font-semibold mb-1">Validation Audit Trail</p>
                  <p className="text-gray-600">✓ 4 herbarium sheets reviewed</p>
                  <p className="text-gray-600">✓ 3 botanical plates analyzed</p>
                  <p className="text-gray-600">✓ Dichotomous key completed</p>
                  <p className="text-gray-600">✓ 5 structures validated</p>
                </div>
              )}

              {/* Credits */}
              {includeCredits && (
                <div className="bg-white rounded-lg p-3 text-xs">
                  <p className="font-semibold mb-1 flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    Contributors
                  </p>
                  <p className="text-gray-600">Honoring 587+ contributors across 43 years (1982-2025)</p>
                  <p className="text-gray-600 mt-1">Sources: GBIF, Missouri Botanical Garden, Biodiversity Heritage Library</p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Export Options */}
        <div className="space-y-4">
          <Card className="p-4">
            <h3 className="font-bold mb-3 flex items-center gap-2">
              <FileImage className="w-5 h-5 text-purple-600" />
              Export Format
            </h3>
            <div className="flex gap-2 mb-4">
              <Button
                onClick={() => setExportFormat('png')}
                variant={exportFormat === 'png' ? 'default' : 'outline'}
                className={exportFormat === 'png' ? 'flex-1 bg-purple-600' : 'flex-1'}
              >
                PNG
              </Button>
              <Button
                onClick={() => setExportFormat('jpg')}
                variant={exportFormat === 'jpg' ? 'default' : 'outline'}
                className={exportFormat === 'jpg' ? 'flex-1 bg-purple-600' : 'flex-1'}
              >
                JPG
              </Button>
            </div>

            <div className="space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAudit}
                  onChange={(e) => setIncludeAudit(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Include Audit Trail</span>
              </label>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeCredits}
                  onChange={(e) => setIncludeCredits(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Include Contributor Credits</span>
              </label>
            </div>

            <Button
              onClick={handleExport}
              className="w-full mt-4 bg-green-600 hover:bg-green-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Image ({exportFormat.toUpperCase()})
            </Button>
          </Card>

          <Card className="p-4">
            <h3 className="font-bold mb-3 flex items-center gap-2">
              <Save className="w-5 h-5 text-purple-600" />
              Save Validation Record
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Save your complete validation record to the Verified Orchid Directory. This will include:
            </p>
            <ul className="text-sm text-gray-700 space-y-1 mb-4">
              <li>• Selected species and materials</li>
              <li>• All label placements and notes</li>
              <li>• Dichotomous key path</li>
              <li>• Validation status and corrections</li>
              <li>• Your contributor information</li>
            </ul>

            <Button
              onClick={handleSave}
              className="w-full bg-purple-600 hover:bg-purple-700"
              disabled={saving}
            >
              {saving ? (
                <>Saving...</>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save to Directory
                </>
              )}
            </Button>
          </Card>

          <Card className="p-4 bg-gradient-to-br from-yellow-50 to-white border-yellow-200">
            <h3 className="font-bold mb-2 flex items-center gap-2 text-yellow-900">
              <Award className="w-5 h-5" />
              Congratulations!
            </h3>
            <p className="text-sm text-gray-700">
              You've completed a full BloomBuilder validation session! Your work contributes to a growing database of verified orchid identifications, honoring centuries of botanical research.
            </p>
          </Card>
        </div>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button
          onClick={onComplete}
          className="bg-purple-600 hover:bg-purple-700"
        >
          Complete Session
        </Button>
      </div>
    </div>
  );
}
