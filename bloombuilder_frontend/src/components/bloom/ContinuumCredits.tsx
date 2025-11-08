import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

const credits = [
  { era: 'Original Botanists & Collectors', period: '1850s–1900s' },
  { era: 'Herbarium Curators', period: 'MoBot/Tropicos' },
  { era: 'Botanical Illustrators', period: 'Lindenia (1885–1906)' },
  { era: 'Digital Archivists', period: 'GBIF/EOL/iNat' },
  { era: 'Database Engineers', period: 'FCOS/Orchid Continuum' },
  { era: 'Educational Designers', period: 'NAOCC Orchid-Gami' }
];

export function ContinuumCredits() {
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Continuum Credits</h3>
      <ScrollArea className="h-48">
        <div className="space-y-2">
          {credits.map((credit, idx) => (
            <div key={idx} className="text-sm border-l-2 border-primary/30 pl-3 py-1">
              <div className="font-medium">{credit.era}</div>
              <div className="text-xs text-muted-foreground">{credit.period}</div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </Card>
  );
}
