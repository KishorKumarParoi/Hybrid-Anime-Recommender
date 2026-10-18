import './globals.css';
import Navbar from '@/components/Navbar';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Anime.AI | Enterprise Hybrid Recommender & Polyglot Platform',
  description: 'Production-ready recommendation engine powered by Go Auth, Express Interactions, Rust Scoring Engine, and Python LangGraph LLMOps.',
  keywords: ['Anime Recommender', 'Next.js', 'Go', 'Rust', 'Express', 'FastAPI', 'PyTorch', 'Kafka', 'LangGraph'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main>{children}</main>
        <footer style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '40px 24px',
          marginTop: '80px',
          background: 'rgba(8, 11, 17, 0.95)',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '0.85rem'
        }}>
          <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="badge badge-nextjs">Next.js Latest (v16 Turbopack)</span>
              <span className="badge badge-go">Go 1.27</span>
              <span className="badge badge-express">Express (Node 22)</span>
              <span className="badge badge-rust">Rust 1.99</span>
              <span className="badge badge-python">Python 3.12</span>
            </div>
            <p>© 2026 Hybrid Anime Intelligence Platform. Polyglot Microservices with PostgreSQL, MongoDB, Kafka & Tri-Cloud Architecture.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
