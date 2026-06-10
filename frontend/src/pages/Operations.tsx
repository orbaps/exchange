import React, { useState } from 'react';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const Operations: React.FC = () => {
  const [contestantCount, setContestantCount] = useState(4);
  const [tJournal, setTJournal] = useState('');
  const [hJournal, setHJournal] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleStartTournament = async () => {
    setLoading(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const data = await services.admin.startTournament(contestantCount);
      setStatusMsg(`Tournament launched successfully! ID: ${data.tournament_id}`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to start tournament.');
    } finally {
      setLoading(false);
    }
  };

  const handleStopTournament = async () => {
    setLoading(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const data = await services.admin.stopTournament();
      setStatusMsg(data.message);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to stop tournament.');
    } finally {
      setLoading(false);
    }
  };

  const handleRebuild = async () => {
    setLoading(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const data = await services.admin.rebuildDatabase(tJournal, hJournal);
      setStatusMsg(data.message);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to rebuild state from journals.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <Header title="Operator Mission Control" />

      {statusMsg && <div style={styles.successBanner} className="badge-success">{statusMsg}</div>}
      {errorMsg && <div style={styles.errorBanner} className="badge-danger">{errorMsg}</div>}

      <div style={styles.grid}>
        {/* Run Controls */}
        <GlassCard title="Execution Control Plane">
          <div style={styles.section}>
            <p style={styles.desc}>Start a background tournament campaign running sequentially on sandbox container nodes.</p>
            <div style={styles.formGroup}>
              <label style={styles.label}>Contestant Team Count</label>
              <input
                type="number"
                min={2}
                max={20}
                className="glass-input"
                value={contestantCount}
                onChange={(e) => setContestantCount(parseInt(e.target.value))}
              />
            </div>
            <div style={styles.btnRow}>
              <button className="glass-button" onClick={handleStartTournament} disabled={loading}>
                Start Campaign
              </button>
              <button className="glass-button-secondary" onClick={handleStopTournament} disabled={loading} style={{ color: 'var(--danger)' }}>
                Terminate Runner
              </button>
            </div>
          </div>
        </GlassCard>

        {/* Database Rebuilds */}
        <GlassCard title="Journal Store Aggregator">
          <div style={styles.section}>
            <p style={styles.desc}>Rebuild the cache database dynamically from past file-backed transaction logs.</p>
            <div style={styles.formGroup}>
              <label style={styles.label}>Tournament Journal File Path (Optional)</label>
              <input
                type="text"
                className="glass-input"
                value={tJournal}
                onChange={(e) => setTJournal(e.target.value)}
                placeholder="e.g. dashboard_run_artifacts/t1_journal.jsonl"
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Hosting Journal File Path (Optional)</label>
              <input
                type="text"
                className="glass-input"
                value={hJournal}
                onChange={(e) => setHJournal(e.target.value)}
                placeholder="e.g. dashboard_run_artifacts/hosting_journal.jsonl"
              />
            </div>
            <button className="glass-button" onClick={handleRebuild} disabled={loading} style={styles.fullWidthBtn}>
              Rebuild Dashboard Cache
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

const styles = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
    gap: '24px',
  },
  section: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  },
  desc: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    lineHeight: '1.4',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
  },
  label: {
    fontSize: '0.8rem',
    fontWeight: '600',
    color: 'var(--text-muted)',
  },
  btnRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '10px',
  },
  fullWidthBtn: {
    marginTop: '10px',
    width: '100%',
  },
  successBanner: {
    padding: '12px 20px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    marginBottom: '20px',
  },
  errorBanner: {
    padding: '12px 20px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    marginBottom: '20px',
  },
};
export default Operations;
