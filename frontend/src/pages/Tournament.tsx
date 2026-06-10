import React, { useEffect } from 'react';
import { useDashboardStore } from '../state/useDashboardStore';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const Tournament: React.FC = () => {
  const { tournament, setTournament } = useDashboardStore();

  useEffect(() => {
    services.public.getTournament().then(setTournament).catch(console.error);
  }, []);

  return (
    <div className="animate-fade-in">
      <Header title="Tournament Bracket & Stages" />

      {tournament ? (
        <div style={styles.container}>
          <GlassCard title={`Event: ${tournament.name}`} style={styles.fullWidth}>
            <p style={styles.desc}>{tournament.description}</p>
            <div style={styles.metaRow}>
              <span>Status: <span className="badge badge-primary">{tournament.status}</span></span>
              <span>Created: {new Date(tournament.created_at / 1e6).toLocaleString()}</span>
            </div>
          </GlassCard>

          {/* Bracket / Stage Flow */}
          <div style={styles.stageFlow}>
            {tournament.stages.map((stage, idx) => (
              <div key={stage.stage_id} style={styles.stageNode}>
                <div style={styles.stageConnector(idx > 0)}></div>
                <GlassCard style={styles.stageCard}>
                  <div style={styles.stageHeader}>
                    <div style={styles.stageIdx}>STAGE 0{idx + 1}</div>
                    <div className="badge badge-success">{stage.stage_type}</div>
                  </div>
                  <h4 style={styles.stageTitle}>{stage.stage_id}</h4>
                  <div style={styles.stageDetails}>
                    <div style={styles.detailItem}>
                      <span style={styles.label}>Campaign:</span>
                      <span style={styles.val}>{stage.campaign_id}</span>
                    </div>
                  </div>
                </GlassCard>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <GlassCard>
          <div style={styles.emptyState}>
            <span>ℹ&nbsp;</span> No active tournament is currently loaded. Go to **Mission Control** to launch a campaign tournament.
          </div>
        </GlassCard>
      )}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '24px',
  },
  fullWidth: {
    width: '100%',
  },
  desc: {
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
    marginBottom: '16px',
  },
  metaRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
  },
  stageFlow: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '40px',
    alignItems: 'center',
    marginTop: '20px',
    position: 'relative' as const,
  },
  stageNode: {
    display: 'flex',
    alignItems: 'center',
    position: 'relative' as const,
  },
  stageConnector: (active: boolean) => ({
    width: active ? '40px' : '0px',
    height: '2px',
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
    position: 'absolute' as const,
    left: '-40px',
    display: active ? 'block' : 'none',
  }),
  stageCard: {
    width: '320px',
    marginBottom: '0px',
  },
  stageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  stageIdx: {
    fontSize: '0.75rem',
    color: 'var(--primary)',
    fontWeight: '800',
    letterSpacing: '1px',
  },
  stageTitle: {
    fontSize: '1.2rem',
    fontWeight: '700',
    marginBottom: '16px',
  },
  stageDetails: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
    borderTop: '1px solid var(--border-glass)',
    paddingTop: '12px',
  },
  detailItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.85rem',
  },
  label: {
    color: 'var(--text-muted)',
  },
  val: {
    fontWeight: '600',
  },
  emptyState: {
    color: 'var(--text-muted)',
    padding: '40px 0',
    textAlign: 'center' as const,
    fontSize: '0.9rem',
  },
};
export default Tournament;
