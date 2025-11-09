import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface TemplatePreviewProps {
  components: any[];
  subject: string;
  style: string;
}

export function TemplatePreview({ components, subject, style }: TemplatePreviewProps) {
  const getStyleClasses = () => {
    if (style === 'victorian') return 'bg-[#FFF8DC] border-[#8B0000] border-4';
    if (style === 'modern') return 'bg-white border-gray-200';
    return 'bg-gray-50 border-gray-300';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Preview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`p-8 border-2 rounded ${getStyleClasses()}`}>
          <div className="mb-4 font-bold text-lg">{subject || 'Subject Line'}</div>
          {components.map((comp) => (
            <div key={comp.id} className="mb-4">
              {comp.type === 'heading' && <h2 className="text-2xl font-bold">{comp.text}</h2>}
              {comp.type === 'text' && <p>{comp.text}</p>}
              {comp.type === 'button' && (
                <button className="bg-blue-600 text-white px-6 py-2 rounded">{comp.text}</button>
              )}
              {comp.type === 'divider' && <hr className="my-4" />}
              {comp.type === 'spacer' && <div style={{ height: comp.height }} />}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
