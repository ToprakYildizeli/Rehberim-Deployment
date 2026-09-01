import { createContext, useContext, useState, useCallback } from 'react';
import { logout as apiLogout } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('access'));
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('refresh'));
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  const saveSession = useCallback((access, refresh, userData) => {
    setAccessToken(access);
    setRefreshToken(refresh);
    setUser(userData);
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  /** Oturumu bozmadan yalnızca kullanıcı objesini tazeler (profil kaydedince). */
  const updateUser = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  const clearSession = useCallback(async () => {
    if (refreshToken && accessToken) {
      try { await apiLogout(refreshToken, accessToken); } catch (_) {}
    }
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
  }, [accessToken, refreshToken]);

  return (
    <AuthContext.Provider
      value={{ user, accessToken, saveSession, updateUser, clearSession, isLoggedIn: !!accessToken }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
