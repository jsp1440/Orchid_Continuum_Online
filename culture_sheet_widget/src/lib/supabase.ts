import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-key';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type Database = {
  public: {
    Tables: {
      saved_culture_sheets: {
        Row: {
          id: string;
          user_id: string;
          species_id: string;
          species_name: string;
          sections: any;
          location: any;
          theme: string;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['saved_culture_sheets']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['saved_culture_sheets']['Insert']>;
      };
      user_profiles: {
        Row: {
          id: string;
          user_id: string;
          favorite_orchids: string[];
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['user_profiles']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['user_profiles']['Insert']>;
      };
    };
  };
};
