'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignInPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // 1. Primary: Call Go Auth Microservice on Port 8081 (proxied via /api/auth/signin)
      let res = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      // 2. Resilient Fallback: If Go server not proxying, call direct or FastAPI auth
      if (!res.ok && res.status !== 401) {
        try {
          const directGo = await fetch('http://localhost:8081/api/v1/auth/signin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          });
          if (directGo.ok) res = directGo;
        } catch {
          // If neither reached, try FastAPI /api/v1/auth/token
          const form = new URLSearchParams();
          form.append('username', username);
          form.append('password', password);
          const pyRes = await fetch('http://localhost:8000/api/v1/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form.toString(),
          });
          if (pyRes.ok) res = pyRes;
        }
      }

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || data.detail || 'Authentication failed. Please verify credentials.');
      }

      // Store JWT token & claims
      localStorage.setItem('anime_auth_token', data.access_token);
      localStorage.setItem('anime_auth_user', JSON.stringify(data.user || { username, roles: data.roles || ['viewer'] }));

      window.dispatchEvent(new Event('auth-change'));
      setSuccess(`Signed in successfully as ${username}! Redirecting...`);
      setTimeout(() => router.push('/'), 1200);

    } catch (err: any) {
      setError(err.message || 'Connection error. Ensure microservices are running.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div style={{ maxWidth: '440px', margin: '60px auto', padding: '0 20px' }}>
      <div className="glass-panel" style={{ padding: '36px 32px' }}>
        
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            display: 'inline-flex', padding: '10px 14px', borderRadius: '12px',
            background: 'rgba(99, 102, 241, 0.15)', color: '#6366f1', marginBottom: '12px',
            fontSize: '1.4rem'
          }}>
            🔐
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginBottom: '6px' }}>
            Welcome Back
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Sign in via Go Auth Microservice & PostgreSQL / MongoDB
          </p>
        </div>

        {/* Quick Demo Fillers */}
        <div style={{ marginBottom: '20px', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px' }}>
            ⚡ Instant Demo Logins
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              type="button"
              onClick={() => fillDemo('admin', 'admin123')}
              className="btn-secondary"
              style={{ flex: 1, padding: '6px 8px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              👑 Admin
            </button>
            <button
              type="button"
              onClick={() => fillDemo('researcher', 'research123')}
              className="btn-secondary"
              style={{ flex: 1, padding: '6px 8px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              🔬 Researcher
            </button>
            <button
              type="button"
              onClick={() => fillDemo('user', 'user123')}
              className="btn-secondary"
              style={{ flex: 1, padding: '6px 8px', fontSize: '0.75rem', justifyContent: 'center' }}
            >
              👤 Viewer
            </button>
          </div>
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
        <form onSubmit={handleSignIn} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600, marginBottom: '6px' }}>
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin or kenshiro"
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
              placeholder="••••••••••••"
              className="input-glass"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: '6px', fontSize: '1rem' }}
          >
            {loading ? 'Authenticating...' : 'Sign In with JWT'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem', color: '#94a3b8' }}>
          Don't have an account?{' '}
          <Link href="/signup" style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 600 }}>
            Create one here
          </Link>
        </div>

      </div>
    </div>
  );
}
