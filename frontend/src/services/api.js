// services/api.js
/**
 * Servicio centralizado para todas las llamadas a la API
 */

import axios from 'axios';

// Configuración base de la API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Crear instancia de axios con configuración base
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token de autenticación
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar respuestas y errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Manejar errores de autenticación
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==============================================================================
// AUTENTICACIÓN
// ==============================================================================

export const authService = {
  login: async (username, password) => {
    const response = await axios.post(`${API_BASE_URL.replace('/api', '')}/api-token-auth/`, {
      username,
      password,
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};

// ==============================================================================
// EMPRESAS
// ==============================================================================

export const companyService = {
  getAll: async () => {
    const response = await api.get('/companies/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/companies/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/companies/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/companies/${id}/`, data);
    return response.data;
  },
};

// ==============================================================================
// CUENTAS CONTABLES
// ==============================================================================

export const accountService = {
  getAll: async () => {
    const response = await api.get('/accounts/');
    return response.data;
  },

  getByCode: async (code) => {
    const response = await api.get(`/accounts/?code=${code}`);
    return response.data;
  },

  search: async (query) => {
    const response = await api.get(`/accounts/?search=${query}`);
    return response.data;
  },
};

// ==============================================================================
// TERCEROS
// ==============================================================================

export const thirdPartyService = {
  getAll: async () => {
    const response = await api.get('/third-parties/');
    return response.data;
  },

  getByNit: async (nit) => {
    const response = await api.get(`/third-parties/?nit=${nit}`);
    return response.data;
  },

  search: async (query) => {
    const response = await api.get(`/third-parties/?search=${query}`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/third-parties/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/third-parties/${id}/`, data);
    return response.data;
  },
};

// ==============================================================================
// TRANSACCIONES
// ==============================================================================

export const transactionService = {
  getAll: async (params = {}) => {
    const response = await api.get('/transactions/', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/transactions/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/transactions/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.post(`/transactions/${id}/edit/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.post(`/transactions/${id}/delete/`);
    return response.data;
  },

  validate: async (data) => {
    const response = await api.post('/transactions/validate/', data);
    return response.data;
  },

  correct: async (id, data) => {
    const response = await api.post(`/transactions/${id}/corregir/`, data);
    return response.data;
  },

  calculateCorrections: async (id) => {
    const response = await api.post(`/transactions/${id}/calcular-correcciones/`);
    return response.data;
  },
};

// ==============================================================================
// MOVIMIENTOS
// ==============================================================================

export const movementService = {
  getAll: async (params = {}) => {
    const response = await api.get('/movements/', { params });
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.post(`/movements/${id}/edit/`, data);
    return response.data;
  },
};

// ==============================================================================
// REPORTES Y EXPORTACIÓN
// ==============================================================================

export const reportService = {
  exportExcel: async (companyId, year, month) => {
    const response = await api.get(`/export-excel/${companyId}/${year}/${month}/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getDashboardStats: async (companyId = null) => {
    const params = companyId ? { company: companyId } : {};
    const response = await api.get('/dashboard/stats/', { params });
    return response.data;
  },
};

// ==============================================================================
// REGLAS DE CLASIFICACIÓN
// ==============================================================================

export const accountingRuleService = {
  getAll: async (companyId = null) => {
    const params = companyId ? { company: companyId } : {};
    const response = await api.get('/accounting-rules/', { params });
    return response.data;
  },

  delete: async (id) => {
    const response = await api.post(`/accounting-rules/${id}/delete/`);
    return response.data;
  },
};

// ==============================================================================
// PROCESAMIENTO DE ARCHIVOS
// ==============================================================================

export const processingService = {
  processFacturasExcel: async (formData) => {
    const response = await api.post('/procesar-facturas-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutos para archivos grandes
    });
    return response.data;
  },

  processCompressedFile: async (formData) => {
    const response = await api.post('/procesar-comprimido/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutos para archivos comprimidos
    });
    return response.data;
  },
};

// ==============================================================================
// TRANSACCIONES RECURRENTES
// ==============================================================================

export const recurringService = {
  generate: async () => {
    const response = await api.post('/recurring/generate/');
    return response.data;
  },
};

// ==============================================================================
// UTILIDADES
// ==============================================================================

/**
 * Descarga un archivo blob con el nombre especificado
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Maneja errores de API de forma consistente
 */
export const handleApiError = (error) => {
  if (error.response) {
    // El servidor respondió con un código de error
    const data = error.response.data;
    if (data.error?.details) {
      return data.error.details;
    }
    if (data.detail) {
      return data.detail;
    }
    if (typeof data === 'string') {
      return data;
    }
    return 'Error del servidor';
  }
  if (error.request) {
    // No hubo respuesta del servidor
    return 'No se pudo conectar con el servidor';
  }
  // Error de configuración
  return error.message || 'Error desconocido';
};

export default api;
