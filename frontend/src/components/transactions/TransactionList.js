// components/transactions/TransactionList.js
/**
 * Lista de transacciones
 */

import React, { useState } from 'react';
import {
  Edit2,
  Trash2,
  Eye,
  ChevronDown,
  ChevronUp,
  FileText,
  Calendar,
  Hash,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

const TransactionRow = ({ transaction, onEdit, onDelete, onView }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateStr) => {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  const totalDebit = transaction.movements?.reduce((sum, m) => sum + parseFloat(m.debit || 0), 0) || 0;
  const totalCredit = transaction.movements?.reduce((sum, m) => sum + parseFloat(m.credit || 0), 0) || 0;

  return (
    <>
      <tr className={transaction.is_deleted ? 'deleted-row' : ''}>
        <td>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn-glass-edit"
            style={{ padding: '6px' }}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </td>
        <td>
          <span style={{ fontWeight: '600', color: '#3b82f6' }}>{transaction.number}</span>
        </td>
        <td>{formatDate(transaction.date)}</td>
        <td>
          <div style={{ maxWidth: '300px' }}>
            <div style={{ fontWeight: '500' }}>{transaction.concept}</div>
            {transaction.additional_description && (
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                {transaction.additional_description.substring(0, 50)}
                {transaction.additional_description.length > 50 && '...'}
              </div>
            )}
          </div>
        </td>
        <td className="amount-debit" style={{ textAlign: 'right' }}>
          ${formatNumber(totalDebit)}
        </td>
        <td className="amount-credit" style={{ textAlign: 'right' }}>
          ${formatNumber(totalCredit)}
        </td>
        <td>
          <span
            style={{
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: '500',
              background: transaction.movements?.length > 2 ? '#dbeafe' : '#e2e8f0',
              color: transaction.movements?.length > 2 ? '#1d4ed8' : '#475569',
            }}
          >
            {transaction.movements?.length || 0} mov.
          </span>
        </td>
        <td>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => onView?.(transaction)}
              className="btn-glass-edit"
              title="Ver detalles"
            >
              <Eye size={16} />
            </button>
            <button
              onClick={() => onEdit?.(transaction)}
              className="btn-glass-edit"
              title="Editar"
              disabled={transaction.is_deleted}
            >
              <Edit2 size={16} />
            </button>
            <button
              onClick={() => onDelete?.(transaction)}
              className="btn-glass-delete"
              title="Eliminar"
              disabled={transaction.is_deleted}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </td>
      </tr>

      {/* Movimientos expandidos */}
      {isExpanded && (
        <tr className="expanded-row">
          <td colSpan={8} style={{ padding: '0', background: '#f8fafc' }}>
            <div style={{ padding: '15px 20px' }}>
              <table style={{ width: '100%', minWidth: 'auto' }}>
                <thead>
                  <tr style={{ background: '#e2e8f0' }}>
                    <th style={{ padding: '8px 12px' }}>Cuenta</th>
                    <th style={{ padding: '8px 12px' }}>Tercero</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>Débito</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>Crédito</th>
                    <th style={{ padding: '8px 12px' }}>Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {transaction.movements?.map((mov, idx) => (
                    <tr key={idx}>
                      <td style={{ padding: '8px 12px' }}>
                        <span style={{ fontFamily: 'monospace', fontWeight: '600' }}>
                          {mov.account_code}
                        </span>
                        {' - '}
                        {mov.account_name}
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        {mov.third_party_name}
                        <span style={{ color: '#64748b', fontSize: '12px', marginLeft: '5px' }}>
                          ({mov.third_party_nit})
                        </span>
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }} className="amount-debit">
                        {parseFloat(mov.debit) > 0 ? `$${formatNumber(mov.debit)}` : '-'}
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }} className="amount-credit">
                        {parseFloat(mov.credit) > 0 ? `$${formatNumber(mov.credit)}` : '-'}
                      </td>
                      <td style={{ padding: '8px 12px', color: '#64748b' }}>
                        {mov.description || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

const TransactionList = ({ onEdit, onView }) => {
  const { transactions, loading, deleteTransaction, pagination, loadTransactions } = useApp();
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleDelete = async (transaction) => {
    if (deleteConfirm === transaction.id) {
      await deleteTransaction(transaction.id);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(transaction.id);
      // Auto-cerrar después de 3 segundos
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">
          <span className="loading" style={{ width: '40px', height: '40px' }}></span>
          <p>Cargando transacciones...</p>
        </div>
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card">
        <div className="empty-state">
          <FileText size={64} className="empty-state-icon" />
          <h3>No hay transacciones</h3>
          <p>Crea tu primer asiento contable para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">
          <FileText size={20} />
          Transacciones
        </h2>
        <span className="badge">{pagination.totalCount} registros</span>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th>
                <Hash size={14} style={{ marginRight: '5px' }} />
                Número
              </th>
              <th>
                <Calendar size={14} style={{ marginRight: '5px' }} />
                Fecha
              </th>
              <th>Concepto</th>
              <th style={{ textAlign: 'right' }}>Débito</th>
              <th style={{ textAlign: 'right' }}>Crédito</th>
              <th>Movimientos</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((transaction) => (
              <TransactionRow
                key={transaction.id}
                transaction={transaction}
                onEdit={onEdit}
                onDelete={handleDelete}
                onView={onView}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {pagination.totalPages > 1 && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '10px',
          padding: '20px',
          borderTop: '1px solid #e2e8f0',
        }}>
          <button
            onClick={() => loadTransactions({ page: pagination.page - 1 })}
            disabled={pagination.page <= 1}
            className="btn btn-secondary"
          >
            Anterior
          </button>
          <span style={{ color: '#64748b' }}>
            Página {pagination.page} de {pagination.totalPages}
          </span>
          <button
            onClick={() => loadTransactions({ page: pagination.page + 1 })}
            disabled={pagination.page >= pagination.totalPages}
            className="btn btn-secondary"
          >
            Siguiente
          </button>
        </div>
      )}

      {/* Modal de confirmación de eliminación */}
      {deleteConfirm && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#ef4444',
          color: 'white',
          padding: '15px 25px',
          borderRadius: '10px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '15px',
        }}>
          <span>¿Confirmar eliminación? Haz clic de nuevo para eliminar</span>
          <button
            onClick={() => setDeleteConfirm(null)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              padding: '5px 10px',
              borderRadius: '5px',
              color: 'white',
              cursor: 'pointer',
            }}
          >
            Cancelar
          </button>
        </div>
      )}
    </div>
  );
};

export default TransactionList;
