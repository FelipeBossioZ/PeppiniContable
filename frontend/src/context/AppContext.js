// context/AppContext.js
/**
 * Contexto global de la aplicación
 * Corregido: Eliminadas dependencias circulares que causaban bucles infinitos
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
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

  // Ref para evitar dependencias circulares en callbacks
  const notificationRef = useRef(notification);
  notificationRef.current = notification;

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

  // Control para evitar cargas duplicadas
  const [initialDataLoaded, setInitialDataLoaded] = useState(false);
  const loadingRef = useRef(false);

  // Paginación
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    totalCount: 0,
  });

  // Cargar datos iniciales (solo una vez)
  const loadInitialData = useCallback(async () => {
    // Prevenir cargas duplicadas
    if (loadingRef.current || initialDataLoaded) return;
    loadingRef.current = true;

    setLoading(true);
    try {
      const [companiesData, accountsData, thirdPartiesData] = await Promise.all([
        companyService.getAll(),
        accountService.getAll(),
        thirdPartyService.getAll(),
      ]);

      const companiesList = Array.isArray(companiesData) ? companiesData : companiesData.results || [];
      const accountsList = Array.isArray(accountsData) ? accountsData : accountsData.results || [];
      const thirdPartiesList = Array.isArray(thirdPartiesData) ? thirdPartiesData : thirdPartiesData.results || [];

      setCompanies(companiesList);
      setAccounts(accountsList);
      setThirdParties(thirdPartiesList);

      // Seleccionar primera empresa si hay
      if (companiesList.length > 0) {
        setSelectedCompany(companiesList[0].id);
      }

      setInitialDataLoaded(true);
    } catch (error) {
      console.error('Error loading initial data:', error);
      notificationRef.current.showError('Error al cargar datos iniciales');
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [initialDataLoaded]); // Solo depende de initialDataLoaded

  // Cargar transacciones
  const loadTransactions = useCallback(async (filters = {}, companyId = null) => {
    const company = companyId || selectedCompany;
    if (!company) return;

    setLoading(true);
    try {
      const params = {
        ...filters,
        company,
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
      notificationRef.current.showError('Error al cargar transacciones');
    } finally {
      setLoading(false);
    }
  }, [selectedCompany]);

  // Cargar dashboard stats
  const loadDashboardStats = useCallback(async (companyId = null) => {
    const company = companyId || selectedCompany;
    if (!company) return;

    try {
      const data = await reportService.getDashboardStats(company);
      setDashboardStats(data);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  }, [selectedCompany]);

  // Cargar reglas de clasificación
  const loadAccountingRules = useCallback(async (companyId = null) => {
    const company = companyId || selectedCompany;
    if (!company) return;

    try {
      const data = await accountingRuleService.getAll(company);
      setAccountingRules(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      console.error('Error loading accounting rules:', error);
    }
  }, [selectedCompany]);

  // Crear transacción
  const createTransaction = useCallback(async (transactionData) => {
    try {
      const result = await transactionService.create(transactionData);
      notificationRef.current.showSuccess('Transacción creada exitosamente');
      await loadTransactions();
      return { success: true, data: result };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al crear transacción';
      notificationRef.current.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions]);

  // Actualizar transacción
  const updateTransaction = useCallback(async (id, transactionData) => {
    try {
      const result = await transactionService.update(id, transactionData);
      notificationRef.current.showSuccess('Transacción actualizada exitosamente');
      await loadTransactions();
      return { success: true, data: result };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al actualizar transacción';
      notificationRef.current.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions]);

  // Eliminar transacción
  const deleteTransaction = useCallback(async (id) => {
    try {
      await transactionService.delete(id);
      notificationRef.current.showSuccess('Transacción eliminada exitosamente');
      await loadTransactions();
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Error al eliminar transacción';
      notificationRef.current.showError(errorMsg);
      return { success: false, error: errorMsg };
    }
  }, [loadTransactions]);

  // Refrescar datos de una empresa
  const refreshCompanyData = useCallback(async (companyId = null) => {
    const company = companyId || selectedCompany;
    if (!company) return;

    await Promise.all([
      loadTransactions({}, company),
      loadDashboardStats(company),
      loadAccountingRules(company),
    ]);
  }, [loadTransactions, loadDashboardStats, loadAccountingRules, selectedCompany]);

  // Efecto para cargar datos al autenticarse (solo una vez)
  useEffect(() => {
    if (auth.isAuthenticated && !initialDataLoaded) {
      loadInitialData();
    }
  }, [auth.isAuthenticated, initialDataLoaded, loadInitialData]);

  // Efecto para cargar datos cuando cambia la empresa seleccionada
  useEffect(() => {
    // Solo ejecutar si los datos iniciales ya se cargaron
    // y hay una empresa seleccionada
    if (initialDataLoaded && selectedCompany) {
      refreshCompanyData(selectedCompany);
    }
  }, [selectedCompany]); // Solo depende de selectedCompany, no de las funciones

  // Reset cuando el usuario cierra sesión
  useEffect(() => {
    if (!auth.isAuthenticated) {
      setCompanies([]);
      setAccounts([]);
      setThirdParties([]);
      setTransactions([]);
      setAccountingRules([]);
      setDashboardStats(null);
      setSelectedCompany(null);
      setInitialDataLoaded(false);
    }
  }, [auth.isAuthenticated]);

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
