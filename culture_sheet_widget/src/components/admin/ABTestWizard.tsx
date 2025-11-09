import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

interface ABTestWizardProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (test: any) => void;
  templates: Array<{ id: string; name: string }>;
}

export function ABTestWizard({ open, onClose, onSubmit, templates }: ABTestWizardProps) {
  const [step, setStep] = useState(1);
  const [testName, setTestName] = useState('');
  const [variantA, setVariantA] = useState('');
  const [variantB, setVariantB] = useState('');
  const [splitPercentage, setSplitPercentage] = useState([50]);
  const [successMetric, setSuccessMetric] = useState('open_rate');
  const [duration, setDuration] = useState(7);
  const [endDate, setEndDate] = useState<Date>();

  const handleSubmit = () => {
    onSubmit({
      name: testName,
      variantA,
      variantB,
      splitPercentage: splitPercentage[0],
      successMetric,
      duration,
      endDate,
      status: 'running',
    });
    onClose();
    resetForm();
  };

  const resetForm = () => {
    setStep(1);
    setTestName('');
    setVariantA('');
    setVariantB('');
    setSplitPercentage([50]);
    setSuccessMetric('open_rate');
    setDuration(7);
    setEndDate(undefined);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create A/B Test - Step {step} of 3</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="testName">Test Name</Label>
              <Input id="testName" value={testName} onChange={(e) => setTestName(e.target.value)} placeholder="Welcome Email Test" />
            </div>
            <div>
              <Label htmlFor="variantA">Variant A (Control)</Label>
              <Select value={variantA} onValueChange={setVariantA}>
                <SelectTrigger>
                  <SelectValue placeholder="Select template" />
                </SelectTrigger>
                <SelectContent>
                  {templates.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="variantB">Variant B (Test)</Label>
              <Select value={variantB} onValueChange={setVariantB}>
                <SelectTrigger>
                  <SelectValue placeholder="Select template" />
                </SelectTrigger>
                <SelectContent>
                  {templates.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div>
              <Label>Traffic Split: {splitPercentage[0]}% / {100 - splitPercentage[0]}%</Label>
              <Slider value={splitPercentage} onValueChange={setSplitPercentage} min={10} max={90} step={5} className="mt-2" />
            </div>
            <div>
              <Label htmlFor="metric">Success Metric</Label>
              <Select value={successMetric} onValueChange={setSuccessMetric}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open_rate">Open Rate</SelectItem>
                  <SelectItem value="click_rate">Click Rate</SelectItem>
                  <SelectItem value="conversion_rate">Conversion Rate</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="duration">Test Duration (days)</Label>
              <Input id="duration" type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} min={1} max={30} />
            </div>
            <div>
              <Label>End Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, 'PPP') : 'Pick a date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent><Calendar mode="single" selected={endDate} onSelect={setEndDate} /></PopoverContent>
              </Popover>
            </div>
          </div>
        )}

        <div className="flex justify-between mt-6">
          <Button variant="outline" onClick={() => step > 1 ? setStep(step - 1) : onClose()}>
            {step === 1 ? 'Cancel' : 'Back'}
          </Button>
          <Button onClick={() => step < 3 ? setStep(step + 1) : handleSubmit()} disabled={step === 1 && (!testName || !variantA || !variantB)}>
            {step === 3 ? 'Create Test' : 'Next'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
