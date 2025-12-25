// components/dashboard/Dashboard.js
/**
 * Dashboard con estadísticas
 */

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Users,
  Calendar,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

const StatCard = ({ title, value, icon: Icon, trend, trendValue, color = 'blue' }) => {
  const colors = {
    blue: { bg: '#dbeafe', text: '#1d4ed8', icon: '#3b82f6' },
    green: { bg: '#dcfce7', text: '#15803d', icon: '#10b981' },
    red: { bg: '#fee2e2', text: '#b91c1c', icon: '#ef4444' },
    purple: { bg: '#f3e8ff', text: '#7c3aed', icon: '#8b5cf6' },
    yellow: { bg: '#fef3c7', text: '#b45309', icon: '#f59e0b' },
  };

  const colorScheme = colors[color] || colors.blue;

  return (
    <div className="stat-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="stat-label">{title}</div>
          <div className="stat-value">{value}</div>
          {trend !== undefined && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              marginTop: '8px',
              fontSize: '13px',
              color: trend >= 0 ? '#10b981' : '#ef4444',
            }}>
              {trend >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              <span>{Math.abs(trend)}% {trendValue || 'vs mes anterior'}</span>
            </div>
          )}
        </div>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          background: colorScheme.bg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Icon size={24} color={colorScheme.icon} />
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { dashboardStats, loading, transactions } = useApp();

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  // Calcular estadísticas básicas si no hay datos del API
  const stats = dashboardStats || {
    total_transactions: transactions?.length || 0,
    total_debit: transactions?.reduce((sum, t) =>
      sum + (t.movements?.reduce((s, m) => s + parseFloat(m.debit || 0), 0) || 0), 0) || 0,
    total_credit: transactions?.reduce((sum, t) =>
      sum + (t.movements?.reduce((s, m) => s + parseFloat(m.credit || 0), 0) || 0), 0) || 0,
    unique_third_parties: new Set(
      transactions?.flatMap(t => t.movements?.map(m => m.third_party) || []) || []
    ).size,
  };

  if (loading) {
    return (
      <div className="stats-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card" style={{ opacity: 0.5 }}>
            <div className="stat-label">Cargando...</div>
            <div className="stat-value">---</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="stats-grid">
        <StatCard
          title="Total Transacciones"
          value={stats.total_transactions || 0}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Total Débitos"
          value={formatCurrency(stats.total_debit)}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Total Créditos"
          value={formatCurrency(stats.total_credit)}
          icon={TrendingDown}
          color="red"
        />
        <StatCard
          title="Terceros Únicos"
          value={stats.unique_third_parties || 0}
          icon={Users}
          color="purple"
        />
      </div>

      {/* Resumen del mes */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <h2 className="card-title">
            <Calendar size={20} />
            Resumen del Período
          </h2>
        </div>
        <div style={{ padding: '20px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '20px',
          }}>
            <div>
              <div style={{ color: '#64748b', fontSize: '14px', marginBottom: '5px' }}>
                Balance General
              </div>
              <div style={{
                fontSize: '24px',
                fontWeight: '700',
                color: (stats.total_debit - stats.total_credit) >= 0 ? '#10b981' : '#ef4444',
              }}>
                {formatCurrency(Math.abs(stats.total_debit - stats.total_credit))}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                {(stats.total_debit - stats.total_credit) >= 0 ? 'Saldo a favor' : 'Saldo en contra'}
              </div>
            </div>

            <div>
              <div style={{ color: '#64748b', fontSize: '14px', marginBottom: '5px' }}>
                Promedio por Transacción
              </div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#1e293b' }}>
                {formatCurrency(
                  stats.total_transactions > 0
                    ? stats.total_debit / stats.total_transactions
                    : 0
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>
                En débitos
              </div>
            </div>

            <div>
              <div style={{ color: '#64748b', fontSize: '14px', marginBottom: '5px' }}>
                Estado
              </div>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '20px',
                background: Math.abs(stats.total_debit - stats.total_credit) < 1 ? '#dcfce7' : '#fef3c7',
                color: Math.abs(stats.total_debit - stats.total_credit) < 1 ? '#15803d' : '#b45309',
                fontWeight: '500',
              }}>
                <DollarSign size={16} />
                {Math.abs(stats.total_debit - stats.total_credit) < 1
                  ? 'Balanceado'
                  : 'Revisar diferencias'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
