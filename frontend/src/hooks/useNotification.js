// hooks/useNotification.js
/**
 * Hook para manejar notificaciones
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export const useNotification = (defaultTimeout = 3000) => {
  const [notification, setNotification] = useState(null);
  const timeoutRef = useRef(null);

  const clearNotification = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setNotification(null);
  }, []);

  const showNotification = useCallback((message, type = 'info', timeout = defaultTimeout) => {
    // Limpiar notificación anterior
    clearNotification();

    setNotification({ message, type });

    if (timeout > 0) {
      timeoutRef.current = setTimeout(() => {
        setNotification(null);
      }, timeout);
    }
  }, [clearNotification, defaultTimeout]);

  const showSuccess = useCallback((message, timeout) => {
    showNotification(message, 'success', timeout);
  }, [showNotification]);

  const showError = useCallback((message, timeout = 5000) => {
    showNotification(message, 'error', timeout);
  }, [showNotification]);

  const showInfo = useCallback((message, timeout) => {
    showNotification(message, 'info', timeout);
  }, [showNotification]);

  const showWarning = useCallback((message, timeout = 4000) => {
    showNotification(message, 'warning', timeout);
  }, [showNotification]);

  // Limpiar timeout al desmontar
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    notification,
    showNotification,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    clearNotification,
  };
};

export default useNotification;
