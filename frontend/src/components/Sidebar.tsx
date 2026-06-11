import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../state/useAuthStore';

export const Sidebar: React.FC = () => {
  const { role, logout, username } = useAuthStore();
  const isAdmin = role === 'admin';

  return (
    <aside style={styles.sidebar} className="glass-panel">
      <div style={styles.logoArea}>
        <div style={styles.logoIcon}>IICPC</div>
        <div style={styles.logoText}>RUNTIME</div>
      </div>
      
      <nav style={styles.nav}>
        <NavLink to="/" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>📊</span> Overview
        </NavLink>
        <NavLink to="/leaderboard" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>🏆</span> Leaderboard
        </NavLink>
        <NavLink to="/tournament" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>⚡</span> Tournament
        </NavLink>
        <NavLink to="/deployments" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>📦</span> Deployments
        </NavLink>
        <NavLink to="/analytics" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>📈</span> Analytics
        </NavLink>
        <NavLink to="/replay" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
          <span>🕒</span> Replay Viewer
        </NavLink>
        
        {isAdmin && (
          <>
            <NavLink to="/operations" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>⚙️</span> Mission Control
            </NavLink>
            <NavLink to="/governance" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>⚖️</span> Governance
            </NavLink>
            <NavLink to="/forecast" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🔮</span> Forecasts
            </NavLink>
            <NavLink to="/risks" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>⚠️</span> Risks
            </NavLink>
            <NavLink to="/simulation" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🧪</span> Simulations
            </NavLink>
            <div style={{ marginTop: '10px', marginBottom: '5px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Strategic</div>
            <NavLink to="/strategic" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🗺️</span> Strategic Center
            </NavLink>
            <NavLink to="/multi-cluster" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🌐</span> Multi-Cluster
            </NavLink>
            <NavLink to="/recovery" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🏥</span> Recovery Center
            </NavLink>
            <NavLink to="/policy-hierarchy" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>📜</span> Policy Hierarchy
            </NavLink>
            <div style={{ marginTop: '10px', marginBottom: '5px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Cloud</div>
            <NavLink to="/cloud-operations" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>☁️</span> Operations Center
            </NavLink>
            <NavLink to="/deployments-gitops" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🚀</span> Deployment Center
            </NavLink>
            <div style={{ marginTop: '10px', marginBottom: '5px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Certification</div>
            <NavLink to="/benchmarking" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>⏱️</span> Benchmark Center
            </NavLink>
            <NavLink to="/performance-lab" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🔬</span> Performance Lab
            </NavLink>
            <NavLink to="/certification" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>🏆</span> Certification
            </NavLink>
            <NavLink to="/showcase" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>✨</span> Showcase
            </NavLink>
            <div style={{ marginTop: '10px', marginBottom: '5px', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Release</div>
            <NavLink to="/release" style={({ isActive }) => isActive ? { ...styles.link, ...styles.linkActive } : styles.link}>
              <span>📦</span> Release Center
            </NavLink>
          </>
        )}
      </nav>

      <div style={styles.footer}>
        <div style={styles.userBadge}>
          <div style={styles.userDot(isAdmin)}></div>
          <div>
            <div style={styles.userName}>{username || 'Guest'}</div>
            <div style={styles.userRole}>{role === 'admin' ? 'Operator' : 'Public'}</div>
          </div>
        </div>
        <button onClick={logout} style={styles.logoutBtn}>
          Exit Console
        </button>
      </div>
    </aside>
  );
};

const styles = {
  sidebar: {
    width: '260px',
    height: 'calc(100vh - 40px)',
    margin: '20px 0 20px 20px',
    padding: '30px 20px',
    display: 'flex',
    flexDirection: 'column' as const,
    borderRight: '1px solid var(--border-glass)',
    position: 'sticky' as const,
    top: '20px',
    zIndex: 10,
  },
  logoArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '40px',
  },
  logoIcon: {
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    color: '#fff',
    padding: '6px 12px',
    borderRadius: '8px',
    fontWeight: '800',
    fontSize: '1rem',
    letterSpacing: '1px',
  },
  logoText: {
    fontWeight: '700',
    fontSize: '1.2rem',
    letterSpacing: '1.5px',
    background: 'linear-gradient(135deg, #fff, #a78bfa)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  nav: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
    flex: 1,
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    color: 'var(--text-muted)',
    textDecoration: 'none',
    borderRadius: '10px',
    fontSize: '0.95rem',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
  linkActive: {
    background: 'rgba(139, 92, 246, 0.15)',
    color: '#fff',
    borderLeft: '4px solid var(--primary)',
    paddingLeft: '12px',
  },
  footer: {
    borderTop: '1px solid var(--border-glass)',
    paddingTop: '20px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '15px',
  },
  userBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  userDot: (isAdmin: boolean) => ({
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    backgroundColor: isAdmin ? 'var(--primary)' : 'var(--secondary)',
    boxShadow: `0 0 10px ${isAdmin ? 'var(--primary)' : 'var(--secondary)'}`,
  }),
  userName: {
    fontWeight: '600',
    fontSize: '0.9rem',
  },
  userRole: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  },
  logoutBtn: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    color: 'var(--danger)',
    padding: '10px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.85rem',
    transition: 'all 0.2s',
  },
};
