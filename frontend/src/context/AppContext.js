// context/AppContext.js
/**
 * Contexto global de la aplicación
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  companyService,
  accountService,
  thirdPartyService,
  transactionService,
  reportService,
  accountingRuleService,
} from '../services/api';
import useAuth from '../hooks/useAuth';
import useNotification from '../hooks/useNotification';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Auth
  const auth = useAuth();

  // Notificaciones
  const notification = useNotification();

  // Estados de datos
  const [companies, setCompanies] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [thirdParties, setThirdParties] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [accountingRules, setAccountingRules] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);

  // Estados de UI
  const [loading, setLoading] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [activeTab, setActiveTab] = useState('transactions');

  // Paginación
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    totalCount: 0,
  });

  // Cargar datos iniciales
  const loadInitialData = useCallback(async () => {
    if (!auth.isAuthenticated) return;

    setLoading(true);
    try {
      const [companiesData, accountsData, thirdPartiesData] = await Promise.all([
        companyService.getAll(),
        accountService.getAll(),
        thirdPartyService.getAll(),
      ]);

      setCompanies(Array.isArray(companiesData) ? companiesData : companiesData.results || []);
      setAccounts(Array.isArray(accountsData) ? accountsData : accountsData.results || []);
      setThirdParties(Array.isArray(thirdPartiesData) ? thirdPartiesData : thirdPartiesData.results || []);

      // Seleccionar primera empresa si hay
      const companiesList = Array.isArray(companiesData) ? companiesData : companiesData.results || [];
      if (companiesList.length > 0 && !selectedCompany) {
        setSelectedCompany(companiesList[0].id);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      notification.showError('Error al cargar datos iniciales');
    } finally {
      setLoading(false);
    }
  }, [auth.isAuthenticated, notification, selectedCompany]);

  // Cargar transacciones
  const loadTransactions = useCallback(async (filters = {}) => {
    if (!auth.isAuthenticated) return;

    setLoading(true);
    try {
      const params = {
        ...filters,
        company: selectedCompany || filters.company,
      };
      const data = await transactionService.getAll(params);

      if (data.results) {
        setTransactions(data.results);
        setPagination({
          page: filters.page || 1,
          totalPages: Math.ceil(data.count / 50),
          totalCount: data.count,
        });
      } else {
        setTransactions(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error loading transactions:', error);
      notification.showError('Error al cargar transacciones');
    } finally {
      setLoading(false);
    }
  }, [auth.isAuthenticated, selectedCompany, notification]);

  // Cargar dashboard stats
  const loadDashboardStats = useCallback(async () => {
    if (!auth.isAuthenticated) return;

    try {
      const data = await reportService.getDashboardStats(selectedCompany);
      setDashboardStats(data);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  }, [auth.isAuthenticated, selectedCompany]);

  // Cargar reglas de clasificación
  const loadAccountingRules = useCallback(async () => {
    if (!auth.isAuthenticated) return;

    try {
      const data = await accountingRuleService.getAll(selectedCompany);
      setAccountingRules(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Error loading accounting rules:', error);
    }
  }, [auth.isAuthenticated, selectedCompany]);

  // Crear transacción
  const createTransaction = useCallback(async (transactionData) => {
    try {
      const result = await transactionService.create(transactionData);
      notification.showSuccess('Transacción creada exitosamente');
      await loadTransactions();
      return { success: true, data: result };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al crear transacción';
      notification.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions, notification]);

  // Actualizar transacción
  const updateTransaction = useCallback(async (id, transactionData) => {
    try {
      const result = await transactionService.update(id, transactionData);
      notification.showSuccess('Transacción actualizada exitosamente');
      await loadTransactions();
      return { success: true, data: result };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al actualizar transacción';
      notification.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions, notification]);

  // Eliminar transacción
  const deleteTransaction = useCallback(async (id) => {
    try {
      await transactionService.delete(id);
      notification.showSuccess('Transacción eliminada exitosamente');
      await loadTransactions();
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al eliminar transacción';
      notification.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions, notification]);

  // Refrescar datos de una empresa
  const refreshCompanyData = useCallback(async () => {
    await Promise.all([
      loadTransactions(),
      loadDashboardStats(),
      loadAccountingRules(),
    ]);
  }, [loadTransactions, loadDashboardStats, loadAccountingRules]);

  // Efecto para cargar datos al autenticarse
  useEffect(() => {
    if (auth.isAuthenticated) {
      loadInitialData();
    }
  }, [auth.isAuthenticated, loadInitialData]);

  // Efecto para cargar datos cuando cambia la empresa seleccionada
  useEffect(() => {
    if (auth.isAuthenticated && selectedCompany) {
      refreshCompanyData();
    }
  }, [auth.isAuthenticated, selectedCompany, refreshCompanyData]);

  const value = {
    // Auth (login, logout, isAuthenticated, token, user)
    login: auth.login,
    logout: auth.logout,
    isAuthenticated: auth.isAuthenticated,
    token: auth.token,
    user: auth.user,
    authLoading: auth.loading,
    authError: auth.error,

    // Notificaciones
    notification: notification.notification,
    showNotification: notification.showNotification,
    showSuccess: notification.showSuccess,
    showError: notification.showError,
    showInfo: notification.showInfo,
    showWarning: notification.showWarning,
    clearNotification: notification.clearNotification,

    // Datos
    companies,
    accounts,
    thirdParties,
    transactions,
    accountingRules,
    dashboardStats,

    // UI - usar authLoading para login, loading para datos
    loading: loading || auth.loading,
    dataLoading: loading,
    selectedCompany,
    setSelectedCompany,
    activeTab,
    setActiveTab,
    pagination,

    // Setters de datos
    setCompanies,
    setAccounts,
    setThirdParties,
    setTransactions,

    // Acciones
    loadInitialData,
    loadTransactions,
    loadDashboardStats,
    loadAccountingRules,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    refreshCompanyData,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export default AppContext;
