import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [form, setForm] = useState({
    company: 1,
    date: '',
    account: 1,
    third_party: 1,
    concept: '',
    debit: 0,
    credit: 0
  });
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  useEffect(() => {
    if (token) {
      axios.get('/api/transactions/', {
        headers: { Authorization: `Token ${token}` }
      })
      .then(response => setTransactions(response.data))
      .catch(error => console.error('Error fetching transactions:', error));
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
    // This endpoint needs to be created in the backend to handle POST requests.
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
        <input type="date" name="date" value={form.date} onChange={handleChange} required />
        <input type="text" name="concept" placeholder="Concept" value={form.concept} onChange={handleChange} required />
        <input type="number" name="debit" placeholder="Debit" value={form.debit} onChange={handleChange} />
        <input type="number" name="credit" placeholder="Credit" value={form.credit} onChange={handleChange} />
        <button type="submit">Add</button>
      </form>
    </div>
  );
}

export default App;
