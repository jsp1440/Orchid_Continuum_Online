import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface EmailLogExport {
  id: string;
  email_type: string;
  template_style?: string;
  recipient_email: string;
  sent_at: string;
  opened: boolean;
  clicked: boolean;
  unsubscribed: boolean;
  open_count: number;
  click_count: number;
}

interface MetricsSummary {
  totalSent: number;
  openRate: string;
  clickRate: string;
  unsubscribeRate: string;
  dateRange: string;
}

export function exportToPDF(data: EmailLogExport[], metrics: MetricsSummary, filename: string) {
  const doc = new jsPDF();
  
  // Title
  doc.setFontSize(20);
  doc.text('Email Analytics Report', 14, 20);
  
  // Date range
  doc.setFontSize(10);
  doc.text(metrics.dateRange, 14, 28);
  
  // Summary metrics
  doc.setFontSize(12);
  doc.text('Summary Metrics', 14, 40);
  doc.setFontSize(10);
  doc.text(`Total Emails Sent: ${metrics.totalSent}`, 14, 48);
  doc.text(`Open Rate: ${metrics.openRate}%`, 14, 55);
  doc.text(`Click Rate: ${metrics.clickRate}%`, 14, 62);
  doc.text(`Unsubscribe Rate: ${metrics.unsubscribeRate}%`, 14, 69);
  
  // Email logs table
  const tableData = data.map(log => [
    log.email_type,
    log.template_style || 'default',
    new Date(log.sent_at).toLocaleDateString(),
    log.opened ? 'Yes' : 'No',
    log.clicked ? 'Yes' : 'No',
    log.open_count.toString(),
    log.click_count.toString()
  ]);
  
  autoTable(doc, {
    startY: 80,
    head: [['Type', 'Template', 'Sent Date', 'Opened', 'Clicked', 'Opens', 'Clicks']],
    body: tableData,
    theme: 'grid',
    headStyles: { fillColor: [99, 102, 241] }
  });
  
  doc.save(filename);
}
