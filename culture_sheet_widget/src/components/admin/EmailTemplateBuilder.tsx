import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Eye, Save, History } from 'lucide-react';
import { TemplateCanvas } from './TemplateCanvas';
import { ComponentPalette } from './ComponentPalette';
import { TemplatePreview } from './TemplatePreview';
import { VersionHistory } from './VersionHistory';

export function EmailTemplateBuilder() {
  const [name, setName] = useState('');
  const [emailType, setEmailType] = useState('confirmation');
  const [style, setStyle] = useState('default');
  const [subject, setSubject] = useState('');
  const [components, setComponents] = useState<any[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Email Template Builder</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Template Name</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
            <div><Label>Email Type</Label>
              <Select value={emailType} onValueChange={setEmailType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="confirmation">Confirmation</SelectItem>
                  <SelectItem value="digest">Weekly Digest</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label>Subject Line</Label><Input value={subject} onChange={(e) => setSubject(e.target.value)} /></div>
          <div><Label>Template Style</Label>
            <Select value={style} onValueChange={setStyle}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default</SelectItem>
                <SelectItem value="modern">Modern</SelectItem>
                <SelectItem value="victorian">Victorian</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-4 gap-6">
        <ComponentPalette onAdd={(c) => setComponents([...components, c])} />
        <div className="col-span-3">
          <TemplateCanvas components={components} onChange={setComponents} />
        </div>
      </div>

      <div className="flex gap-2">
        <Button onClick={() => setShowPreview(!showPreview)}><Eye className="h-4 w-4 mr-2" />Preview</Button>
        <Button><Save className="h-4 w-4 mr-2" />Save Template</Button>
        <Button variant="outline"><History className="h-4 w-4 mr-2" />Version History</Button>
      </div>

      {showPreview && <TemplatePreview components={components} subject={subject} style={style} />}
    </div>
  );
}
