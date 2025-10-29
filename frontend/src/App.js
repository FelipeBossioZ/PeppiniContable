// App.js - 
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
  
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [form, setForm] = useState({
    company: '',
    date: new Date().toISOString().split('T')[0],
    account: '',
    third_party: '',
    concept: '',
    additional_description: '',
    debit: 0,
    credit: 0
  });
  
  const [reportForm, setReportForm] = useState({
    company: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1
  });

  
  // Sistema de notificaciones
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Cargar datos cuando hay token
  useEffect(() => {
  if (token) {
    fetchAllData();
  }
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

    // IMPORTANTE: Asegúrate de que siempre sean arrays
    setTransactions(Array.isArray(transRes.data.results) ? transRes.data.results : 
                    Array.isArray(transRes.data) ? transRes.data : []);
    setCompanies(Array.isArray(compRes.data) ? compRes.data : []);
    setAccounts(Array.isArray(accRes.data) ? accRes.data : []);
    setThirdParties(Array.isArray(thirdRes.data) ? thirdRes.data : []);

    // ...resto del código
  } catch (error) {
    console.error('Error cargando datos:', error);
    showNotification('Error al cargar datos', 'error');
  } finally {
    setLoading(false);
  }
};

  // ========== MANEJO DE LOGIN ==========
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
      console.error('Login failed:', error);
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

  // ========== MANEJO DE TRANSACCIONES ==========
  const handleSubmitTransaction = async (e) => {
    e.preventDefault();
    setLoading(true);

     const headers = { 
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  };
    
    try {
      const response = await axios.post('/api/transactions/', form, { headers: headers });
      
      setTransactions(prev => [response.data, ...prev]);
      showNotification('Transacción creada exitosamente', 'success');
      
      // Resetear formulario
      setForm({
        ...form,
        concept: '',
        additional_description: '',
        debit: 0,
        credit: 0
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
  // Protección: asegurarse de que transactions es un array
  if (!Array.isArray(transactions)) {
    return { 
      totalDebits: 0, 
      totalCredits: 0, 
      balance: 0, 
      count: 0 
    };
  }
  
  const totalDebits = transactions.reduce((sum, t) => sum + parseFloat(t.debit || 0), 0);
  const totalCredits = transactions.reduce((sum, t) => sum + parseFloat(t.credit || 0), 0);
  const balance = totalDebits - totalCredits;
  
  return { 
    totalDebits, 
    totalCredits, 
    balance, 
    count: transactions.length 
  };
};

  const stats = calculateStats();

  // ========== RENDERIZADO ==========
  

  
  // Si no hay token, mostrar login
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

      {/* Header */}
      <div className="header">
        <div className="header-content">
          <div className="header-title">
            <div className="header-logo">TD</div>
            <h1>Sistema de Transacciones Diarias</h1>
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
            📊 Transacciones
          </button>
          <button 
            className={`tab-button ${activeTab === 'new' ? 'active' : ''}`}
            onClick={() => setActiveTab('new')}
          >
            ➕ Nueva Transacción
          </button>
          <button 
            className={`tab-button ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            📈 Reportes Excel
          </button>
        </div>

        {/* Contenido de Tabs */}
        {activeTab === 'transactions' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📊 Transacciones Recientes</h2>
              <span className="badge">{transactions.length} registros</span>
            </div>
            
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Empresa</th>
                    <th>Cuenta</th>
                    <th>Tercero</th>
                    <th>Concepto</th>
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
                    transactions.slice(0, 50).map((transaction) => (
                      <tr key={transaction.id}>
                        <td>{formatDate(transaction.date)}</td>
                        <td>
                          {companies.find(c => c.id === transaction.company)?.name || '-'}
                        </td>
                        <td>
                          {accounts.find(a => a.id === transaction.account)?.name || '-'}
                        </td>
                        <td>
                          {thirdParties.find(tp => tp.id === transaction.third_party)?.name || '-'}
                        </td>
                        <td>{transaction.concept}</td>
                        <td className="amount-debit">
                          {transaction.debit > 0 ? formatCurrency(transaction.debit) : '-'}
                        </td>
                        <td className="amount-credit">
                          {transaction.credit > 0 ? formatCurrency(transaction.credit) : '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'new' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">➕ Registrar Nueva Transacción</h2>
            </div>
            
            <form onSubmit={handleSubmitTransaction}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Empresa *</label>
                  <select 
                    className="form-control"
                    name="company"
                    value={form.company}
                    onChange={(e) => setForm({...form, company: e.target.value})}
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
                    name="date"
                    value={form.date}
                    onChange={(e) => setForm({...form, date: e.target.value})}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Cuenta Contable *</label>
                  <select 
                    className="form-control"
                    name="account"
                    value={form.account}
                    onChange={(e) => setForm({...form, account: e.target.value})}
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
                    name="third_party"
                    value={form.third_party}
                    onChange={(e) => setForm({...form, third_party: e.target.value})}
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
                    name="debit"
                    value={form.debit}
                    onChange={(e) => setForm({...form, debit: parseFloat(e.target.value) || 0})}
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                  />
                </div>
                
                <div className="form-group">
                  <label>Crédito</label>
                  <input
                    type="number"
                    className="form-control"
                    name="credit"
                    value={form.credit}
                    onChange={(e) => setForm({...form, credit: parseFloat(e.target.value) || 0})}
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Concepto *</label>
                <input
                  type="text"
                  className="form-control"
                  name="concept"
                  value={form.concept}
                  onChange={(e) => setForm({...form, concept: e.target.value})}
                  placeholder="Descripción del concepto contable"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Descripción Adicional</label>
                <textarea
                  className="form-control"
                  name="additional_description"
                  value={form.additional_description}
                  onChange={(e) => setForm({...form, additional_description: e.target.value})}
                  placeholder="Información adicional de la transacción (opcional)"
                  rows="3"
                />
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
                  disabled={loading}
                >
                  {loading ? <span className="loading"></span> : '💾'}
                  {loading ? 'Guardando...' : 'Guardar Transacción'}
                </button>
              </div>
            </form>
          </div>
        )}

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
                📥 Descargar Balance de Prueba (Excel)
              </button>
              
              <div style={{marginTop: '20px', padding: '16px', background: 'var(--bg-main)', borderRadius: '8px'}}>
                <p style={{color: 'var(--text-secondary)', fontSize: '14px', margin: 0}}>
                  <strong>📋 Información del Reporte:</strong> El sistema generará un Balance de Prueba por Tercero 
                  incluyendo saldos anteriores, débitos, créditos y saldo final para el período seleccionado. 
                  El archivo Excel incluirá validaciones y formato profesional.
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