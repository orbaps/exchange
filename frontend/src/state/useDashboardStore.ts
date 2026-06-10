import { create } from 'zustand';

export interface LeaderboardEntry {
  contestant_id: string;
  rank: number;
  score: number;
  average_correctness: number;
  average_latency: number;
  average_tps: number;
  success_rate: number;
  campaign_id: string;
  rating_grade: string;
  previous_rank: number | null;
  tournament_id: string | null;
  stage_id: string | null;
}

export interface LeaderboardSnapshot {
  snapshot_id: string;
  campaign_id: string;
  timestamp: string;
  entries: LeaderboardEntry[];
  tournament_id: string | null;
  stage_id: string | null;
  entry_count: number;
  generated_at: string;
  load_profile: string;
  event_count: number;
  campaign_size: number;
  worker_count: number;
  execution_tps: number;
}

export interface TournamentStage {
  stage_id: string;
  stage_type: string;
  campaign_id: string;
}

export interface Tournament {
  tournament_id: string;
  name: string;
  description: string;
  status: string;
  created_at: number;
  start_time: number;
  end_time: number | null;
  stages: TournamentStage[];
}

export interface DeploymentRecord {
  deployment_id: string;
  submission_id: string;
  build_id: string;
  container_id: string;
  status: string;
  created_at: number;
  updated_at: number;
  end_time: number | null;
  error: string | null;
}

export interface DeploymentHealth {
  submission_id: string;
  container_id: string;
  status: string;
  uptime_ns: number;
  restart_count: number;
  failure_count: number;
  last_heartbeat: number;
}

export interface AnalyticsSummary {
  total_scenarios_run: number;
  successful_runs: number;
  failed_runs: number;
  avg_correctness: number;
  avg_latency_ms: number;
  avg_tps: number;
  overall_success_rate: number;
}

interface DashboardState {
  leaderboard: LeaderboardSnapshot | null;
  tournament: Tournament | null;
  deployments: DeploymentRecord[];
  analytics: AnalyticsSummary | null;
  health: DeploymentHealth[];
  isConnected: boolean;
  
  setLeaderboard: (leaderboard: LeaderboardSnapshot | null) => void;
  setTournament: (tournament: Tournament | null) => void;
  setDeployments: (deployments: DeploymentRecord[]) => void;
  upsertDeployment: (record: DeploymentRecord) => void;
  setAnalytics: (analytics: AnalyticsSummary | null) => void;
  setHealth: (health: DeploymentHealth[]) => void;
  setIsConnected: (connected: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  leaderboard: null,
  tournament: null,
  deployments: [],
  analytics: null,
  health: [],
  isConnected: false,

  setLeaderboard: (leaderboard) => set({ leaderboard }),
  setTournament: (tournament) => set({ tournament }),
  setDeployments: (deployments) => set({ deployments }),
  upsertDeployment: (record) => set((state) => {
    const exists = state.deployments.some((d) => d.deployment_id === record.deployment_id);
    const updated = exists
      ? state.deployments.map((d) => (d.deployment_id === record.deployment_id ? record : d))
      : [record, ...state.deployments];
    return { deployments: updated };
  }),
  setAnalytics: (analytics) => set({ analytics }),
  setHealth: (health) => set({ health }),
  setIsConnected: (isConnected) => set({ isConnected })
}));
