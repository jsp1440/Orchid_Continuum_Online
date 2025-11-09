import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../lib/supabase';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Trash2, FileText, Download, Eye } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';

interface SavedSheet {
  id: string;
  orchid_name: string;
  sheet_data: any;
  created_at: string;
  updated_at: string;
}

interface UserDashboardProps {
  onLoadSheet?: (sheetData: any) => void;
}

export const UserDashboard: React.FC<UserDashboardProps> = ({ onLoadSheet }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [savedSheets, setSavedSheets] = useState<SavedSheet[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadSavedSheets();
    }
  }, [user]);

  const loadSavedSheets = async () => {
    try {
      const { data, error } = await supabase
        .from('saved_culture_sheets')
        .select('*')
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false });
      
      if (error) throw error;
      setSavedSheets(data || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const deleteSheet = async (id: string) => {
    if (!confirm('Are you sure you want to delete this culture sheet?')) return;
    
    try {
      const { error } = await supabase
        .from('saved_culture_sheets')
        .delete()
        .eq('id', id);
      
      if (error) throw error;
      
      setSavedSheets(savedSheets.filter(s => s.id !== id));
      toast({
        title: 'Success',
        description: 'Culture sheet deleted successfully',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleLoadSheet = (sheet: SavedSheet) => {
    if (onLoadSheet) {
      onLoadSheet(sheet.sheet_data);
      toast({
        title: 'Success',
        description: 'Culture sheet loaded successfully',
      });
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading your culture sheets...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">My Saved Culture Sheets</h2>
      {savedSheets.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            No saved culture sheets yet. Generate and save your first one!
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {savedSheets.map(sheet => (
            <Card key={sheet.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FileText className="h-5 w-5" />
                  {sheet.orchid_name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600">
                  Created: {new Date(sheet.created_at).toLocaleDateString()}
                </p>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleLoadSheet(sheet)}
                    className="flex-1"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Load
                  </Button>
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={() => deleteSheet(sheet.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
