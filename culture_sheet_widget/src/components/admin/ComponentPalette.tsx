import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Type, Image, Layout, Mail, Link2, Divide } from 'lucide-react';

interface ComponentPaletteProps {
  onAdd: (component: any) => void;
}

const components = [
  { type: 'heading', icon: Type, label: 'Heading', default: { text: 'Heading', size: 'h2' } },
  { type: 'text', icon: Type, label: 'Text', default: { text: 'Your text here' } },
  { type: 'image', icon: Image, label: 'Image', default: { src: '', alt: '', width: '100%' } },
  { type: 'button', icon: Mail, label: 'Button', default: { text: 'Click Here', url: '#' } },
  { type: 'divider', icon: Divide, label: 'Divider', default: { style: 'solid' } },
  { type: 'spacer', icon: Layout, label: 'Spacer', default: { height: 20 } },
];

export function ComponentPalette({ onAdd }: ComponentPaletteProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Components</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {components.map((comp) => (
          <Button
            key={comp.type}
            variant="outline"
            className="w-full justify-start"
            onClick={() => onAdd({ ...comp.default, type: comp.type, id: Date.now() })}
          >
            <comp.icon className="h-4 w-4 mr-2" />
            {comp.label}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
