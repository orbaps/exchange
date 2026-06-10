import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDashboardStore } from '../state/useDashboardStore';
import { services } from '../services/api';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const Leaderboard: React.FC = () => {
  const { leaderboard, setLeaderboard } = useDashboardStore();

  useEffect(() => {
    services.public.getLeaderboard().then(setLeaderboard).catch(console.error);
  }, []);

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'S+': case 'S': return '#a78bfa'; // Violet
      case 'A+': case 'A': return '#06b6d4'; // Cyan
      case 'B': return '#10b981'; // Green
      case 'C': return '#f59e0b'; // Amber
      default: return '#ef4444'; // Red
    }
  };

  return (
    <div className="animate-fade-in">
      <Header title="Competition Leaderboard" />

      <GlassCard title={leaderboard ? `Leaderboard snapshot: ${leaderboard.snapshot_id}` : 'Leaderboard snapshot'}>
        {leaderboard && leaderboard.entries.length > 0 ? (
          <div style={styles.tableWrapper}>
            <table className="glass-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Contestant</th>
                  <th>Composite Score</th>
                  <th>Rating</th>
                  <th>Avg Correctness</th>
                  <th>Avg Latency</th>
                  <th>Avg TPS</th>
                  <th>Success Rate</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.entries.map((entry) => {
                  const gradeColor = getGradeColor(entry.rating_grade);
                  return (
                    <tr key={entry.contestant_id}>
                      <td style={styles.rankCol}>
                        <span style={styles.rankNum}>{entry.rank}</span>
                        {entry.previous_rank !== null && entry.previous_rank !== undefined && (
                          <span style={styles.rankDiff(entry.previous_rank - entry.rank)}>
                            {entry.previous_rank > entry.rank ? '▲' : entry.previous_rank < entry.rank ? '▼' : '•'}
                          </span>
                        )}
                      </td>
                      <td>
                        <Link to={`/submission/${entry.contestant_id}`} style={styles.teamLink}>
                          {entry.contestant_id}
                        </Link>
                      </td>
                      <td style={styles.scoreCell}>{entry.score.toFixed(2)}</td>
                      <td>
                        <span style={{ ...styles.gradeBadge, color: gradeColor, borderColor: gradeColor }}>
                          {entry.rating_grade}
                        </span>
                      </td>
                      <td>{(entry.average_correctness).toFixed(1)}%</td>
                      <td>{entry.average_latency.toFixed(3)} ms</td>
                      <td>{entry.average_tps.toFixed(1)} eps</td>
                      <td>
                        <span className={`badge ${entry.success_rate >= 90 ? 'badge-success' : 'badge-warning'}`}>
                          {entry.success_rate.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={styles.emptyState}>
            <span>ℹ️</span> No leaderboard entries are currently calculated. Run a tournament stage to populate entries.
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
  rankCol: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  rankNum: {
    fontWeight: '800',
    fontSize: '1.1rem',
  },
  rankDiff: (diff: number) => ({
    fontSize: '0.75rem',
    color: diff > 0 ? 'var(--success)' : diff < 0 ? 'var(--danger)' : 'var(--text-muted)',
  }),
  teamLink: {
    color: '#fff',
    textDecoration: 'none',
    fontWeight: '600',
    transition: 'color 0.2s',
  },
  scoreCell: {
    fontWeight: '700',
    color: 'var(--secondary)',
  },
  gradeBadge: {
    padding: '3px 8px',
    borderRadius: '4px',
    border: '1px solid',
    fontSize: '0.8rem',
    fontWeight: '800' as const,
    display: 'inline-block',
  },
  emptyState: {
    color: 'var(--text-muted)',
    padding: '40px 0',
    textAlign: 'center' as const,
    fontSize: '0.9rem',
  },
};
export default Leaderboard;
