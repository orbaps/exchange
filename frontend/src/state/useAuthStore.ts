import { create } from 'zustand';

interface AuthState {
  token: string | null;
  role: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (token: string, role: string, username: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  // Try to load initial state from localStorage
  const savedToken = localStorage.getItem('token');
  const savedRole = localStorage.getItem('role');
  const savedUsername = localStorage.getItem('username');

  return {
    token: savedToken,
    role: savedRole,
    username: savedUsername,
    isAuthenticated: !!savedToken,
    login: (token, role, username) => {
      localStorage.setItem('token', token);
      localStorage.setItem('role', role);
      localStorage.setItem('username', username);
      set({ token, role, username, isAuthenticated: true });
    },
    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('username');
      set({ token: null, role: null, username: null, isAuthenticated: false });
    }
  };
});
