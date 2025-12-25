// hooks/useAuth.js
/**
 * Hook para manejar autenticación
 */

import { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/api';

export const useAuth = () => {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuthenticated = !!token;

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const data = await authService.login(username, password);
      const newToken = data.token;
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setUser(data.user || { username });
      return { success: true };
    } catch (err) {
      const errorMessage = err.response?.data?.non_field_errors?.[0]
        || err.response?.data?.detail
        || 'Error de autenticación';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  }, []);

  // Verificar token al cargar
  useEffect(() => {
    if (token) {
      // Opcionalmente verificar que el token sea válido
      // Esto podría hacerse con una llamada a la API
    }
  }, [token]);

  return {
    token,
    user,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
  };
};

export default useAuth;
