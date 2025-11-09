import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { exportToPDF, PDFOptions } from '../../lib/pdfExport';
import { Download } from 'lucide-react';

interface Props {
  elementId: string;
  filename: string;
}

export const PDFExportOptions: React.FC<Props> = ({ elementId, filename }) => {
  const [options, setOptions] = useState<PDFOptions>({
    pageSize: 'letter',
    orientation: 'portrait',
    quality: 2,
  });
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    await exportToPDF(elementId, filename, options);
    setExporting(false);
  };

  return (
    <div className="flex gap-3 items-center flex-wrap">
      <Select value={options.pageSize} onValueChange={(v: any) => setOptions({...options, pageSize: v})}>
        <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value="letter">Letter</SelectItem><SelectItem value="a4">A4</SelectItem></SelectContent>
      </Select>
      <Select value={options.orientation} onValueChange={(v: any) => setOptions({...options, orientation: v})}>
        <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value="portrait">Portrait</SelectItem><SelectItem value="landscape">Landscape</SelectItem></SelectContent>
      </Select>
      <Button onClick={handleExport} disabled={exporting}><Download className="w-4 h-4 mr-2" />{exporting ? 'Exporting...' : 'Export PDF'}</Button>
    </div>
  );
};
