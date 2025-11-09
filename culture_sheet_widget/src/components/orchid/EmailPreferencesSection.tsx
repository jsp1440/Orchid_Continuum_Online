import React, { useState, useEffect } from 'react';
import { Mail, Eye, Bell, BellOff } from 'lucide-react';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { EmailTemplatePreview } from './EmailTemplatePreview';
import { supabase } from '@/lib/supabase';
import { useToast } from '@/hooks/use-toast';

type EmailTemplate = 'minimal' | 'detailed' | 'botanical';

export const EmailPreferencesSection: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate>('detailed');
  const [emailNotificationsEnabled, setEmailNotificationsEnabled] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { data } = await supabase
      .from('user_profiles')
      .select('email_template_preference, email_notifications_enabled')
      .eq('id', user.id)
      .single();

    if (data) {
      if (data.email_template_preference) {
        setSelectedTemplate(data.email_template_preference as EmailTemplate);
      }
      if (data.email_notifications_enabled !== undefined) {
        setEmailNotificationsEnabled(data.email_notifications_enabled);
      }
    }
  };

  const savePreferences = async () => {
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase
      .from('user_profiles')
      .upsert({ 
        id: user.id, 
        email_template_preference: selectedTemplate,
        email_notifications_enabled: emailNotificationsEnabled,
        updated_at: new Date().toISOString()
      });

    if (error) {
      toast({ title: 'Error', description: 'Failed to save preferences', variant: 'destructive' });
    } else {
      toast({ title: 'Saved', description: 'Email preferences updated successfully' });
    }
    setLoading(false);
  };

  const templates: { id: EmailTemplate; name: string; desc: string }[] = [
    { id: 'minimal', name: 'Minimal', desc: 'Clean and simple' },
    { id: 'detailed', name: 'Detailed', desc: 'Rich information' },
    { id: 'botanical', name: 'Botanical', desc: 'Nature-inspired' }
  ];

  return (
    <div className="space-y-6">
      {/* Weekly Digest Toggle */}
      <div className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {emailNotificationsEnabled ? <Bell className="h-5 w-5 text-green-600" /> : <BellOff className="h-5 w-5 text-gray-400" />}
            <div>
              <h3 className="text-lg font-semibold">Weekly Digest Emails</h3>
              <p className="text-sm text-gray-600">Receive care reminders for your saved orchids</p>
            </div>
          </div>
          <Switch 
            checked={emailNotificationsEnabled}
            onCheckedChange={setEmailNotificationsEnabled}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2 ml-8">
          Note: Confirmation emails when saving culture sheets will still be sent
        </p>
      </div>

      {/* Template Style Selection */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Mail className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Email Template Style</h3>
        </div>
        <div className="grid grid-cols-3 gap-3 mb-4">
          {templates.map(t => (
            <button
              key={t.id}
              onClick={() => setSelectedTemplate(t.id)}
              className={`p-3 rounded-lg border-2 transition-all ${selectedTemplate === t.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-400'}`}
            >
              <div className="text-sm font-medium">{t.name}</div>
              <div className="text-xs text-gray-600">{t.desc}</div>
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowPreview(!showPreview)} variant="outline" size="sm">
            <Eye className="h-4 w-4 mr-1" /> {showPreview ? 'Hide' : 'Show'} Preview
          </Button>
          <Button onClick={savePreferences} disabled={loading} size="sm">
            {loading ? 'Saving...' : 'Save Preferences'}
          </Button>
        </div>
        {showPreview && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm font-medium mb-3">Email Preview:</p>
            <EmailTemplatePreview template={selectedTemplate} />
          </div>
        )}
      </div>
    </div>
  );
};
