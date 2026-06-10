import React, { useEffect } from 'react';
import { useDashboardStore } from '../state/useDashboardStore';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const Deployments: React.FC = () => {
  const { deployments, setDeployments } = useDashboardStore();

  useEffect(() => {
    services.public.getDeployments().then(setDeployments).catch(console.error);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'badge-success';
      case 'BUILDING': case 'STARTING':
        return 'badge-primary';
      case 'FAILED':
        return 'badge-danger';
      default:
        return 'badge-warning';
    }
  };

  return (
    <div className="animate-fade-in">
      <Header title="Container Registry & Deployments" />

      <GlassCard title="Contestant Container Deployment Audit Trail">
        {deployments.length > 0 ? (
          <div style={styles.tableWrapper}>
            <table className="glass-table">
              <thead>
                <tr>
                  <th>Deployment ID</th>
                  <th>Submission ID</th>
                  <th>Build ID</th>
                  <th>Container ID</th>
                  <th>State</th>
                  <th>Deployed At</th>
                  <th>End Time</th>
                  <th>Errors</th>
                </tr>
              </thead>
              <tbody>
                {deployments.map((d) => (
                  <tr key={d.deployment_id}>
                    <td style={styles.mono}>{d.deployment_id}</td>
                    <td><strong>{d.submission_id}</strong></td>
                    <td style={styles.mono}>{d.build_id}</td>
                    <td style={styles.mono}>{d.container_id.slice(0, 12)}...</td>
                    <td>
                      <span className={`badge ${getStatusBadge(d.status)}`}>
                        {d.status}
                      </span>
                    </td>
                    <td>{new Date(d.created_at / 1e6).toLocaleString()}</td>
                    <td>{d.end_time ? new Date(d.end_time / 1e6).toLocaleString() : 'Active'}</td>
                    <td style={styles.errorText}>{d.error || 'None'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={styles.emptyState}>
            <span>ℹ️</span> No container logs are currently stored. Deploy a contestant to see logs.
          </div>
        )}
      </GlassCard>
    </div>
  );
};

const styles = {
  tableWrapper: {
    overflowX: 'auto' as const,
  },
  mono: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
  errorText: {
    color: 'var(--danger)',
    fontSize: '0.85rem',
    maxWidth: '200px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  emptyState: {
    color: 'var(--text-muted)',
    padding: '40px 0',
    textAlign: 'center' as const,
    fontSize: '0.9rem',
  },
};
export default Deployments;
