// components/layout/Header.js
/**
 * Componente de cabecera de la aplicación
 */

import React from 'react';
import { LogOut, Building2, User } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const Header = () => {
  const { logout, user, companies, selectedCompany, setSelectedCompany } = useApp();

  const currentCompany = companies.find((c) => c.id === selectedCompany);

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-title">
          <div className="header-logo">P</div>
          <h1>PeppiniContable</h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* Selector de empresa */}
          {companies.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Building2 size={18} />
              <select
                value={selectedCompany || ''}
                onChange={(e) => setSelectedCompany(Number(e.target.value))}
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  color: 'white',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                {companies.map((company) => (
                  <option key={company.id} value={company.id} style={{ color: '#333' }}>
                    {company.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Info de empresa actual */}
          {currentCompany && companies.length === 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8 }}>
              <Building2 size={18} />
              <span>{currentCompany.name}</span>
            </div>
          )}

          {/* Info de usuario */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.8 }}>
              <User size={18} />
              <span>{user.username}</span>
            </div>
          )}

          {/* Botón de logout */}
          <button
            onClick={logout}
            className="btn btn-secondary"
            style={{
              padding: '8px 16px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              color: 'white',
            }}
          >
            <LogOut size={18} />
            Salir
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
