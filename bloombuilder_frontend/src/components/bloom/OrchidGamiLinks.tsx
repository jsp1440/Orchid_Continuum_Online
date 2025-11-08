import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';

const links = [
  { title: 'NAOCC Orchid-Gami Overview', url: '#' },
  { title: 'Folding Guides (PDF Index)', url: '#' },
  { title: 'Teacher Resources', url: '#' }
];

export function OrchidGamiLinks() {
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Orchid-Gami Quick Links</h3>
      <div className="space-y-2">
        {links.map((link, idx) => (
          <Button
            key={idx}
            variant="ghost"
            size="sm"
            className="w-full justify-between"
            onClick={() => window.open(link.url, '_blank')}
          >
            <span className="text-xs">{link.title}</span>
            <ExternalLink className="w-3 h-3" />
          </Button>
        ))}
      </div>
    </Card>
  );
}
