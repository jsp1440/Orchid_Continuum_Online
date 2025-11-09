import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmailMetricsChart } from './EmailMetricsChart';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Mail, MousePointerClick, Eye, UserX, Download, FileText } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { exportToCSV } from '@/lib/exportUtils';
import { exportToPDF } from '@/lib/adminPdfExport';
import { EmailTemplateBuilder } from './EmailTemplateBuilder';
import { ABTestDashboard } from './ABTestDashboard';


interface EmailLog {
  id: string;
  email_type: string;
  template_style?: string;
  recipient_email: string;
  sent_at: string;
  email_analytics: Array<{
    event_type: string;
    created_at: string;
  }>;
}

export function AdminDashboard() {
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [emailType, setEmailType] = useState('all');
  const [templateStyle, setTemplateStyle] = useState('all');

  useEffect(() => {
    loadAnalytics();
  }, [startDate, endDate, emailType, templateStyle]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase.functions.invoke('get-email-analytics', {
        body: { 
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          emailType: emailType !== 'all' ? emailType : undefined,
          templateStyle: templateStyle !== 'all' ? templateStyle : undefined
        }
      });

      if (error) throw error;
      setEmailLogs(data?.data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const calculateMetrics = () => {
    const totalSent = emailLogs.length;
    const totalOpened = emailLogs.filter(log => 
      log.email_analytics?.some(a => a.event_type === 'open')
    ).length;
    const totalClicked = emailLogs.filter(log => 
      log.email_analytics?.some(a => a.event_type === 'click')
    ).length;
    const totalUnsubscribed = emailLogs.filter(log => 
      log.email_analytics?.some(a => a.event_type === 'unsubscribe')
    ).length;

    return {
      totalSent,
      openRate: totalSent > 0 ? ((totalOpened / totalSent) * 100).toFixed(1) : '0',
      clickRate: totalSent > 0 ? ((totalClicked / totalSent) * 100).toFixed(1) : '0',
      unsubscribeRate: totalSent > 0 ? ((totalUnsubscribed / totalSent) * 100).toFixed(1) : '0'
    };
  };

  const handleExportCSV = () => {
    const exportData = emailLogs.map(log => ({
      id: log.id,
      email_type: log.email_type,
      template_style: log.template_style,
      recipient_email: log.recipient_email,
      sent_at: log.sent_at,
      opened: log.email_analytics?.some(a => a.event_type === 'open') || false,
      clicked: log.email_analytics?.some(a => a.event_type === 'click') || false,
      unsubscribed: log.email_analytics?.some(a => a.event_type === 'unsubscribe') || false,
      open_count: log.email_analytics?.filter(a => a.event_type === 'open').length || 0,
      click_count: log.email_analytics?.filter(a => a.event_type === 'click').length || 0
    }));
    exportToCSV(exportData, `email-analytics-${new Date().toISOString().split('T')[0]}.csv`);
  };

  const handleExportPDF = () => {
    const metrics = calculateMetrics();
    const exportData = emailLogs.map(log => ({
      id: log.id,
      email_type: log.email_type,
      template_style: log.template_style,
      recipient_email: log.recipient_email,
      sent_at: log.sent_at,
      opened: log.email_analytics?.some(a => a.event_type === 'open') || false,
      clicked: log.email_analytics?.some(a => a.event_type === 'click') || false,
      unsubscribed: log.email_analytics?.some(a => a.event_type === 'unsubscribe') || false,
      open_count: log.email_analytics?.filter(a => a.event_type === 'open').length || 0,
      click_count: log.email_analytics?.filter(a => a.event_type === 'click').length || 0
    }));
    
    const dateRange = startDate && endDate 
      ? `${new Date(startDate).toLocaleDateString()} - ${new Date(endDate).toLocaleDateString()}`
      : 'All time';
    
    exportToPDF(exportData, { ...metrics, dateRange }, `email-analytics-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const getChartData = () => {
    const dateMap = new Map<string, { sent: number; opened: number; clicked: number }>();
    
    emailLogs.forEach(log => {
      const date = new Date(log.sent_at).toLocaleDateString();
      const existing = dateMap.get(date) || { sent: 0, opened: 0, clicked: 0 };
      
      existing.sent++;
      if (log.email_analytics?.some(a => a.event_type === 'open')) existing.opened++;
      if (log.email_analytics?.some(a => a.event_type === 'click')) existing.clicked++;
      
      dateMap.set(date, existing);
    });

    return Array.from(dateMap.entries())
      .map(([date, metrics]) => ({ date, ...metrics }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const metrics = calculateMetrics();

  if (loading) {
    return <div className="p-8">Loading analytics...</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <div className="flex gap-2">
          <Button onClick={handleExportCSV} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={handleExportPDF} variant="outline">
            <FileText className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="analytics">
        <TabsList>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="templates">Email Templates</TabsTrigger>
          <TabsTrigger value="abtesting">A/B Testing</TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Filters</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label>Start Date</Label>
                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div>
                <Label>End Date</Label>
                <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
              <div>
                <Label>Email Type</Label>
                <Select value={emailType} onValueChange={setEmailType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="confirmation">Confirmation</SelectItem>
                    <SelectItem value="digest">Weekly Digest</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Template Style</Label>
                <Select value={templateStyle} onValueChange={setTemplateStyle}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Styles</SelectItem>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="modern">Modern</SelectItem>
                    <SelectItem value="classic">Classic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Sent</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.totalSent}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Open Rate</CardTitle>
                <Eye className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.openRate}%</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Click Rate</CardTitle>
                <MousePointerClick className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.clickRate}%</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Unsubscribe Rate</CardTitle>
                <UserX className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.unsubscribeRate}%</div>
              </CardContent>
            </Card>
          </div>

          <EmailMetricsChart data={getChartData()} />
        </TabsContent>

        <TabsContent value="templates">
          <EmailTemplateBuilder />
        </TabsContent>

        <TabsContent value="abtesting">
          <ABTestDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
}
