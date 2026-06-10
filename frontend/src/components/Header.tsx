import React from 'react';
import { useDashboardStore } from '../state/useDashboardStore';

interface HeaderProps {
  title: string;
}

export const Header: React.FC<HeaderProps> = ({ title }) => {
  const { isConnected, tournament } = useDashboardStore();

  return (
    <header style={styles.header} className="glass-panel">
      <div>
        <h1 style={styles.title}>{title}</h1>
        {tournament && (
          <span style={styles.activeTour}>
            🏆 Active Event: {tournament.name} ({tournament.status})
          </span>
        )}
      </div>
      
      <div style={styles.stats}>
        <div style={styles.statItem}>
          <span style={styles.statLabel}>Platform:</span>
          <span style={styles.statVal}>IICPC-Sandbox</span>
        </div>
        <div style={styles.statDivider}></div>
        <div style={styles.statItem}>
          <span style={styles.statLabel}>Signal:</span>
          <span className={`badge ${isConnected ? 'badge-success' : 'badge-danger'}`}>
            <span style={styles.signalPulse(isConnected)}></span>
            {isConnected ? 'LIVE FEED' : 'DISCONNECTED'}
          </span>
        </div>
      </div>
    </header>
  );
};

const styles = {
  header: {
    padding: '20px 30px',
    marginBottom: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: '16px',
    background: 'rgba(18, 15, 32, 0.45)',
  },
  title: {
    fontSize: '1.6rem',
    fontWeight: '700',
    letterSpacing: '-0.5px',
  },
  activeTour: {
    fontSize: '0.8rem',
    color: 'var(--primary)',
    fontWeight: '600',
    marginTop: '4px',
    display: 'inline-block',
  },
  stats: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  statItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statLabel: {
    color: 'var(--text-muted)',
    fontSize: '0.85rem',
  },
  statVal: {
    fontWeight: '600',
    fontSize: '0.85rem',
  },
  statDivider: {
    width: '1px',
    height: '24px',
    background: 'var(--border-glass)',
  },
  signalPulse: (isConnected: boolean) => ({
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: isConnected ? 'var(--success)' : 'var(--danger)',
    display: 'inline-block',
    animation: isConnected ? 'pulse-glow 1.5s infinite' : 'none',
  }),
};
