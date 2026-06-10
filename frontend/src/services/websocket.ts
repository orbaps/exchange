import { useDashboardStore } from '../state/useDashboardStore';

let socket: WebSocket | null = null;
let reconnectTimeout: number | null = null;

export const wsClient = {
  connect: (token: string) => {
    if (socket) {
      return;
    }

    const wsUrl = `ws://127.0.0.1:8000/api/ws?token=${encodeURIComponent(token)}`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connection established.');
      useDashboardStore.getState().setIsConnected(true);

      // Subscribe to all dashboard channels
      const channels = ['leaderboard', 'analytics', 'tournament', 'health'];
      channels.forEach((channel) => {
        socket?.send(JSON.stringify({
          action: 'subscribe',
          channel: channel
        }));
      });
    };

    socket.onmessage = (event) => {
      try {
        const frame = JSON.parse(event.data);
        const { channel, data } = frame;

        if (!channel) return;

        // Route real-time channel frames to their respective Zustand store actions
        if (channel === 'leaderboard') {
          // data is the LeaderboardSnapshot payload
          useDashboardStore.getState().setLeaderboard(data);
        } else if (channel === 'analytics') {
          // data could contain event_type + payload
          if (data && data.event_type) {
            // Re-fetch analytics REST summary to keep averages 100% accurate,
            // or perform local rollups
            import('./api').then(({ services }) => {
              services.public.getAnalytics().then((summary) => {
                useDashboardStore.getState().setAnalytics(summary);
              }).catch(console.error);
            });
          }
        } else if (channel === 'tournament') {
          // Trigger a refresh of the tournament structure
          import('./api').then(({ services }) => {
            services.public.getTournament().then((t) => {
              useDashboardStore.getState().setTournament(t);
            }).catch(console.error);
          });
        } else if (channel === 'health') {
          // data is health reports list
          if (Array.isArray(data)) {
            useDashboardStore.getState().setHealth(data);
          } else if (data && typeof data === 'object') {
            const list = Object.values(data).filter(r => typeof r === 'object') as any[];
            useDashboardStore.getState().setHealth(list);
          }
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    socket.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
      useDashboardStore.getState().setIsConnected(false);
      socket = null;

      // Exponential backoff reconnect
      reconnectTimeout = window.setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        wsClient.connect(token);
      }, 5000);
    };

    socket.onerror = (err) => {
      console.error('WebSocket encountered an error:', err);
    };
  },

  disconnect: () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (socket) {
      socket.close();
      socket = null;
    }
    useDashboardStore.getState().setIsConnected(false);
  }
};
