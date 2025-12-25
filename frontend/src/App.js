// App.js
/**
 * Aplicación principal PeppiniContable
 * Sistema Contable por Partida Doble
 */

import React, { useState } from 'react';
import './App.css';

// Context
import { AppProvider, useApp } from './context/AppContext';

// Components
import {
  Notification,
  LoginForm,
  Header,
  Navigation,
  TransactionForm,
  TransactionList,
  Dashboard,
} from './components';

// Placeholder components para tabs pendientes
const ReportsTab = () => (
  <div className="card">
    <div className="card-header">
      <h2 className="card-title">Reportes</h2>
    </div>
    <div className="empty-state">
      <p>Sección de reportes en desarrollo</p>
    </div>
  </div>
);

const RulesTab = () => {
  const { accountingRules, loading } = useApp();

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">
          <span className="loading"></span>
          <p>Cargando reglas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Reglas de Clasificación IA</h2>
        <span className="badge">{accountingRules?.length || 0} reglas</span>
      </div>
      {accountingRules && accountingRules.length > 0 ? (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>NIT Tercero</th>
                <th>Nombre</th>
                <th>Cuenta</th>
                <th>Confianza</th>
                <th>Último Monto</th>
              </tr>
            </thead>
            <tbody>
              {accountingRules.map((rule) => (
                <tr key={rule.id}>
                  <td style={{ fontFamily: 'monospace' }}>{rule.third_party_nit}</td>
                  <td>{rule.third_party_name}</td>
                  <td>
                    <span style={{ fontWeight: '600' }}>{rule.account_code}</span>
                    {' - '}{rule.account_name}
                  </td>
                  <td>
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      background: rule.confidence_score > 5 ? '#dcfce7' : '#fef3c7',
                      color: rule.confidence_score > 5 ? '#15803d' : '#b45309',
                      fontWeight: '500',
                    }}>
                      {rule.confidence_score} usos
                    </span>
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                    ${new Intl.NumberFormat('es-CO').format(rule.last_amount || 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <p>No hay reglas de clasificación. Se crearán automáticamente al procesar transacciones.</p>
        </div>
      )}
    </div>
  );
};

const ExportTab = () => {
  const { companies, selectedCompany, showSuccess, showError } = useApp();
  const [exportForm, setExportForm] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
  });
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!selectedCompany) {
      showError('Selecciona una empresa primero');
      return;
    }

    setExporting(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/export-excel/${selectedCompany}/${exportForm.year}/${exportForm.month}/`,
        {
          headers: {
            Authorization: `Token ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) throw new Error('Error al exportar');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `libro_diario_${exportForm.year}_${exportForm.month}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showSuccess('Archivo exportado exitosamente');
    } catch (error) {
      showError('Error al exportar: ' + error.message);
    } finally {
      setExporting(false);
    }
  };

  const currentCompany = companies.find((c) => c.id === selectedCompany);

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Exportar a Excel</h2>
      </div>
      <div style={{ padding: '20px' }}>
        <p style={{ marginBottom: '20px', color: '#64748b' }}>
          Exporta el libro diario de {currentCompany?.name || 'la empresa seleccionada'} a formato Excel.
        </p>

        <div className="form-grid">
          <div className="form-group">
            <label>Año</label>
            <select
              value={exportForm.year}
              onChange={(e) => setExportForm((prev) => ({ ...prev, year: Number(e.target.value) }))}
              className="form-control"
            >
              {[2023, 2024, 2025].map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Mes</label>
            <select
              value={exportForm.month}
              onChange={(e) => setExportForm((prev) => ({ ...prev, month: Number(e.target.value) }))}
              className="form-control"
            >
              {[
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
              ].map((month, idx) => (
                <option key={idx} value={idx + 1}>{month}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting || !selectedCompany}
          className="btn btn-primary"
          style={{ marginTop: '20px' }}
        >
          {exporting ? (
            <>
              <span className="loading"></span>
              Exportando...
            </>
          ) : (
            'Descargar Excel'
          )}
        </button>
      </div>
    </div>
  );
};

const SettingsTab = () => (
  <div className="card">
    <div className="card-header">
      <h2 className="card-title">Configuración</h2>
    </div>
    <div className="empty-state">
      <p>Opciones de configuración en desarrollo</p>
    </div>
  </div>
);

// Componente principal del contenido
const MainContent = () => {
  const { activeTab, setActiveTab } = useApp();
  const [editingTransaction, setEditingTransaction] = useState(null);

  const handleEditTransaction = (transaction) => {
    setEditingTransaction(transaction);
    setActiveTab('new');
  };

  const handleFormSuccess = () => {
    setEditingTransaction(null);
    setActiveTab('transactions');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'transactions':
        return (
          <>
            <Dashboard />
            <TransactionList onEdit={handleEditTransaction} />
          </>
        );

      case 'new':
        return (
          <TransactionForm
            initialData={editingTransaction}
            onSuccess={handleFormSuccess}
          />
        );

      case 'reports':
        return <ReportsTab />;

      case 'rules':
        return <RulesTab />;

      case 'export':
        return <ExportTab />;

      case 'settings':
        return <SettingsTab />;

      default:
        return <TransactionList onEdit={handleEditTransaction} />;
    }
  };

  return (
    <div className="container">
      <Navigation />
      {renderContent()}
    </div>
  );
};

// Componente de la aplicación autenticada
const AuthenticatedApp = () => {
  const { notification } = useApp();

  return (
    <div className="App">
      <Header />
      <MainContent />
      <Notification notification={notification} />
    </div>
  );
};

// Componente raíz
const AppContent = () => {
  const { isAuthenticated, loading } = useApp();

  if (loading) {
    return (
      <div className="login-container">
        <div style={{ textAlign: 'center', color: 'white' }}>
          <span className="loading" style={{ width: '40px', height: '40px', borderColor: 'white', borderTopColor: 'transparent' }}></span>
          <p style={{ marginTop: '20px' }}>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return <AuthenticatedApp />;
};

// App principal con Provider
function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
