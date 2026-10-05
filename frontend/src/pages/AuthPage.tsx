import React, { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { api } from '../services/api';
import { AuthUser } from '../types';

interface AuthPageProps { onAuthenticated: (user: AuthUser) => void; }

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthenticated }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('');
    if (mode === 'register') {
      if (!fullName.trim()) { setError('Please enter your full name.'); return; }
      if (password.length < 8) { setError('Choose a password with at least 8 characters.'); return; }
      if (password !== confirmPassword) { setError('Passwords do not match.'); return; }
    }
    setBusy(true);
    try {
      const user = mode === 'login' ? await api.login({ email, password }) : await api.register({ full_name: fullName, email, password, confirm_password: confirmPassword });
      onAuthenticated(user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'We could not complete your request. Please try again.');
    } finally { setBusy(false); }
  };

  return <main className="auth-screen"><section className="auth-card panel">
    <div className="auth-brand"><span className="brand-mark"><ShieldCheck size={22} /></span><span><strong>SwiftIntel</strong><small>Investigation workspace</small></span></div>
    <p className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}</p>
    <h1>{mode === 'login' ? 'Log in to your account' : 'Create your account'}</h1>
    <p className="auth-intro">{mode === 'login' ? 'Sign in to continue to your investigation workspace.' : 'Create an account to manage investigations and evidence.'}</p>
    {error && <div className="notice notice-error auth-error" role="alert">{error}</div>}
    <form onSubmit={submit} className="auth-form">
      {mode === 'register' && <label>Full name<input autoComplete="name" value={fullName} onChange={e => setFullName(e.target.value)} required maxLength={160} /></label>}
      <label>Email<input type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required maxLength={254} /></label>
      <label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={e => setPassword(e.target.value)} required minLength={mode === 'login' ? 1 : 8} maxLength={256} />{mode === 'register' && <small>Use at least 8 characters.</small>}</label>
      {mode === 'register' && <label>Confirm password<input type="password" autoComplete="new-password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required minLength={8} maxLength={256} /></label>}
      <button type="submit" className="button-primary" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Login' : 'Create Account'}</button>
    </form>
    <p className="auth-switch">{mode === 'login' ? "Don't have an account?" : 'Already have an account?'} <button type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'Register' : 'Login'}</button></p>
  </section></main>;
};
