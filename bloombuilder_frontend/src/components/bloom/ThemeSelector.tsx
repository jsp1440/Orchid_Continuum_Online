import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useTheme, ThemeMode } from '@/contexts/ThemeContext';

const themes: { id: ThemeMode; name: string; desc: string }[] = [
  { id: 'modern', name: 'Modern Scientific', desc: 'Crisp, minimal' },
  { id: 'victorian', name: 'Victorian Naturalist', desc: 'Journal tone, sepia' },
  { id: 'regency', name: 'Regency Botanical Salon', desc: 'Elegant, pastel' },
  { id: 'fantasy', name: 'Fantasy Conservatory', desc: 'Ethereal, art nouveau' },
  { id: 'ecofuturist', name: 'Eco-Futurist', desc: 'Holographic, teal' }
];

export function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Era / Voice Theme</h3>
      <div className="space-y-2">
        {themes.map((t) => (
          <Button
            key={t.id}
            variant={theme === t.id ? 'default' : 'outline'}
            onClick={() => setTheme(t.id)}
            className="w-full justify-start text-left"
            size="sm"
          >
            <div>
              <div className="font-medium text-sm">{t.name}</div>
              <div className="text-xs opacity-70">{t.desc}</div>
            </div>
          </Button>
        ))}
      </div>
    </Card>
  );
}
