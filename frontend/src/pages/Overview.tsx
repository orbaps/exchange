import React, { useEffect } from 'react';
import { useDashboardStore } from '../state/useDashboardStore';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const Overview: React.FC = () => {
  const { analytics, health, tournament, setAnalytics, setTournament } = useDashboardStore();

  useEffect(() => {
    // Initial fetch of dashboard stats
    services.public.getAnalytics().then(setAnalytics).catch(console.error);
    services.public.getDeployments().then(() => {
      // Re-map to health list
      services.public.getTournament().then(setTournament).catch(console.error);
    }).catch(console.error);
  }, []);

  const statsList = [
    { label: 'Scenarios Run', value: analytics?.total_scenarios_run ?? 0, color: 'var(--primary)' },
    { label: 'Success Rate', value: `${(analytics?.overall_success_rate ?? 0).toFixed(1)}%`, color: 'var(--success)' },
    { label: 'Average TPS', value: (analytics?.avg_tps ?? 0).toFixed(1), color: 'var(--secondary)' },
    { label: 'Avg Latency', value: `${(analytics?.avg_latency_ms ?? 0).toFixed(3)} ms`, color: 'var(--warning)' },
  ];

  return (
    <div className="animate-fade-in">
      <Header title="Operator Overview" />
      
      {/* Real-time stats grid */}
      <div style={styles.statsGrid}>
        {statsList.map((stat, idx) => (
          <GlassCard key={idx} style={styles.statCard}>
            <div style={styles.statLabel}>{stat.label}</div>
            <div style={{ ...styles.statVal, color: stat.color }}>{stat.value}</div>
          </GlassCard>
        ))}
      </div>

      <div style={styles.mainGrid}>
        {/* Active Tournament Status */}
        <GlassCard title="Active Tournament Summary" style={styles.col}>
          {tournament ? (
            <div style={styles.tourInfo}>
              <div style={styles.tourRow}>
                <span style={styles.label}>ID:</span>
                <span style={styles.val}>{tournament.tournament_id}</span>
              </div>
              <div style={styles.tourRow}>
                <span style={styles.label}>Name:</span>
                <span style={styles.val}>{tournament.name}</span>
              </div>
              <div style={styles.tourRow}>
                <span style={styles.label}>Status:</span>
                <span className={`badge ${tournament.status === 'COMPLETED' ? 'badge-success' : 'badge-primary'}`}>
                  {tournament.status}
                </span>
              </div>
              <div style={styles.tourRow}>
                <span style={styles.label}>Stages Configured:</span>
                <span style={styles.val}>{tournament.stages.length}</span>
              </div>
            </div>
          ) : (
            <div style={styles.emptyState}>
              <span>ℹ️</span> No active tournament is currently running. Use the Mission Control panel to start one.
            </div>
          )}
        </GlassCard>

        {/* Deployment Health Summary */}
        <GlassCard title="Container Nodes Status" style={styles.col}>
          {health.length > 0 ? (
            <div style={styles.healthList}>
              {health.map((h, idx) => (
                <div key={idx} style={styles.healthRow} className="glass-panel">
                  <div>
                    <div style={styles.subId}>{h.submission_id}</div>
                    <div style={styles.contId}>{h.container_id.slice(0, 12)}...</div>
                  </div>
                  <div style={styles.healthStats}>
                    <div style={styles.uptime}>Uptime: {((h.uptime_ns || 0) / 1e9).toFixed(1)}s</div>
                    <span className={`badge ${h.status === 'RUNNING' ? 'badge-success' : 'badge-danger'}`}>
                      {h.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptyState}>
              No container instances are currently deployed on the hosting layer.
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
};

const styles = {
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '20px',
    marginBottom: '24px',
  },
  statCard: {
    padding: '20px 24px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  statLabel: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    fontWeight: '500',
  },
  statVal: {
    fontSize: '2rem',
    fontWeight: '800',
    letterSpacing: '-1px',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
  },
  col: {
    minHeight: '300px',
  },
  tourInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '14px',
    marginTop: '10px',
  },
  tourRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: '10px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
  },
  label: {
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
  },
  val: {
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  emptyState: {
    color: 'var(--text-muted)',
    fontSize: '0.85rem',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '20px',
  },
  healthList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px',
  },
  healthRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 18px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '12px',
  },
  subId: {
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  contId: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-mono)',
  },
  healthStats: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
  },
  uptime: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
};
