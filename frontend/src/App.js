// App.js - SISTEMA CONTABLE CON PARTIDA DOBLE
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [transactions, setTransactions] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [thirdParties, setThirdParties] = useState([]);
  const [activeTab, setActiveTab] = useState('transactions');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [alertasContables, setAlertasContables] = useState(null);

  
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [reportForm, setReportForm] = useState({
    company: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1
  });

  // ========== NUEVO FORMULARIO PARTIDA DOBLE ==========
  const [transactionForm, setTransactionForm] = useState({
    company: '',
    date: new Date().toISOString().split('T')[0],
    concept: '',
    additional_description: '',
    movements: [
      { account: '', third_party: '', debit: 0, credit: 0, description: '' },
      { account: '', third_party: '', debit: 0, credit: 0, description: '' }
    ]
  });

  // ========== NOTIFICACIONES ==========
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // ========== CARGA DE DATOS ==========
  useEffect(() => {
  if (token) fetchAllData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const headers = { 
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      };
      
      const [transRes, compRes, accRes, thirdRes] = await Promise.all([
        axios.get('/api/transactions/', { headers }),
        axios.get('/api/companies/', { headers }),
        axios.get('/api/accounts/', { headers }),
        axios.get('/api/third-parties/', { headers })
      ]);

      setTransactions(Array.isArray(transRes.data.results) ? transRes.data.results : []);
      setCompanies(Array.isArray(compRes.data) ? compRes.data : []);
      setAccounts(Array.isArray(accRes.data) ? accRes.data : []);
      setThirdParties(Array.isArray(thirdRes.data) ? thirdRes.data : []);

    } catch (error) {
      console.error('Error cargando datos:', error);
      showNotification('Error al cargar datos', 'error');
    } finally {
      setLoading(false);
    }
  };

  // ========== LOGIN ==========
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('/api-token-auth/', loginForm);
      const newToken = response.data.token;
      setToken(newToken);
      localStorage.setItem('token', newToken);
      showNotification('¡Ingreso exitoso!', 'success');
    } catch (error) {
      showNotification('Credenciales incorrectas', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
    showNotification('Sesión cerrada', 'info');
  };

  // ========== NUEVO: MANEJO PARTIDA DOBLE ==========
  const handleMovementChange = (index, field, value) => {
    const updatedMovements = [...transactionForm.movements];
    
    if (field === 'debit' || field === 'credit') {
      // Si ingresa débito, pone crédito en 0 y viceversa
      if (field === 'debit' && parseFloat(value) > 0) {
        updatedMovements[index].credit = 0;
      } else if (field === 'credit' && parseFloat(value) > 0) {
        updatedMovements[index].debit = 0;
      }
      updatedMovements[index][field] = parseFloat(value) || 0;
    } else {
      updatedMovements[index][field] = value;
    }
    
    setTransactionForm({ ...transactionForm, movements: updatedMovements });
  };

  const addMovement = () => {
    setTransactionForm({
      ...transactionForm,
      movements: [
        ...transactionForm.movements,
        { account: '', third_party: '', debit: 0, credit: 0, description: '' }
      ]
    });
  };

  const removeMovement = (index) => {
    if (transactionForm.movements.length > 2) {
      const updatedMovements = transactionForm.movements.filter((_, i) => i !== index);
      setTransactionForm({ ...transactionForm, movements: updatedMovements });
    }
  };

  // ========== VALIDACIÓN PARTIDA DOBLE ==========
  const validateTransaction = () => {
    const totalDebit = transactionForm.movements.reduce((sum, m) => sum + parseFloat(m.debit || 0), 0);
    const totalCredit = transactionForm.movements.reduce((sum, m) => sum + parseFloat(m.credit || 0), 0);
    
    if (Math.abs(totalDebit - totalCredit) > 0.01) {
      return { isValid: false, message: `EL ASIENTO NO CUADRA: Débito $${totalDebit} ≠ Crédito $${totalCredit}` };
    }
    
    if (transactionForm.movements.length < 2) {
      return { isValid: false, message: 'Mínimo 2 movimientos por transacción' };
    }

    const emptyFields = transactionForm.movements.some(m => !m.account || !m.third_party);
    if (emptyFields || !transactionForm.company || !transactionForm.concept) {
      return { isValid: false, message: 'Complete todos los campos obligatorios' };
    }

    return { isValid: true };
  };

  // ========== ENVÍO TRANSACCIÓN PARTIDA DOBLE ==========
  // ============================================
// REEMPLAZAR TODA LA FUNCIÓN handleSubmitTransaction
// Busca donde dice: const handleSubmitTransaction = async (e) => {
// Y reemplaza TODA esa función con esta versión:
// ============================================

const handleSubmitTransaction = async (e) => {
  e.preventDefault();
  
  const validation = validateTransaction();
  if (!validation.isValid) {
    showNotification(validation.message, 'error');
    return;
  }

  setLoading(true);
  try {
    const headers = { 
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    };

    // Filtrar movimientos vacíos
    const filteredMovements = transactionForm.movements.filter(m => 
      m.account && m.third_party && (m.debit > 0 || m.credit > 0)
    );

    const transactionData = {
      ...transactionForm,
      movements: filteredMovements
    };
    
    // 1. PRIMERO VALIDAR (SIN GUARDAR)
    const validateResponse = await axios.post(
      '/api/transactions/validate/',
      transactionData,
      { headers }
    );
    
    // 2. SI HAY ALERTAS, MOSTRAR MODAL (NO GUARDAR)
    if (validateResponse.data.alertas && validateResponse.data.alertas.length > 0) {
      setAlertasContables({
        alertas: validateResponse.data.alertas,
        sugerencias: validateResponse.data.sugerencias,
        correcciones: validateResponse.data.correcciones,
        transactionData: transactionData
      });
      setLoading(false);
      return; // NO continuar, esperar respuesta del usuario
    }
    
    // 3. SI NO HAY ALERTAS, GUARDAR DIRECTAMENTE
    const response = await axios.post('/api/transactions/', transactionData, { headers });
    
    setTransactions(prev => [response.data, ...prev]);
    showNotification('✅ Transacción guardada exitosamente', 'success');
    
    // Resetear formulario
    setTransactionForm({
      company: '',
      date: new Date().toISOString().split('T')[0],
      concept: '',
      additional_description: '',
      movements: [
        { account: '', third_party: '', debit: 0, credit: 0, description: '' },
        { account: '', third_party: '', debit: 0, credit: 0, description: '' }
      ]
    });
    
    setActiveTab('transactions');
    
  } catch (error) {
    console.error('Error creando transacción:', error);
    showNotification('Error al crear transacción', 'error');
  } finally {
    setLoading(false);
  }
};

  // ========== EXPORTACIÓN EXCEL ==========
  const handleDownloadReport = async () => {
    const headers = { 
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    };
    const { company, year, month } = reportForm;
    
    if (!company) {
      showNotification('Seleccione una empresa', 'error');
      return;
    }

    try {
      const response = await axios.get(
        `/api/export-excel/${company}/${year}/${month}/`, 
        { 
          headers: headers,
          responseType: 'blob'
        }
      );

      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let fileName = `balance_${year}_${month}.xlsx`;
      
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
        if (fileNameMatch && fileNameMatch.length === 2) {
          fileName = fileNameMatch[1];
        }
      }
      
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showNotification('Reporte descargado exitosamente', 'success');
      
    } catch (error) {
      console.error('Error descargando reporte:', error);
      showNotification('Error al descargar reporte', 'error');
    }
  };

  // ========== FUNCIONES DE FORMATEO ==========
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-CO');
  };

  // ========== CÁLCULO DE ESTADÍSTICAS ==========
 const calculateStats = () => {
  // VERIFICACIÓN MÁS ROBUSTA
  if (!transactions || !Array.isArray(transactions)) {
    return { totalDebits: 0, totalCredits: 0, balance: 0, count: 0 };
  }
  
  let totalDebits = 0;
  let totalCredits = 0;

  transactions.forEach(transaction => {
    // VERIFICAR SI TIENE MOVIMIENTOS
    if (transaction.movements && Array.isArray(transaction.movements)) {
      transaction.movements.forEach(movement => {
        totalDebits += parseFloat(movement.debit || 0);
        totalCredits += parseFloat(movement.credit || 0);
      });
    }
    // COMPATIBILIDAD CON TRANSACCIONES VIEJAS
    else if (transaction.debit || transaction.credit) {
      totalDebits += parseFloat(transaction.debit || 0);
      totalCredits += parseFloat(transaction.credit || 0);
    }
  });

  const balance = totalDebits - totalCredits;
  
  return { 
    totalDebits, 
    totalCredits, 
    balance, 
    count: transactions.length 
  };
};

  const stats = calculateStats();

  // ========== VALIDACIÓN EN TIEMPO REAL ==========
  const getBalanceStatus = () => {
    const totalDebit = transactionForm.movements.reduce((sum, m) => sum + parseFloat(m.debit || 0), 0);
    const totalCredit = transactionForm.movements.reduce((sum, m) => sum + parseFloat(m.credit || 0), 0);
    const difference = Math.abs(totalDebit - totalCredit);
    
    return {
      totalDebit,
      totalCredit,
      isBalanced: difference < 0.01,
      difference
    };
  };

  const balanceStatus = getBalanceStatus();

  // 🔥 PEGA ESTO JUSTO ANTES del "if (!token) {" 
// (al final de todo el código, antes del primer return)

const AlertaContable = ({ alertas, sugerencias, onConfirm, onCancel, onAutoFix  }) => (
  <div style={{
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', 
    justifyContent: 'center', zIndex: 10000
  }}>
    <div style={{
      background: 'white', padding: '30px', borderRadius: '20px',
      maxWidth: '500px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      border: '3px solid #FF6B35'
    }}>
      <div style={{textAlign: 'center', marginBottom: '20px'}}>
        <div style={{fontSize: '48px', marginBottom: '10px'}}>⚠️</div>
        <h3 style={{color: '#FF6B35', margin: '0 0 10px 0'}}>Validación Contable</h3>
        <p style={{color: '#666', margin: 0}}>El sistema detectó posibles inconsistencias</p>
      </div>

      <div style={{marginBottom: '25px'}}>
        <div style={{background: '#FFF3CD', padding: '15px', borderRadius: '10px', marginBottom: '15px'}}>
          <strong style={{color: '#856404'}}>📊 Alertas:</strong>
          <ul style={{margin: '10px 0 0 0', paddingLeft: '20px', color: '#856404'}}>
            {alertas.map((alerta, idx) => <li key={idx}>{alerta}</li>)}
          </ul>
        </div>
        
        <div style={{background: '#D1ECF1', padding: '15px', borderRadius: '10px'}}>
          <strong style={{color: '#0C5460'}}>💡 Sugerencias:</strong>
          <ul style={{margin: '10px 0 0 0', paddingLeft: '20px', color: '#0C5460'}}>
            {sugerencias.map((sug, idx) => <li key={idx}>{sug}</li>)}
          </ul>
        </div>
      </div>

      <div style={{display: 'flex', gap: '10px', justifyContent: 'center'}}>
       <button onClick={onCancel} style={{padding: '12px 24px', border: '2px solid #6C757D', background: 'white', color: '#6C757D', borderRadius: '10px', cursor: 'pointer', fontWeight: 'bold'}}>
        🗑️ Eliminar Asiento
      </button>
      <button onClick={onAutoFix} style={{padding: '12px 24px', border: 'none', background: 'linear-gradient(135deg, #28A745, #20C997)', color: 'white', borderRadius: '10px', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 4px 15px rgba(40, 167, 69, 0.4)'}}>
        🔄 Corregir Automáticamente
      </button>
      <button onClick={onConfirm} style={{padding: '12px 24px', border: 'none', background: 'linear-gradient(135deg, #FF6B35, #FF8E35)', color: 'white', borderRadius: '10px', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 4px 15px rgba(255, 107, 53, 0.4)'}}>
        ✅ Entiendo, Continuar
      </button>
      </div>
    </div>
  </div>
);

  // ========== RENDERIZADO ==========
  if (!token) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="logo-container">
            <div className="logo">TD</div>
          </div>
          <h2 style={{textAlign: 'center', marginBottom: '10px', fontSize: '28px'}}>
            Sistema de Transacciones
          </h2>
          <p style={{textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '30px'}}>
            Gestión contable inteligente
          </p>
          <form onSubmit={handleLogin}>
            <div className="form-group" style={{marginBottom: '20px'}}>
              <label>Usuario</label>
              <input
                type="text"
                className="form-control"
                value={loginForm.username}
                onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                required
                placeholder="Ingrese su usuario"
              />
            </div>
            <div className="form-group" style={{marginBottom: '30px'}}>
              <label>Contraseña</label>
              <input
                type="password"
                className="form-control"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                required
                placeholder="Ingrese su contraseña"
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{width: '100%'}} disabled={loading}>
              {loading ? <span className="loading"></span> : null}
              {loading ? 'Ingresando...' : 'Ingresar al Sistema'}
            </button>
          </form>
        </div>

        {notification && (
          <div className={`notification ${notification.type}`}>
            {notification.type === 'success' && '✓'}
            {notification.type === 'error' && '✗'}
            {notification.message}
          </div>
        )}
      </div>
    );
  }

  // Main App cuando está autenticado
  return (
    <div className="App">
      {/* Notificación */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.type === 'success' && '✓'}
          {notification.type === 'error' && '✗'}
          {notification.type === 'info' && 'ℹ'}
          {notification.message}
        </div>
      )}

      {alertasContables && (
  <AlertaContable
    alertas={alertasContables.alertas}
    sugerencias={alertasContables.sugerencias}
    
    onAutoFix={() => {
      // Aplicar correcciones al formulario
      const correcciones = alertasContables.correcciones;
      
      const movimientosCorregidos = transactionForm.movements.map((mov, index) => {
        const correccion = correcciones.find(c => c.movement_index === index);
        
        if (correccion) {
          return {
            ...mov,
            debit: correccion.debito_corregido,
            credit: correccion.credito_corregido
          };
        }
        
        return mov;
      });
      
      // Actualizar formulario con valores corregidos
      setTransactionForm({
        ...transactionForm,
        movements: movimientosCorregidos
      });
      
      // Cerrar alerta
      setAlertasContables(null);
      
      showNotification('✅ Valores corregidos. Revisa y guarda el asiento.', 'success');
    }}
    
    onConfirm={async () => {
      // Guardar el asiento tal como está (con alertas)
      try {
        const headers = { 
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        };
        
        const response = await axios.post(
          '/api/transactions/',
          alertasContables.transactionData,
          { headers }
        );
        
        setTransactions(prev => [response.data, ...prev]);
        showNotification('✅ Asiento guardado (con alertas)', 'warning');
        
        // Resetear formulario
        setTransactionForm({
          company: '',
          date: new Date().toISOString().split('T')[0],
          concept: '',
          additional_description: '',
          movements: [
            { account: '', third_party: '', debit: 0, credit: 0, description: '' },
            { account: '', third_party: '', debit: 0, credit: 0, description: '' }
          ]
        });
        
        setAlertasContables(null);
        setActiveTab('transactions');
        
      } catch (error) {
        console.error('Error guardando:', error);
        showNotification('❌ Error al guardar', 'error');
      }
    }}
    
    onCancel={() => {
      // Solo cerrar el modal sin guardar nada
      setAlertasContables(null);
      showNotification('Asiento no guardado. Puedes corregir manualmente.', 'info');
    }}
  />
)}

      {/* Header */}
      <div className="header">
        <div className="header-content">
          <div className="header-title">
            <div className="header-logo">TD</div>
            <h1>Sistema Contable - Partida Doble</h1>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary">
            🚪 Cerrar Sesión
          </button>
        </div>
      </div>

      <div className="container">
        {/* Estadísticas */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Débitos</div>
            <div className="stat-value amount-debit">
              {formatCurrency(stats.totalDebits)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Créditos</div>
            <div className="stat-value amount-credit">
              {formatCurrency(stats.totalCredits)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Balance General</div>
            <div className="stat-value" style={{ 
              color: stats.balance >= 0 ? 'var(--success)' : 'var(--danger)' 
            }}>
              {formatCurrency(stats.balance)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Transacciones</div>
            <div className="stat-value">{stats.count}</div>
          </div>
        </div>

        {/* Navegación por Tabs */}
        <div className="tabs">
          <button 
            className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
            onClick={() => setActiveTab('transactions')}
          >
            📊 Libro Diario
          </button>
          <button 
            className={`tab-button ${activeTab === 'new' ? 'active' : ''}`}
            onClick={() => setActiveTab('new')}
          >
            ➕ Partida Doble
          </button>
          <button 
            className={`tab-button ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            📈 Reportes Excel
          </button>
        </div>

        {/* TAB 1: LIBRO DIARIO */}
        {activeTab === 'transactions' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📊 Libro Diario - Partida Doble</h2>
              <span className="badge">{transactions.length} asientos</span>
            </div>
            
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Comprobante</th>
                    <th>Concepto</th>
                    <th>Cuenta</th>
                    <th>Tercero</th>
                    <th>Débito</th>
                    <th>Crédito</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="empty-state">
                        <div style={{textAlign: 'center', padding: '40px', color: 'var(--text-secondary)'}}>
                          <div style={{fontSize: '48px', marginBottom: '16px'}}>📭</div>
                          <p>No hay transacciones registradas</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    transactions.flatMap(transaction => 
                      transaction.movements && Array.isArray(transaction.movements) 
                        ? transaction.movements.map((movement, index) => (
                            <tr key={`${transaction.id}-${index}`}>
                              <td>{formatDate(transaction.date)}</td>
                              <td style={{fontFamily: 'monospace', fontSize: '12px'}}>
                                {transaction.number || 'N/A'}
                              </td>
                              <td>
                                {transaction.concept}
                                {index === 0 && transaction.movements.length > 1 && (
                                  <div style={{fontSize: '11px', color: 'var(--text-secondary)'}}>
                                    ({transaction.movements.length} movimientos)
                                  </div>
                                )}
                              </td>
                              <td>
                                {accounts.find(a => a.id === movement.account)?.name || '-'}
                              </td>
                              <td>
                                {thirdParties.find(tp => tp.id === movement.third_party)?.name || '-'}
                              </td>
                              <td className="amount-debit">
                                {movement.debit > 0 ? formatCurrency(movement.debit) : '-'}
                              </td>
                              <td className="amount-credit">
                                {movement.credit > 0 ? formatCurrency(movement.credit) : '-'}
                              </td>
                            </tr>
                          ))
                        : []
                    )
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: NUEVA TRANSACCIÓN PARTIDA DOBLE */}
        {activeTab === 'new' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">➕ Sistema de Partida Doble</h2>
              <div className="balance-status" style={{
                padding: '8px 16px',
                background: balanceStatus.isBalanced ? 'var(--success-light)' : 'var(--danger-light)',
                color: balanceStatus.isBalanced ? 'var(--success)' : 'var(--danger)',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 'bold'
              }}>
                {balanceStatus.isBalanced ? '✅ BALANCEADO' : `⚖️ DESBALANCEADO: $${balanceStatus.difference.toFixed(2)}`}
              </div>
            </div>
            
            <form onSubmit={handleSubmitTransaction}>
              {/* Datos generales de la transacción */}
              <div className="form-grid" style={{marginBottom: '20px'}}>
                <div className="form-group">
                  <label>Empresa *</label>
                  <select 
                    className="form-control"
                    value={transactionForm.company}
                    onChange={(e) => setTransactionForm({...transactionForm, company: e.target.value})}
                    required
                  >
                    <option value="">Seleccionar empresa...</option>
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>
                        {company.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Fecha *</label>
                  <input
                    type="date"
                    className="form-control"
                    value={transactionForm.date}
                    onChange={(e) => setTransactionForm({...transactionForm, date: e.target.value})}
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Concepto *</label>
                <input
                  type="text"
                  className="form-control"
                  value={transactionForm.concept}
                  onChange={(e) => setTransactionForm({...transactionForm, concept: e.target.value})}
                  placeholder="Descripción del asiento contable"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Descripción Adicional</label>
                <textarea
                  className="form-control"
                  value={transactionForm.additional_description}
                  onChange={(e) => setTransactionForm({...transactionForm, additional_description: e.target.value})}
                  placeholder="Información adicional del asiento (opcional)"
                  rows="2"
                />
              </div>

              {/* Movimientos - PARTIDA DOBLE */}
              <div style={{marginTop: '30px'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px'}}>
                  <h3 style={{margin: 0}}>📋 Movimientos Contables</h3>
                  <button type="button" onClick={addMovement} className="btn btn-secondary" style={{fontSize: '14px'}}>
                    ➕ Agregar Movimiento
                  </button>
                </div>

                {transactionForm.movements.map((movement, index) => (
                  <div key={index} className="movement-row" style={{
                    padding: '16px',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    marginBottom: '12px',
                    background: 'var(--bg-main)'
                  }}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px'}}>
                      <h4 style={{margin: 0, fontSize: '14px', color: 'var(--text-secondary)'}}>
                        Movimiento #{index + 1}
                      </h4>
                      {transactionForm.movements.length > 2 && (
                        <button 
                          type="button" 
                          onClick={() => removeMovement(index)}
                          className="btn btn-danger"
                          style={{padding: '4px 8px', fontSize: '12px'}}
                        >
                          🗑️ Eliminar
                        </button>
                      )}
                    </div>

                    <div className="form-grid">
                      <div className="form-group">
                        <label>Cuenta Contable *</label>
                        <select 
                          className="form-control"
                          value={movement.account}
                          onChange={(e) => handleMovementChange(index, 'account', e.target.value)}
                          required
                        >
                          <option value="">Seleccionar cuenta...</option>
                          {accounts.map(account => (
                            <option key={account.id} value={account.id}>
                              {account.code} - {account.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className="form-group">
                        <label>Tercero *</label>
                        <select 
                          className="form-control"
                          value={movement.third_party}
                          onChange={(e) => handleMovementChange(index, 'third_party', e.target.value)}
                          required
                        >
                          <option value="">Seleccionar tercero...</option>
                          {thirdParties.map(thirdParty => (
                            <option key={thirdParty.id} value={thirdParty.id}>
                              {thirdParty.name} - NIT: {thirdParty.nit}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className="form-group">
                        <label>Débito</label>
                        <input
                          type="number"
                          className="form-control"
                          value={movement.debit}
                          onChange={(e) => handleMovementChange(index, 'debit', e.target.value)}
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          style={{borderColor: movement.debit > 0 ? 'var(--success)' : ''}}
                        />
                      </div>
                      
                      <div className="form-group">
                        <label>Crédito</label>
                        <input
                          type="number"
                          className="form-control"
                          value={movement.credit}
                          onChange={(e) => handleMovementChange(index, 'credit', e.target.value)}
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          style={{borderColor: movement.credit > 0 ? 'var(--danger)' : ''}}
                        />
                      </div>
                    </div>
                    
                    <div className="form-group">
                      <label>Descripción del Movimiento</label>
                      <input
                        type="text"
                        className="form-control"
                        value={movement.description}
                        onChange={(e) => handleMovementChange(index, 'description', e.target.value)}
                        placeholder="Detalle específico de este movimiento"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Resumen y validación */}
              <div style={{
                padding: '16px',
                background: 'var(--bg-secondary)',
                borderRadius: '8px',
                marginTop: '20px',
                border: `2px solid ${balanceStatus.isBalanced ? 'var(--success)' : 'var(--danger)'}`
              }}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div>
                    <strong>Resumen del Asiento:</strong>
                    <div style={{fontSize: '14px', color: 'var(--text-secondary)'}}>
                      Débito Total: <span className="amount-debit">{formatCurrency(balanceStatus.totalDebit)}</span> | 
                      Crédito Total: <span className="amount-credit">{formatCurrency(balanceStatus.totalCredit)}</span>
                    </div>
                  </div>
                  <div style={{
                    color: balanceStatus.isBalanced ? 'var(--success)' : 'var(--danger)',
                    fontWeight: 'bold'
                  }}>
                    {balanceStatus.isBalanced ? '✅ LISTO PARA GUARDAR' : '❌ CORRIJA EL BALANCE'}
                  </div>
                </div>
              </div>
              
              <div style={{display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px'}}>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setActiveTab('transactions')}
                >
                  ↩ Cancelar
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={loading || !balanceStatus.isBalanced}
                >
                  {loading ? <span className="loading"></span> : '💾'}
                  {loading ? 'Guardando...' : 'Guardar Asiento Contable'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 3: REPORTES (igual que antes) */}
        {activeTab === 'reports' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📈 Generar Reporte Excel</h2>
            </div>
            
            <div className="form-grid">
              <div className="form-group">
                <label>Empresa *</label>
                <select 
                  className="form-control"
                  value={reportForm.company}
                  onChange={(e) => setReportForm({...reportForm, company: e.target.value})}
                >
                  <option value="">Seleccionar empresa...</option>
                  {companies.map(company => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Año</label>
                <input
                  type="number"
                  className="form-control"
                  value={reportForm.year}
                  onChange={(e) => setReportForm({...reportForm, year: parseInt(e.target.value)})}
                  min="2020"
                  max="2030"
                />
              </div>
              
              <div className="form-group">
                <label>Mes</label>
                <select 
                  className="form-control"
                  value={reportForm.month}
                  onChange={(e) => setReportForm({...reportForm, month: parseInt(e.target.value)})}
                >
                  <option value="1">Enero</option>
                  <option value="2">Febrero</option>
                  <option value="3">Marzo</option>
                  <option value="4">Abril</option>
                  <option value="5">Mayo</option>
                  <option value="6">Junio</option>
                  <option value="7">Julio</option>
                  <option value="8">Agosto</option>
                  <option value="9">Septiembre</option>
                  <option value="10">Octubre</option>
                  <option value="11">Noviembre</option>
                  <option value="12">Diciembre</option>
                </select>
              </div>
            </div>
            
            <div style={{marginTop: '30px'}}>
              <button 
                onClick={handleDownloadReport} 
                className="btn btn-success"
                disabled={!reportForm.company}
              >
                📥 Descargar Libro Diario (Excel)
              </button>
              
              <div style={{marginTop: '20px', padding: '16px', background: 'var(--bg-main)', borderRadius: '8px'}}>
                <p style={{color: 'var(--text-secondary)', fontSize: '14px', margin: 0}}>
                  <strong>📋 Información del Reporte:</strong> El sistema generará un Libro Diario completo 
                  con todos los movimientos de partida doble para el período seleccionado. 
                  Incluye validación de balance y formato profesional.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;