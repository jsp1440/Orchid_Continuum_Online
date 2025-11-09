import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export function VersionHistory() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Version History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between items-center p-2 border rounded">
            <div>
              <div className="font-semibold">Version 1</div>
              <div className="text-sm text-muted-foreground">Created 2 days ago</div>
            </div>
            <Button size="sm" variant="outline">Restore</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
