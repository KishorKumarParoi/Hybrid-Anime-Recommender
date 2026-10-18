'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Navbar() {
  const [user, setUser] = useState<{ username: string; roles: string[] } | null>(null);

  useEffect(() => {
    const checkAuth = () => {
      const storedUser = localStorage.getItem('anime_auth_user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    };

    checkAuth();
    window.addEventListener('storage', checkAuth);
    window.addEventListener('auth-change', checkAuth);
    return () => {
      window.removeEventListener('storage', checkAuth);
      window.removeEventListener('auth-change', checkAuth);
    };
  }, []);

  const handleSignOut = () => {
    localStorage.removeItem('anime_auth_token');
    localStorage.removeItem('anime_auth_user');
    setUser(null);
    window.dispatchEvent(new Event('auth-change'));
  };

  return (
    <header className="glass-nav" style={{ position: 'sticky', top: 0, zIndex: 100, width: '100%' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        
        {/* Brand */}
        <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px', height: '38px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.2rem', fontWeight: 'bold', color: '#fff',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            ⚡
          </div>
          <div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
              ANIME<span style={{ color: '#6366f1' }}>.AI</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Polyglot Microservices
            </div>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
          <Link href="/#recommendations" style={{ color: '#cbd5e1', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500, transition: 'color 0.2s' }}>
            Hybrid Recommender
          </Link>
          <Link href="/#dossiers" style={{ color: '#cbd5e1', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500, transition: 'color 0.2s' }}>
            Agent Research
          </Link>
          <Link href="/#community" style={{ color: '#cbd5e1', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500, transition: 'color 0.2s' }}>
            Live Stream
          </Link>
          <Link href="/#microservices" style={{ color: '#cbd5e1', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500, transition: 'color 0.2s' }}>
            Architecture
          </Link>
        </nav>

        {/* Auth State & Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>
                  {user.username}
                </span>
                <span style={{ fontSize: '0.7rem', color: '#6366f1', textTransform: 'uppercase', fontWeight: 700 }}>
                  {user.roles?.[0] || 'viewer'}
                </span>
              </div>
              <button
                onClick={handleSignOut}
                className="btn-secondary"
                style={{ padding: '6px 14px', fontSize: '0.85rem' }}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Link href="/signin" className="btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
                Sign In
              </Link>
              <Link href="/signup" className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.85rem' }}>
                Sign Up
              </Link>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
