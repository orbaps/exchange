import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-inject JWT token if stored
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// REST Call Helpers
export const services = {
  auth: {
    login: async (username: string, password: string) => {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);
      
      const response = await api.post('/api/auth/token', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    },
  },
  public: {
    getLeaderboard: async () => {
      const response = await api.get('/api/public/leaderboard');
      return response.data;
    },
    getTournament: async () => {
      const response = await api.get('/api/public/tournament');
      return response.data;
    },
    getDeployments: async () => {
      const response = await api.get('/api/public/deployments');
      return response.data;
    },
    getAnalytics: async () => {
      const response = await api.get('/api/public/analytics');
      return response.data;
    },
    getReplayTimeline: async (tournamentId: string) => {
      const response = await api.get(`/api/public/replay/${tournamentId}`);
      return response.data;
    },
    getReplaySnapshot: async (tournamentId: string, index: number) => {
      const response = await api.get(`/api/public/replay/${tournamentId}/snapshot/${index}`);
      return response.data;
    },
  },
  admin: {
    startTournament: async (contestantCount: number = 4) => {
      const response = await api.post('/api/admin/tournament/start', {
        contestant_count: contestantCount
      });
      return response.data;
    },
    stopTournament: async () => {
      const response = await api.post('/api/admin/tournament/stop');
      return response.data;
    },
    rebuildDatabase: async (tJournal?: string, hJournal?: string) => {
      const response = await api.post('/api/admin/replay/rebuild', {
        tournament_journal_path: tJournal || null,
        hosting_journal_path: hJournal || null
      });
      return response.data;
    },
  },
};
