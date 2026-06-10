import React from 'react';

interface GlassCardProps {
  title?: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({ title, children, style, className = '' }) => {
  return (
    <div style={{ ...styles.card, ...style }} className={`glass-panel animate-fade-in ${className}`}>
      {title && <h3 style={styles.title}>{title}</h3>}
      <div>{children}</div>
    </div>
  );
};

const styles = {
  card: {
    padding: '24px',
    marginBottom: '24px',
  },
  title: {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#fff',
    borderBottom: '1px solid var(--border-glass)',
    paddingBottom: '10px',
  },
};
