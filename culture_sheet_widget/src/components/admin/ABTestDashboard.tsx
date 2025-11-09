import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ABTestWizard } from './ABTestWizard';
import { ActiveTestCard } from './ActiveTestCard';
import { TestAnalytics } from './TestAnalytics';
import { Plus, FlaskConical } from 'lucide-react';
import { toast } from 'sonner';
import { supabase } from '@/lib/supabase';
import { calculateSignificance } from '@/lib/abTestingApi';


export function ABTestDashboard() {
  const [wizardOpen, setWizardOpen] = useState(false);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);

  const mockTemplates = [
    { id: '1', name: 'Welcome Email v1' },
    { id: '2', name: 'Welcome Email v2' },
    { id: '3', name: 'Newsletter Template' },
  ];

  const [activeTests, setActiveTests] = useState([
    {
      testId: 'test-1',
      name: 'Welcome Email Subject Line Test',
      status: 'running' as const,
      variantA: {
        name: 'Control',
        metrics: { sent: 1000, opened: 450, clicked: 120, converted: 45 },
      },
      variantB: {
        name: 'Test',
        metrics: { sent: 1000, opened: 520, clicked: 145, converted: 58 },
      },
      splitPercentage: 50,
      startDate: '2025-11-02',
      endDate: '2025-11-16',
      successMetric: 'open_rate' as const,
    },
  ]);

  const [completedTests, setCompletedTests] = useState([
    {
      testId: 'test-2',
      name: 'CTA Button Color Test',
      status: 'completed' as const,
      variantA: {
        name: 'Blue Button',
        metrics: { sent: 2000, opened: 900, clicked: 180, converted: 72 },
      },
      variantB: {
        name: 'Green Button',
        metrics: { sent: 2000, opened: 920, clicked: 240, converted: 96 },
      },
      splitPercentage: 50,
      startDate: '2025-10-20',
      endDate: '2025-11-03',
      successMetric: 'click_rate' as const,
    },
  ]);

  const handleCreateTest = async (test: any) => {
    try {
      // Insert test into database
      const { data: testData, error: testError } = await supabase
        .from('ab_tests')
        .insert({
          name: test.name,
          template_a_id: test.templateA,
          template_b_id: test.templateB,
          split_percentage: test.splitPercentage,
          success_metric: test.successMetric,
          start_date: test.startDate,
          end_date: test.endDate,
          status: 'running',
        })
        .select()
        .single();

      if (testError) throw testError;

      // Create variant records
      await supabase.from('ab_test_variants').insert([
        { test_id: testData.id, variant_name: 'A', template_id: test.templateA },
        { test_id: testData.id, variant_name: 'B', template_id: test.templateB },
      ]);

      setActiveTests([...activeTests, { ...test, testId: testData.id }]);
      toast.success('A/B test created successfully');
    } catch (error) {
      toast.error('Failed to create test');
      console.error(error);
    }
  };

  const handleStopTest = async (testId: string) => {
    try {
      await supabase
        .from('ab_tests')
        .update({ status: 'stopped' })
        .eq('id', testId);

      const test = activeTests.find(t => t.testId === testId);
      if (test) {
        setActiveTests(activeTests.filter(t => t.testId !== testId));
        setCompletedTests([...completedTests, { ...test, status: 'completed' as const }]);
        toast.info('Test stopped');
      }
    } catch (error) {
      toast.error('Failed to stop test');
    }
  };

  const handlePromoteWinner = (testId: string, variant: 'A' | 'B') => {
    toast.success(`Variant ${variant} promoted as default template`);
  };


  const mockTimeSeriesData = [
    { date: '11/2', variantA: 42, variantB: 48 },
    { date: '11/3', variantA: 44, variantB: 51 },
    { date: '11/4', variantA: 43, variantB: 52 },
    { date: '11/5', variantA: 45, variantB: 53 },
    { date: '11/6', variantA: 46, variantB: 52 },
  ];

  const mockSegmentData = [
    { segment: 'New Users', variantA: 38, variantB: 45 },
    { segment: 'Active Users', variantA: 52, variantB: 58 },
    { segment: 'Inactive Users', variantA: 28, variantB: 35 },
  ];

  if (selectedTest) {
    return (
      <div>
        <Button variant="ghost" onClick={() => setSelectedTest(null)} className="mb-4">
          ← Back to Tests
        </Button>
        <TestAnalytics
          testId={selectedTest}
          testName="Welcome Email Subject Line Test"
          timeSeriesData={mockTimeSeriesData}
          segmentData={mockSegmentData}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">A/B Testing</h2>
          <p className="text-muted-foreground">Create and monitor email template tests</p>
        </div>
        <Button onClick={() => setWizardOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Test
        </Button>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">
            <FlaskConical className="h-4 w-4 mr-2" />
            Active Tests ({activeTests.length})
          </TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedTests.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {activeTests.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg">
              <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No active tests. Create one to get started.</p>
            </div>
          ) : (
            activeTests.map(test => (
              <ActiveTestCard
                key={test.testId}
                {...test}
                onStop={handleStopTest}
                onPromote={handlePromoteWinner}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          {completedTests.map(test => (
            <div key={test.testId} onClick={() => setSelectedTest(test.testId)} className="cursor-pointer">
              <ActiveTestCard {...test} onStop={handleStopTest} onPromote={handlePromoteWinner} />
            </div>
          ))}
        </TabsContent>
      </Tabs>

      <ABTestWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSubmit={handleCreateTest}
        templates={mockTemplates}
      />
    </div>
  );
}
