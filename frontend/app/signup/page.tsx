'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignUpPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('viewer');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // 1. Call Go Auth Service (/api/auth/signup)
      let res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email,
          password,
          roles: [role]
        }),
      });

      // Fallback direct port 8081 if proxy is pending
      if (!res.ok && res.status !== 409) {
        try {
          const direct = await fetch('http://localhost:8081/api/v1/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, roles: [role] }),
          });
          if (direct.ok) res = direct;
        } catch {
          // Fallback to FastAPI register
          const pyRes = await fetch('http://localhost:8000/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email, roles: [role] }),
          });
          if (pyRes.ok) res = pyRes;
        }
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.detail || 'Sign up failed.');
      }

      // If token returned, auto-authenticate
      if (data.access_token) {
        localStorage.setItem('anime_auth_token', data.access_token);
        localStorage.setItem('anime_auth_user', JSON.stringify(data.user || { username, roles: [role] }));
        window.dispatchEvent(new Event('auth-change'));
      }

      setSuccess(`Account '${username}' created in PostgreSQL/MongoDB! Redirecting...`);
      setTimeout(() => router.push('/'), 1200);

    } catch (err: any) {
      setError(err.message || 'Error connecting to authentication service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '460px', margin: '50px auto', padding: '0 20px' }}>
      <div className="glass-panel" style={{ padding: '36px 32px' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex', padding: '10px 14px', borderRadius: '12px',
            background: 'rgba(236, 72, 153, 0.15)', color: '#ec4899', marginBottom: '12px',
            fontSize: '1.4rem'
          }}>
            🚀
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginBottom: '6px' }}>
            Create Account
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Join the Polyglot Anime Intelligence Network
          </p>
        </div>

        {/* Error / Success Banners */}
        {error && (
          <div style={{
            padding: '12px', borderRadius: '8px', marginBottom: '18px',
            background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5', fontSize: '0.85rem'
          }}>
            ⚠️ {error}
          </div>
        )}
        {success && (
          <div style={{
            padding: '12px', borderRadius: '8px', marginBottom: '18px',
            background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#6ee7b7', fontSize: '0.85rem'
          }}>
            ✓ {success}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSignUp} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. shinji_ikari"
              className="input-glass"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. pilot@nerv.jp"
              className="input-glass"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="input-glass"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
              Platform Role (RBAC)
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="input-glass"
              style={{ cursor: 'pointer' }}
            >
              <option value="viewer" style={{ background: '#0f172a', color: '#fff' }}>Anime Enthusiast (Viewer)</option>
              <option value="researcher" style={{ background: '#0f172a', color: '#fff' }}>ML Researcher (LangGraph Agent Access)</option>
              <option value="admin" style={{ background: '#0f172a', color: '#fff' }}>Platform Admin (Full Superuser Access)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: '8px', fontSize: '1rem' }}
          >
            {loading ? 'Creating Account...' : 'Sign Up to Platform'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem', color: '#94a3b8' }}>
          Already have an account?{' '}
          <Link href="/signin" style={{ color: '#ec4899', textDecoration: 'none', fontWeight: 600 }}>
            Sign In here
          </Link>
        </div>

      </div>
    </div>
  );
}
