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

export function exportToCSV(data: EmailLogExport[], filename: string) {
  const headers = ['Email ID', 'Type', 'Template', 'Recipient', 'Sent At', 'Opened', 'Clicked', 'Unsubscribed', 'Opens', 'Clicks'];
  const rows = data.map(log => [
    log.id,
    log.email_type,
    log.template_style || 'default',
    log.recipient_email,
    new Date(log.sent_at).toLocaleString(),
    log.opened ? 'Yes' : 'No',
    log.clicked ? 'Yes' : 'No',
    log.unsubscribed ? 'Yes' : 'No',
    log.open_count.toString(),
    log.click_count.toString()
  ]);

  const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
