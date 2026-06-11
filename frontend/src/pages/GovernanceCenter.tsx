import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import GlassCard from '../components/GlassCard';

export default function GovernanceCenter() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    api.get('/public/governance/status').then(res => setStatus(res.data));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white mb-6 tracking-tight drop-shadow-md">Autonomous Governance Center</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard title="Active Policies">
          <div className="text-4xl font-light text-blue-400">{status?.policies_active || 0}</div>
          <p className="text-sm text-slate-400 mt-2">Currently enforcing</p>
        </GlassCard>
        
        <GlassCard title="Pending Approvals">
          <div className="text-4xl font-light text-orange-400">{status?.decisions_pending || 0}</div>
          <p className="text-sm text-slate-400 mt-2">Requires review</p>
        </GlassCard>

        <GlassCard title="Active Risks">
          <div className="text-4xl font-light text-red-400">{status?.active_risks || 0}</div>
          <p className="text-sm text-slate-400 mt-2">Being mitigated</p>
        </GlassCard>
      </div>

      <GlassCard title="Recent Decisions">
        <div className="text-slate-300">
          <p className="italic opacity-70">No recent decisions...</p>
        </div>
      </GlassCard>
    </div>
  );
}
