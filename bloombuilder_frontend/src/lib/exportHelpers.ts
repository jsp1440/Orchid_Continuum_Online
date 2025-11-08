import { TraitImageMetadata } from '@/types/bloombuilder';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export async function exportComparisonToPDF(images: TraitImageMetadata[]) {
  const pdf = new jsPDF('landscape');
  const pageWidth = pdf.internal.pageSize.getWidth();
  
  // Title Section
  pdf.setFontSize(20);
  pdf.setFont('helvetica', 'bold');
  pdf.text('Orchid Trait Comparison Report', pageWidth / 2, 15, { align: 'center' });
  
  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'normal');
  pdf.text(`Educational Analysis - Generated: ${new Date().toLocaleDateString()}`, pageWidth / 2, 22, { align: 'center' });
  
  // Educational Context
  pdf.setFontSize(9);
  pdf.text('This report compares orchid trait variations and their evolutionary adaptations to different pollinators.', 15, 30);
  
  let yPos = 38;
  
  // Add thumbnail images in a row
  const imgWidth = 70;
  const imgHeight = 52;
  const spacing = 8;
  const maxImgsPerRow = Math.floor((pageWidth - 30) / (imgWidth + spacing));
  
  for (let i = 0; i < Math.min(images.length, maxImgsPerRow); i++) {
    const img = images[i];
    const xPos = 15 + (i * (imgWidth + spacing));
    
    try {
      pdf.addImage(img.url, 'JPEG', xPos, yPos, imgWidth, imgHeight);
      pdf.setFontSize(8);
      pdf.text(img.name, xPos + imgWidth / 2, yPos + imgHeight + 4, { align: 'center', maxWidth: imgWidth });
    } catch (e) {
      pdf.rect(xPos, yPos, imgWidth, imgHeight);
      pdf.text('Image', xPos + imgWidth / 2, yPos + imgHeight / 2, { align: 'center' });
    }
  }
  
  yPos += imgHeight + 15;
  
  // Comparison Table
  const tableData = [
    ['Spur Length', ...images.map(img => img.spurLength)],
    ['Petal Color', ...images.map(img => img.petalColor)],
    ['Characteristics', ...images.map(img => img.characteristics || 'N/A')],
    ['Pollinator Type', ...images.map(img => img.pollinatorType || 'N/A')],
    ['Evolutionary Notes', ...images.map(img => img.evolutionaryNotes || 'N/A')]
  ];
  
  autoTable(pdf, {
    startY: yPos,
    head: [['Trait', ...images.map(img => img.name)]],
    body: tableData,
    theme: 'grid',
    styles: { fontSize: 8, cellPadding: 4, overflow: 'linebreak' },
    headStyles: { fillColor: [139, 92, 246], fontStyle: 'bold', fontSize: 9 },
    columnStyles: { 0: { fontStyle: 'bold', fillColor: [245, 245, 250] } },
    margin: { left: 15, right: 15 }
  });
  
  // Footer
  const finalY = (pdf as any).lastAutoTable.finalY || yPos + 50;
  pdf.setFontSize(8);
  pdf.setTextColor(100);
  pdf.text('Note: Trait differences highlight evolutionary adaptations to specific pollinator types.', 15, finalY + 10);
  
  pdf.save(`orchid-comparison-${Date.now()}.pdf`);
}

export function exportComparisonToCSV(images: TraitImageMetadata[]) {
  const headers = ['Trait', ...images.map(img => img.name)];
  const rows = [
    ['Spur Length', ...images.map(img => img.spurLength)],
    ['Petal Color', ...images.map(img => img.petalColor)],
    ['Characteristics', ...images.map(img => img.characteristics || 'N/A')],
    ['Pollinator Type', ...images.map(img => img.pollinatorType || 'N/A')],
    ['Evolutionary Notes', ...images.map(img => img.evolutionaryNotes || 'N/A')]
  ];
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `orchid-comparison-${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
