import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [thirdParties, setThirdParties] = useState([]);
  const [form, setForm] = useState({
    company: '',
    date: '',
    account: '',
    third_party: '',
    concept: '',
    debit: 0,
    credit: 0
  });
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  useEffect(() => {
    if (token) {
      const headers = { Authorization: `Token ${token}` };
      axios.get('/api/transactions/', { headers })
        .then(response => setTransactions(response.data))
        .catch(error => console.error('Error fetching transactions:', error));
      axios.get('/api/companies/', { headers })
        .then(response => setCompanies(response.data))
        .catch(error => console.error('Error fetching companies:', error));
      axios.get('/api/accounts/', { headers })
        .then(response => setAccounts(response.data))
        .catch(error => console.error('Error fetching accounts:', error));
      axios.get('/api/third-parties/', { headers })
        .then(response => setThirdParties(response.data))
        .catch(error => console.error('Error fetching third parties:', error));
    }
  }, [token]);

  const handleLoginChange = (e) => {
    setLoginForm({
      ...loginForm,
      [e.target.name]: e.target.value
    });
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    axios.post('/api-token-auth/', loginForm)
      .then(response => {
        const newToken = response.data.token;
        setToken(newToken);
        localStorage.setItem('token', newToken);
      })
      .catch(error => console.error('Login failed:', error));
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
  };

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/transactions/', form, {
        headers: { Authorization: `Token ${token}` }
    })
      .then(response => {
        setTransactions([...transactions, response.data]);
      })
      .catch(error => console.error('Error creating transaction:', error));
  };

  if (!token) {
      return (
          <div className="App">
              <h1>Login</h1>
              <form onSubmit={handleLoginSubmit}>
                  <input type="text" name="username" placeholder="Username" value={loginForm.username} onChange={handleLoginChange} required />
                  <input type="password" name="password" placeholder="Password" value={loginForm.password} onChange={handleLoginChange} required />
                  <button type="submit">Login</button>
              </form>
          </div>
      );
  }

  return (
    <div className="App">
      <h1>Accounting System</h1>
      <button onClick={handleLogout}>Logout</button>

      <h2>Transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Concept</th>
            <th>Debit</th>
            <th>Credit</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(t => (
            <tr key={t.id}>
              <td>{t.date}</td>
              <td>{t.concept}</td>
              <td>{t.debit}</td>
              <td>{t.credit}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Add Transaction</h2>
      <form onSubmit={handleSubmit}>
        <select name="company" value={form.company} onChange={handleChange} required>
          <option value="">Select Company</option>
          {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input type="date" name="date" value={form.date} onChange={handleChange} required />
        <select name="account" value={form.account} onChange={handleChange} required>
          <option value="">Select Account</option>
          {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <select name="third_party" value={form.third_party} onChange={handleChange} required>
            <option value="">Select Third Party</option>
            {thirdParties.map(tp => <option key={tp.id} value={tp.id}>{tp.name}</option>)}
        </select>
        <input type="text" name="concept" placeholder="Concept" value={form.concept} onChange={handleChange} required />
        <input type="number" name="debit" placeholder="Debit" value={form.debit} onChange={handleChange} />
        <input type="number" name="credit" placeholder="Credit" value={form.credit} onChange={handleChange} />
        <button type="submit">Add</button>
      </form>
    </div>
  );
}

export default App;
