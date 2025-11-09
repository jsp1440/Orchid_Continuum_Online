import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';

interface ProtectedRouteProps {
  children: React.ReactNode;
  onShowAuth: () => void;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, onShowAuth }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto text-center py-12 space-y-4">
        <h2 className="text-2xl font-bold">Sign In Required</h2>
        <p className="text-gray-600">Please sign in to access this feature</p>
        <Button onClick={onShowAuth}>Sign In</Button>
      </div>
    );
  }

  return <>{children}</>;
};
