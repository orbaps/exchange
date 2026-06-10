import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { services } from '../services/api';
import { useAuthStore } from '../state/useAuthStore';
import { wsClient } from '../services/websocket';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await services.auth.login(username, password);
      // Save credentials in store & localStorage
      login(data.access_token, data.role, username);
      // Initialize WebSocket connection
      wsClient.connect(data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card} className="glass-panel animate-fade-in">
        <div style={styles.logoHeader}>
          <div style={styles.logoIcon}>IICPC</div>
          <h2 style={styles.logoText}>OPERATOR CONSOLE</h2>
        </div>
        <p style={styles.subtitle}>Enter credentials to access competition logs and metrics</p>
        
        {error && <div style={styles.errorBanner} className="badge-danger">{error}</div>}
        
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Username</label>
            <input
              type="text"
              className="glass-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin"
              required
            />
          </div>
          <div style={styles.formGroup}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              className="glass-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" className="glass-button" disabled={loading} style={styles.submitBtn}>
            {loading ? 'Authenticating...' : 'Connect to Feed'}
          </button>
        </form>
        
        <div style={styles.tips}>
          <p style={styles.tipText}>💡 Hint: admin / adminpassword (Admin), public / publicpassword (Viewer)</p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    width: '100vw',
    backgroundColor: '#05030a',
  },
  card: {
    width: '420px',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  logoHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '10px',
  },
  logoIcon: {
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    color: '#fff',
    padding: '4px 10px',
    borderRadius: '6px',
    fontWeight: '800',
    fontSize: '0.9rem',
  },
  logoText: {
    fontSize: '1.25rem',
    fontWeight: '700',
    letterSpacing: '1px',
  },
  subtitle: {
    color: 'var(--text-muted)',
    fontSize: '0.85rem',
    marginBottom: '24px',
  },
  errorBanner: {
    padding: '12px',
    borderRadius: '8px',
    fontSize: '0.85rem',
    marginBottom: '20px',
    textAlign: 'center' as const,
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '18px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  label: {
    fontSize: '0.8rem',
    fontWeight: '600',
    color: 'var(--text-muted)',
  },
  submitBtn: {
    marginTop: '10px',
    padding: '12px',
  },
  tips: {
    marginTop: '24px',
    borderTop: '1px solid var(--border-glass)',
    paddingTop: '16px',
    textAlign: 'center' as const,
  },
  tipText: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  },
};
