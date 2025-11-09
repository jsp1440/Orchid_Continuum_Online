import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { LoginForm } from './LoginForm';
import { SignupForm } from './SignupForm';
import { PasswordResetForm } from './PasswordResetForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'signup' | 'reset';
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState<'login' | 'signup' | 'reset'>(initialMode);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {mode === 'login' && 'Sign In'}
            {mode === 'signup' && 'Create Account'}
            {mode === 'reset' && 'Reset Password'}
          </DialogTitle>
        </DialogHeader>
        {mode === 'login' && (
          <LoginForm
            onSwitchToSignup={() => setMode('signup')}
            onSwitchToReset={() => setMode('reset')}
            onClose={onClose}
          />
        )}
        {mode === 'signup' && (
          <SignupForm onSwitchToLogin={() => setMode('login')} onClose={onClose} />
        )}
        {mode === 'reset' && (
          <PasswordResetForm onSwitchToLogin={() => setMode('login')} />
        )}
      </DialogContent>
    </Dialog>
  );
};
