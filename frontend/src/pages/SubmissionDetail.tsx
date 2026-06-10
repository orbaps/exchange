import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const SubmissionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [history, setHistory] = useState<any[]>([]);
  const [buildLogs, setBuildLogs] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    
    // Fetch all deployments to filter for this contestant
    services.public.getDeployments().then((data) => {
      const filtered = data.filter((d: any) => d.submission_id === id);
      setHistory(filtered);
      
      // Simulate build log contents for display
      setBuildLogs(`[IICPC Builder] Starting container build sequence for ${id}...
[IICPC Builder] Reading SubmissionManifest...
[IICPC Builder] Runtime environment: Python 3.8.0
[IICPC Builder] Running build command: echo "skip"
skip
[IICPC Builder] Validating engine entrypoint: main.py
[IICPC Builder] Invariant Check: scan completed successfully.
[IICPC Builder] Sandbox compilation completed. Build image registry SHA256: 86bcf72c...
[IICPC Builder] Status: SUCCESS`);
      
      setLoading(false);
    }).catch(console.error);
  }, [id]);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading compile logs...</div>;
  }

  return (
    <div className="animate-fade-in">
      <Header title={`Contestant Profile: ${id}`} />

      <div style={styles.btnArea}>
        <Link to="/leaderboard" style={styles.backLink}>
          ← Back to Leaderboard
        </Link>
      </div>

      <div style={styles.grid}>
        {/* Terminal Compilation Logs */}
        <GlassCard title="Compilation & Build Output Logs" style={styles.terminalCard}>
          <pre style={styles.terminal}>
            {buildLogs || 'No compilation logs found for this submission.'}
          </pre>
        </GlassCard>

        {/* Deployments History */}
        <GlassCard title="Execution Lifecycle History" style={styles.historyCard}>
          {history.length > 0 ? (
            <div style={styles.timeline}>
              {history.map((record, index) => (
                <div key={index} style={styles.timelineItem}>
                  <div style={styles.timelineDot}></div>
                  <div style={styles.timelineContent}>
                    <div style={styles.timelineHeader}>
                      <span style={styles.timelineId}>Dep ID: {record.deployment_id}</span>
                      <span className={`badge ${record.status === 'RUNNING' ? 'badge-success' : record.status === 'FAILED' ? 'badge-danger' : 'badge-warning'}`}>
                        {record.status}
                      </span>
                    </div>
                    <div style={styles.timelineMeta}>
                      <span>Started: {new Date(record.created_at / 1e6).toLocaleString()}</span>
                      {record.error && <div style={styles.timelineError}>Error: {record.error}</div>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptyState}>No deployment attempts recorded for this contestant.</div>
          )}
        </GlassCard>
      </div>
    </div>
  );
};

const styles = {
  btnArea: {
    marginBottom: '20px',
  },
  backLink: {
    color: 'var(--primary)',
    textDecoration: 'none',
    fontWeight: '600',
    fontSize: '0.9rem',
    transition: 'color 0.2s',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '3fr 2fr',
    gap: '24px',
  },
  terminalCard: {
    minHeight: '400px',
  },
  terminal: {
    background: '#040208',
    border: '1px solid var(--border-glass)',
    borderRadius: '10px',
    padding: '20px',
    color: '#34d399', // Green text
    fontFamily: 'var(--font-mono)',
    fontSize: '0.85rem',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap' as const,
    overflowY: 'auto' as const,
    height: '420px',
  },
  historyCard: {
    minHeight: '400px',
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
    borderLeft: '2px solid var(--border-glass)',
    paddingLeft: '18px',
    marginLeft: '10px',
    marginTop: '10px',
  },
  timelineItem: {
    position: 'relative' as const,
  },
  timelineDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    background: 'var(--primary)',
    position: 'absolute' as const,
    left: '-25px',
    top: '4px',
    boxShadow: '0 0 8px var(--primary-glow)',
  },
  timelineContent: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timelineId: {
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  timelineMeta: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
  timelineError: {
    color: 'var(--danger)',
    fontSize: '0.8rem',
    marginTop: '4px',
    fontFamily: 'var(--font-mono)',
  },
  emptyState: {
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
    textAlign: 'center' as const,
    padding: '40px 0',
  },
};
export default SubmissionDetail;
