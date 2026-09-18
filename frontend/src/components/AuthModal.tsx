import React, { useState } from 'react';
import {
  X,
  Lock,
  Mail,
  UserPlus,
  LogIn,
  AlertCircle,
} from 'lucide-react';
import {
  signInWithEmail,
  signUpWithEmail,
  signInWithGoogle,
} from '../api/firebase';
import { useAuthStore } from '../store/useAuthStore';
import { Risk2ReliefLogo } from './Risk2ReliefLogo';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal } = useAuthStore();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const getFriendlyErrorMessage = (err: any): string => {
    const code = err?.code || '';
    if (code === 'auth/invalid-credential' || code === 'auth/wrong-password' || code === 'auth/user-not-found') {
      return 'Invalid email address or password. Please verify your credentials.';
    }
    if (code === 'auth/email-already-in-use') {
      return 'This email address is already registered. Please sign in instead.';
    }
    if (code === 'auth/weak-password') {
      return 'Password must be at least 6 characters long.';
    }
    if (code === 'auth/popup-closed-by-user') {
      return 'Google sign-in popup was closed before completion.';
    }
    if (code === 'auth/network-request-failed') {
      return 'Network connection error. Please check your internet connectivity.';
    }
    return err?.message || 'Authentication failed. Please try again.';
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (!email || !password) {
      setLocalError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
      } else {
        await signInWithEmail(email, password);
      }
      closeAuthModal();
      setEmail('');
      setPassword('');
    } catch (err: any) {
      setLocalError(getFriendlyErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLocalError(null);
    setLoading(true);
    try {
      await signInWithGoogle();
      closeAuthModal();
    } catch (err: any) {
      setLocalError(getFriendlyErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(4, 6, 12, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={closeAuthModal}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '2rem',
          position: 'relative',
          borderRadius: '16px',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(11, 17, 32, 0.98))',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={closeAuthModal}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
          }}
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem' }}>
            <Risk2ReliefLogo
              height={58}
              style={{
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
                background: '#000000',
                padding: '2px',
              }}
            />
          </div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            {isSignUp ? 'Create Risk2Relief Account' : 'Sign In to Risk2Relief'}
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.35rem', marginBottom: 0 }}>
            Firebase Authentication & Identity Verification
          </p>
        </div>

        {/* Mode Toggle Tabs */}
        <div
          style={{
            display: 'flex',
            background: 'rgba(15, 23, 42, 0.7)',
            padding: '0.25rem',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
            marginBottom: '1.25rem',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsSignUp(false);
              setLocalError(null);
            }}
            className={`btn ${!isSignUp ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem', gap: '0.4rem' }}
          >
            <LogIn size={14} /> Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsSignUp(true);
              setLocalError(null);
            }}
            className={`btn ${isSignUp ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem', gap: '0.4rem' }}
          >
            <UserPlus size={14} /> Register
          </button>
        </div>

        {/* Error message */}
        {localError && (
          <div
            style={{
              padding: '0.75rem',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.5rem',
              marginBottom: '1.25rem',
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{localError}</span>
          </div>
        )}

        {/* Email & Password Form */}
        <form onSubmit={handleEmailSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label className="form-label">
              <Mail size={12} /> Email Address
            </label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="beneficiary@risk2relief.org"
              required
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">
              <Lock size={12} /> Password
            </label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', padding: '0.7rem', fontSize: '0.9rem', gap: '0.5rem' }}
          >
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16 }} />
            ) : isSignUp ? (
              <>
                <UserPlus size={16} /> Create Account
              </>
            ) : (
              <>
                <LogIn size={16} /> Sign In with Email
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            margin: '1.25rem 0',
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
          }}
        >
          <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
          <span style={{ padding: '0 0.75rem', textTransform: 'uppercase' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
        </div>

        {/* Google Sign-In Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="btn btn-secondary"
          style={{
            width: '100%',
            padding: '0.65rem',
            fontSize: '0.85rem',
            gap: '0.6rem',
            background: 'rgba(255, 255, 255, 0.05)',
            borderColor: 'var(--border-subtle)',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path
              fill="#EA4335"
              d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z"
            />
            <path
              fill="#4285F4"
              d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
            />
            <path
              fill="#FBBC05"
              d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12.3 0 15.2s.7 5.5 1.9 7.9l3.7-2.9c-.2-.8-.4-1.6-.4-2.4z"
            />
            <path
              fill="#34A853"
              d="M12 23.5c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16.5C3.7 20.2 7.5 23.5 12 23.5z"
            />
          </svg>
          Continue with Google
        </button>

        <div style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          Risk2Relief uses Firebase strictly for identity verification.
        </div>
      </div>
    </div>
  );
};
