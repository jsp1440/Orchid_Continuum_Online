import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Sparkles } from 'lucide-react';

interface AcknowledgmentModalProps {
  open: boolean;
  speciesName: string;
  onClose: () => void;
}

export function AcknowledgmentModal({ open, speciesName, onClose }: AcknowledgmentModalProps) {
  const [userName, setUserName] = useState('');
  const [showCredits, setShowCredits] = useState(false);

  const handleSubmit = () => {
    if (userName.trim()) {
      setShowCredits(true);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl text-center flex items-center justify-center gap-2">
            {showCredits ? (
              <>
                <Sparkles className="w-6 h-6 text-yellow-500" />
                Continuum Sequence Complete!
                <Sparkles className="w-6 h-6 text-yellow-500" />
              </>
            ) : (
              'Complete Your Creation'
            )}
          </DialogTitle>
        </DialogHeader>

        {!showCredits ? (
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Enter your name to continue the sequence</Label>
              <Input
                id="name"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                placeholder="Your name"
                className="mt-2"
              />
            </div>
            <Button onClick={handleSubmit} className="w-full" disabled={!userName.trim()}>
              Continue the Sequence
            </Button>
          </div>
        ) : (
          <div className="space-y-6 text-center">
            <p className="text-lg leading-relaxed">
              <strong>{userName}</strong> continued the living sequence of discovery through 
              The Orchid Continuum, illuminating a new expression of <em>{speciesName}</em>.
            </p>
            
            <div className="bg-gradient-to-br from-green-50 to-blue-50 p-6 rounded-lg text-left space-y-4 border-2 border-green-200">
              <p className="text-sm font-medium text-center">
                Through your participation, the Continuum Sequence advances — proving that both 
                orchids and ideas continue to evolve through those who study them.
              </p>
              
              <div className="space-y-2 text-sm">
                <p><strong>1850s-1900s:</strong> Original Botanists & Collectors</p>
                <p><strong>1875-2025:</strong> Herbarium Curators (MoBot/Tropicos)</p>
                <p><strong>1885-1906:</strong> Botanical Illustrators (Lindenia)</p>
                <p><strong>2000s-Present:</strong> Digital Archivists (GBIF/EOL/iNat)</p>
                <p><strong>2024-2025:</strong> Database Engineers (FCOS/Orchid Continuum)</p>
                <p><strong>2025:</strong> Educational Designers (NAOCC Orchid-Gami)</p>
                <p className="pt-2 border-t-2 border-green-300"><strong>Today:</strong> <strong>{userName}</strong> — The next expression in the sequence</p>
              </div>
            </div>

            <p className="text-sm italic text-muted-foreground">
              "The Continuum Sequence never ends — it only transforms."
            </p>

            <Button onClick={onClose} className="w-full">
              Close
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

