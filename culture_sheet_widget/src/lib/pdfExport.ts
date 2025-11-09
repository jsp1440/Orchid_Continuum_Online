import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export interface PDFOptions {
  pageSize: 'letter' | 'a4';
  orientation: 'portrait' | 'landscape';
  quality: number;
}

export const exportToPDF = async (
  elementId: string,
  filename: string,
  options: PDFOptions
) => {
  const element = document.getElementById(elementId);
  if (!element) return;

  const canvas = await html2canvas(element, {
    scale: options.quality,
    useCORS: true,
    logging: false,
  });

  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF({
    orientation: options.orientation,
    unit: 'mm',
    format: options.pageSize,
  });

  const pdfWidth = pdf.internal.pageSize.getWidth();
  const pdfHeight = pdf.internal.pageSize.getHeight();
  const imgWidth = canvas.width;
  const imgHeight = canvas.height;
  const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
  const imgX = (pdfWidth - imgWidth * ratio) / 2;
  const imgY = 0;

  pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
  pdf.save(filename);
};
