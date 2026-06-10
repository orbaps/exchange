import React, { useState, useEffect, useRef } from 'react';
import { services } from '../services/api';
import { useReplayStore } from '../state/useReplayStore';
import { Header } from '../components/Header';
import { GlassCard } from '../components/GlassCard';

export const ReplayViewer: React.FC = () => {
  const [tourId, setTourId] = useState('t1');
  const [activeTab, setActiveTab] = useState<'tournament' | 'analytics' | 'hosting'>('tournament');
  const [error, setError] = useState<string | null>(null);
  
  const {
    timelineEvents,
    currentIndex,
    isPlaying,
    playbackSpeed,
    reconstructedState,
    setTimelineEvents,
    setCurrentIndex,
    setIsPlaying,
    setPlaybackSpeed,
    setReconstructedState,
    resetReplay
  } = useReplayStore();

  const playTimerRef = useRef<number | null>(null);

  // Load timeline events list
  const handleLoadTimeline = async () => {
    setError(null);
    resetReplay();
    try {
      const data = await services.public.getReplayTimeline(tourId);
      if (data.events && data.events.length > 0) {
        setTimelineEvents(data.events);
        // Load first snapshot
        await handleFetchSnapshot(0);
      } else {
        setError('Timeline exists but has no events recorded.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Tournament journal not found.');
    }
  };

  // Fetch reconstructed state snapshot for a specific index
  const handleFetchSnapshot = async (index: number) => {
    try {
      const state = await services.public.getReplaySnapshot(tourId, index);
      setReconstructedState(state);
      setCurrentIndex(index);
    } catch (err) {
      console.error('Failed to fetch snapshot state:', err);
    }
  };

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = window.setInterval(async () => {
        if (currentIndex < timelineEvents.length - 1) {
          const nextIdx = currentIndex + 1;
          await handleFetchSnapshot(nextIdx);
        } else {
          setIsPlaying(false);
        }
      }, playbackSpeed);
    } else {
      if (playTimerRef.current) {
        clearInterval(playTimerRef.current);
        playTimerRef.current = null;
      }
    }

    return () => {
      if (playTimerRef.current) {
        clearInterval(playTimerRef.current);
      }
    };
  }, [isPlaying, currentIndex, timelineEvents, playbackSpeed]);

  const handleStepForward = async () => {
    setIsPlaying(false);
    if (currentIndex < timelineEvents.length - 1) {
      await handleFetchSnapshot(currentIndex + 1);
    }
  };

  const handleStepBackward = async () => {
    setIsPlaying(false);
    if (currentIndex > 0) {
      await handleFetchSnapshot(currentIndex - 1);
    }
  };

  const handleSeek = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setIsPlaying(false);
    const index = parseInt(e.target.value);
    await handleFetchSnapshot(index);
  };

  return (
    <div className="animate-fade-in">
      <Header title="Historical Replay Viewer" />

      {error && <div style={styles.errorBanner} className="badge-danger">{error}</div>}

      <div style={styles.topControl} className="glass-panel">
        <div style={styles.inputGroup}>
          <label style={styles.label}>Tournament ID</label>
          <div style={styles.inputRow}>
            <input
              type="text"
              className="glass-input"
              value={tourId}
              onChange={(e) => setTourId(e.target.value)}
              placeholder="e.g. t1"
            />
            <button className="glass-button" onClick={handleLoadTimeline}>
              Load Timeline
            </button>
          </div>
        </div>

        {timelineEvents.length > 0 && (
          <div style={styles.playbackControls}>
            <div style={styles.btnGroup}>
              <button className="glass-button-secondary" onClick={handleStepBackward} disabled={currentIndex <= 0}>
                ⏮ Step Back
              </button>
              <button className="glass-button" onClick={() => setIsPlaying(!isPlaying)}>
                {isPlaying ? '⏸ Pause' : '▶ Play'}
              </button>
              <button className="glass-button-secondary" onClick={handleStepForward} disabled={currentIndex >= timelineEvents.length - 1}>
                Step Forward ⏭
              </button>
            </div>

            <div style={styles.speedGroup}>
              <span style={styles.speedLabel}>Speed:</span>
              <select
                className="glass-input"
                style={styles.select}
                value={playbackSpeed}
                onChange={(e) => setPlaybackSpeed(parseInt(e.target.value))}
              >
                <option value={2000}>0.5x</option>
                <option value={1000}>1.0x</option>
                <option value={500}>2.0x</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {timelineEvents.length > 0 && (
        <div style={styles.timelineScrubber} className="glass-panel">
          <div style={styles.scrubberInfo}>
            <span>Event Index: <strong>{currentIndex + 1} / {timelineEvents.length}</strong></span>
            <span>Type: <span className="badge badge-primary">{timelineEvents[currentIndex]?.event_type}</span></span>
          </div>
          <input
            type="range"
            min={0}
            max={timelineEvents.length - 1}
            value={currentIndex}
            onChange={handleSeek}
            style={styles.slider}
          />
        </div>
      )}

      {reconstructedState && (
        <div style={styles.detailsContainer}>
          <div style={styles.tabHeader}>
            <button
              style={activeTab === 'tournament' ? { ...styles.tab, ...styles.tabActive } : styles.tab}
              onClick={() => setActiveTab('tournament')}
            >
              Bracket & Stages
            </button>
            <button
              style={activeTab === 'analytics' ? { ...styles.tab, ...styles.tabActive } : styles.tab}
              onClick={() => setActiveTab('analytics')}
            >
              Reconstructed Leaderboard
            </button>
            <button
              style={activeTab === 'hosting' ? { ...styles.tab, ...styles.tabActive } : styles.tab}
              onClick={() => setActiveTab('hosting')}
            >
              Container Uptime log
            </button>
          </div>

          <div style={styles.tabContent}>
            {activeTab === 'tournament' && (
              <GlassCard title="Tournament State snapshot">
                <div style={styles.metaGrid}>
                  <div style={styles.metaItem}>
                    <span style={styles.metaLabel}>Tournament Status:</span>
                    <span className="badge badge-primary">{reconstructedState.status}</span>
                  </div>
                  <div style={styles.metaItem}>
                    <span style={styles.metaLabel}>Active Pool:</span>
                    <span style={styles.metaVal}>{reconstructedState.active_pool.join(', ') || 'None'}</span>
                  </div>
                  <div style={styles.metaItem}>
                    <span style={styles.metaLabel}>Eliminated Teams:</span>
                    <span style={styles.metaVal}>{reconstructedState.eliminated.join(', ') || 'None'}</span>
                  </div>
                  <div style={styles.metaItem}>
                    <span style={styles.metaLabel}>WinnerDeclared:</span>
                    <span className="badge badge-success" style={{ textTransform: 'uppercase' }}>
                      {reconstructedState.winner || 'Undecided'}
                    </span>
                  </div>
                </div>
              </GlassCard>
            )}

            {activeTab === 'analytics' && (
              <GlassCard title="Leaderboard Snapshot View">
                {reconstructedState.leaderboard ? (
                  <table className="glass-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Contestant ID</th>
                        <th>Composite Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reconstructedState.leaderboard.map((entry: any, index: number) => (
                        <tr key={index}>
                          <td><strong>{entry.rank}</strong></td>
                          <td>{entry.contestant_id}</td>
                          <td>{entry.score.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div style={styles.emptyState}>No leaderboard snapshot computed at this timeline frame.</div>
                )}
              </GlassCard>
            )}

            {activeTab === 'hosting' && (
              <GlassCard title="Active Containers Heartbeats">
                <table className="glass-table">
                  <thead>
                    <tr>
                      <th>Contestant ID</th>
                      <th>Container Node Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reconstructedState.active_pool.map((c: string, idx: number) => (
                      <tr key={idx}>
                        <td><strong>{c}</strong></td>
                        <td>
                          <span className="badge badge-success">RUNNING</span>
                        </td>
                      </tr>
                    ))}
                    {reconstructedState.eliminated.map((c: string, idx: number) => (
                      <tr key={idx}>
                        <td>{c}</td>
                        <td>
                          <span className="badge badge-danger">DESTROYED</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </GlassCard>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  errorBanner: {
    padding: '12px 20px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    marginBottom: '20px',
  },
  topControl: {
    padding: '24px 30px',
    marginBottom: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap' as const,
    gap: '20px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  label: {
    fontSize: '0.8rem',
    fontWeight: '600',
    color: 'var(--text-muted)',
  },
  inputRow: {
    display: 'flex',
    gap: '12px',
  },
  playbackControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
  },
  btnGroup: {
    display: 'flex',
    gap: '8px',
  },
  speedGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  speedLabel: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
  },
  select: {
    padding: '8px 12px',
    cursor: 'pointer',
  },
  timelineScrubber: {
    padding: '24px 30px',
    marginBottom: '24px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  scrubberInfo: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
  },
  slider: {
    width: '100%',
    cursor: 'pointer',
    accentColor: 'var(--primary)',
  },
  detailsContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
  },
  tabHeader: {
    display: 'flex',
    borderBottom: '1px solid var(--border-glass)',
    paddingBottom: '2px',
    gap: '8px',
  },
  tab: {
    background: 'none',
    border: 'none',
    color: 'var(--text-muted)',
    padding: '12px 20px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#fff',
    borderBottom: '3px solid var(--primary)',
  },
  tabContent: {
    marginTop: '10px',
  },
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '20px',
    marginTop: '10px',
  },
  metaItem: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
  },
  metaLabel: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
  metaVal: {
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  emptyState: {
    color: 'var(--text-muted)',
    textAlign: 'center' as const,
    padding: '30px 0',
    fontSize: '0.9rem',
  },
};
export default ReplayViewer;
