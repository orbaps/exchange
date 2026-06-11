import React, { useState } from 'react';
import { api } from '../services/api';
import GlassCard from '../components/GlassCard';

export default function SimulationStudio() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  const runSim = async (type: string) => {
    setRunning(true);
    try {
      const res = await api.post('/admin/governance/simulate', {
        sim_type: type,
        target_nodes: ["node_1"],
        parameters: { cpu_increase: 50 }
      });
      setResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-white mb-6 tracking-tight drop-shadow-md">Deterministic Simulation Studio</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard title="Scenario Sandbox">
          <p className="text-sm text-slate-400 mb-4">
            Hypothesize cluster behavior under stress deterministically.
          </p>
          <div className="space-y-3">
            <button 
              onClick={() => runSim('NODE_FAILURE')}
              disabled={running}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded transition-colors disabled:opacity-50">
              Simulate Node Failure
            </button>
            <button 
              onClick={() => runSim('PARTITION')}
              disabled={running}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded transition-colors disabled:opacity-50">
              Simulate Network Partition
            </button>
            <button 
              onClick={() => runSim('CAPACITY')}
              disabled={running}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded transition-colors disabled:opacity-50">
              Simulate 50% CPU Spike
            </button>
          </div>
        </GlassCard>
        
        <GlassCard title="Simulation Result">
          {running ? (
            <div className="flex items-center justify-center h-full text-blue-400 animate-pulse">
              Running deterministic simulation...
            </div>
          ) : result ? (
            <div className="space-y-2 text-sm text-slate-300">
              <div className="flex justify-between">
                <span>Success:</span>
                <span className={result.success ? "text-green-400" : "text-red-400"}>
                  {result.success ? "YES" : "NO"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Quorum Maintained:</span>
                <span className={result.quorum_maintained ? "text-green-400" : "text-red-400"}>
                  {result.quorum_maintained ? "YES" : "NO"}
                </span>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700">
                <span className="block text-slate-400 mb-1">State Fingerprint (SHA256):</span>
                <code className="text-xs break-all text-blue-300">{result.state_fingerprint || "N/A"}</code>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-500 italic mt-10">
              Run a scenario to see outcomes.
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
