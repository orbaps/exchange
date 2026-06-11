import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import GlassCard from '../components/GlassCard';

export default function RiskCenter() {
  const [risks, setRisks] = useState<any[]>([]);

  useEffect(() => {
    api.get('/public/governance/risks').then(res => setRisks(res.data || []));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white mb-6 tracking-tight drop-shadow-md">Risk Assessment Center</h1>
      
      <GlassCard title="Active Correlated Risks">
        {risks.length === 0 ? (
          <div className="p-8 text-center text-slate-400 italic">
            Zero active risks detected across the cluster.
          </div>
        ) : (
          <div className="space-y-4">
            {risks.map((risk, i) => (
              <div key={i} className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-red-400 font-bold">{risk.category}</h3>
                  <span className="px-2 py-1 text-xs font-bold bg-red-500/20 text-red-300 rounded">
                    {risk.severity}
                  </span>
                </div>
                <p className="text-sm text-slate-300">Confidence: {(risk.confidence?.score * 100).toFixed(1)}%</p>
                <p className="text-sm text-slate-400 mt-1">{risk.confidence?.rationale}</p>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
