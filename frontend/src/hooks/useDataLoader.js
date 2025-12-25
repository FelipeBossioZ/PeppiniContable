// hooks/useDataLoader.js
/**
 * Hook para cargar datos de la API con estados de carga y error
 */

import { useState, useCallback, useEffect } from 'react';

export const useDataLoader = (fetchFunction, dependencies = [], autoLoad = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunction(...args);
      setData(result);
      setLastUpdated(new Date());
      return { success: true, data: result };
    } catch (err) {
      const errorMessage = err.response?.data?.detail
        || err.response?.data?.message
        || err.message
        || 'Error al cargar datos';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [fetchFunction]);

  const refresh = useCallback(async (...args) => {
    return load(...args);
  }, [load]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setLastUpdated(null);
  }, []);

  // Cargar automáticamente si autoLoad es true
  useEffect(() => {
    if (autoLoad) {
      load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  return {
    data,
    loading,
    error,
    lastUpdated,
    load,
    refresh,
    reset,
    setData,
  };
};

/**
 * Hook para manejar paginación
 */
export const usePagination = (fetchFunction, pageSize = 50) => {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (pageNum = 1, filters = {}) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunction({ page: pageNum, page_size: pageSize, ...filters });

      // Manejar diferentes formatos de respuesta
      if (result.results) {
        // Respuesta paginada de DRF
        setItems(result.results);
        setTotalCount(result.count || 0);
        setTotalPages(Math.ceil((result.count || 0) / pageSize));
      } else if (Array.isArray(result)) {
        // Respuesta sin paginación
        setItems(result);
        setTotalCount(result.length);
        setTotalPages(1);
      } else {
        setItems([]);
      }

      setPage(pageNum);
      return { success: true };
    } catch (err) {
      setError(err.message || 'Error al cargar datos');
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, pageSize]);

  const nextPage = useCallback((filters = {}) => {
    if (page < totalPages) {
      return load(page + 1, filters);
    }
  }, [page, totalPages, load]);

  const prevPage = useCallback((filters = {}) => {
    if (page > 1) {
      return load(page - 1, filters);
    }
  }, [page, load]);

  const goToPage = useCallback((pageNum, filters = {}) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      return load(pageNum, filters);
    }
  }, [totalPages, load]);

  return {
    items,
    page,
    totalPages,
    totalCount,
    loading,
    error,
    load,
    nextPage,
    prevPage,
    goToPage,
    hasNextPage: page < totalPages,
    hasPrevPage: page > 1,
  };
};

export default useDataLoader;
