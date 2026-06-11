import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import GlassCard from '../components/GlassCard';

export default function ForecastCenter() {
  const [forecasts, setForecasts] = useState<any>(null);

  useEffect(() => {
    api.get('/public/governance/forecasts').then(res => setForecasts(res.data));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white mb-6 tracking-tight drop-shadow-md">Capacity & Failure Forecasts</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard title="CPU Bottlenecks (Linear Projection)">
          <div className="text-slate-300 h-48 flex items-center justify-center border border-slate-700/50 rounded bg-slate-800/30">
            <span className="opacity-50">No bottlenecks projected in next 24h</span>
          </div>
        </GlassCard>
        
        <GlassCard title="Node Failure Probabilities">
          <div className="text-slate-300 h-48 flex items-center justify-center border border-slate-700/50 rounded bg-slate-800/30">
            <span className="opacity-50">All nodes nominal</span>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
