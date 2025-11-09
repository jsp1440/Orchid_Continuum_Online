import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Trash2, ChevronUp, ChevronDown } from 'lucide-react';

interface TemplateCanvasProps {
  components: any[];
  onChange: (components: any[]) => void;
}

export function TemplateCanvas({ components, onChange }: TemplateCanvasProps) {
  const updateComponent = (id: number, field: string, value: any) => {
    onChange(components.map(c => c.id === id ? { ...c, [field]: value } : c));
  };

  const moveComponent = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= components.length) return;
    const newComponents = [...components];
    [newComponents[index], newComponents[newIndex]] = [newComponents[newIndex], newComponents[index]];
    onChange(newComponents);
  };

  const removeComponent = (id: number) => {
    onChange(components.filter(c => c.id !== id));
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-4 min-h-[400px]">
        {components.length === 0 && (
          <div className="text-center text-muted-foreground py-20">
            Drag components here to build your email template
          </div>
        )}
        {components.map((comp, idx) => (
          <div key={comp.id} className="border rounded p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold capitalize">{comp.type}</span>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => moveComponent(idx, 'up')}><ChevronUp className="h-4 w-4" /></Button>
                <Button size="sm" variant="ghost" onClick={() => moveComponent(idx, 'down')}><ChevronDown className="h-4 w-4" /></Button>
                <Button size="sm" variant="ghost" onClick={() => removeComponent(comp.id)}><Trash2 className="h-4 w-4" /></Button>
              </div>
            </div>
            {comp.type === 'heading' && <Input value={comp.text} onChange={(e) => updateComponent(comp.id, 'text', e.target.value)} />}
            {comp.type === 'text' && <Input value={comp.text} onChange={(e) => updateComponent(comp.id, 'text', e.target.value)} />}
            {comp.type === 'button' && (
              <div className="space-y-2">
                <Input placeholder="Button text" value={comp.text} onChange={(e) => updateComponent(comp.id, 'text', e.target.value)} />
                <Input placeholder="URL" value={comp.url} onChange={(e) => updateComponent(comp.id, 'url', e.target.value)} />
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
