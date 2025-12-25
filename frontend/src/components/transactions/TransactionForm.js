// components/transactions/TransactionForm.js
/**
 * Formulario para crear/editar transacciones
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Plus, Trash2, Save, AlertTriangle, CheckCircle } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AccountSelect, ThirdPartySelect } from '../common/SearchableSelect';

const emptyMovement = {
  account: '',
  third_party: '',
  debit: '',
  credit: '',
  description: '',
};

const TransactionForm = ({ onSuccess, initialData = null }) => {
  const { accounts, thirdParties, selectedCompany, createTransaction, updateTransaction } = useApp();

  const [formData, setFormData] = useState({
    date: initialData?.date || new Date().toISOString().split('T')[0],
    concept: initialData?.concept || '',
    additional_description: initialData?.additional_description || '',
    movements: initialData?.movements?.map((m) => ({
      account: m.account,
      third_party: m.third_party,
      debit: m.debit > 0 ? m.debit.toString() : '',
      credit: m.credit > 0 ? m.credit.toString() : '',
      description: m.description || '',
    })) || [{ ...emptyMovement }, { ...emptyMovement }],
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Calcular totales
  const totals = useMemo(() => {
    const debit = formData.movements.reduce(
      (sum, m) => sum + (parseFloat(m.debit) || 0),
      0
    );
    const credit = formData.movements.reduce(
      (sum, m) => sum + (parseFloat(m.credit) || 0),
      0
    );
    return {
      debit,
      credit,
      difference: Math.abs(debit - credit),
      isBalanced: Math.abs(debit - credit) < 0.01,
    };
  }, [formData.movements]);

  // Agregar movimiento
  const addMovement = useCallback(() => {
    setFormData((prev) => ({
      ...prev,
      movements: [...prev.movements, { ...emptyMovement }],
    }));
  }, []);

  // Eliminar movimiento
  const removeMovement = useCallback((index) => {
    if (formData.movements.length <= 2) return;
    setFormData((prev) => ({
      ...prev,
      movements: prev.movements.filter((_, i) => i !== index),
    }));
  }, [formData.movements.length]);

  // Actualizar movimiento
  const updateMovement = useCallback((index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      movements: prev.movements.map((m, i) => {
        if (i !== index) return m;

        const updated = { ...m, [field]: value };

        // Si se ingresa débito, limpiar crédito y viceversa
        if (field === 'debit' && value) {
          updated.credit = '';
        } else if (field === 'credit' && value) {
          updated.debit = '';
        }

        return updated;
      }),
    }));
  }, []);

  // Validar formulario
  const validate = useCallback(() => {
    const newErrors = {};

    if (!formData.date) {
      newErrors.date = 'La fecha es requerida';
    }

    if (!formData.concept.trim()) {
      newErrors.concept = 'El concepto es requerido';
    }

    // Validar movimientos
    const movementErrors = formData.movements.map((m, i) => {
      const err = {};
      if (!m.account) err.account = 'Cuenta requerida';
      if (!m.third_party) err.third_party = 'Tercero requerido';
      if (!m.debit && !m.credit) err.amount = 'Ingrese débito o crédito';
      return Object.keys(err).length > 0 ? err : null;
    });

    if (movementErrors.some((e) => e !== null)) {
      newErrors.movements = movementErrors;
    }

    if (!totals.isBalanced) {
      newErrors.balance = 'El asiento no está balanceado';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, totals.isBalanced]);

  // Enviar formulario
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      const transactionData = {
        company: selectedCompany,
        date: formData.date,
        concept: formData.concept,
        additional_description: formData.additional_description,
        movements: formData.movements.map((m) => ({
          account: m.account,
          third_party: m.third_party,
          debit: parseFloat(m.debit) || 0,
          credit: parseFloat(m.credit) || 0,
          description: m.description,
        })),
      };

      let result;
      if (initialData?.id) {
        result = await updateTransaction(initialData.id, transactionData);
      } else {
        result = await createTransaction(transactionData);
      }

      if (result.success) {
        // Limpiar formulario si es nuevo
        if (!initialData) {
          setFormData({
            date: new Date().toISOString().split('T')[0],
            concept: '',
            additional_description: '',
            movements: [{ ...emptyMovement }, { ...emptyMovement }],
          });
        }
        onSuccess?.(result.data);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Formatear número con separadores de miles
  const formatNumber = (num) => {
    return new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">
          {initialData ? 'Editar Asiento Contable' : 'Nuevo Asiento Contable'}
        </h2>
        <div className="badge">Partida Doble</div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Campos principales */}
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="date">Fecha *</label>
            <input
              id="date"
              type="date"
              value={formData.date}
              onChange={(e) => setFormData((prev) => ({ ...prev, date: e.target.value }))}
              className={`form-control ${errors.date ? 'error' : ''}`}
            />
            {errors.date && <span className="form-error">{errors.date}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="concept">Concepto *</label>
            <input
              id="concept"
              type="text"
              value={formData.concept}
              onChange={(e) => setFormData((prev) => ({ ...prev, concept: e.target.value }))}
              className={`form-control ${errors.concept ? 'error' : ''}`}
              placeholder="Descripción del asiento"
            />
            {errors.concept && <span className="form-error">{errors.concept}</span>}
          </div>

          <div className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label htmlFor="additional_description">Descripción Adicional</label>
            <textarea
              id="additional_description"
              value={formData.additional_description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, additional_description: e.target.value }))
              }
              className="form-control"
              placeholder="Información adicional del asiento (opcional)"
              rows={2}
            />
          </div>
        </div>

        {/* Movimientos */}
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Movimientos</h3>
            <button
              type="button"
              onClick={addMovement}
              className="btn btn-secondary"
              style={{ padding: '8px 16px' }}
            >
              <Plus size={16} />
              Agregar Línea
            </button>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th style={{ width: '25%' }}>Cuenta</th>
                  <th style={{ width: '20%' }}>Tercero</th>
                  <th style={{ width: '15%' }}>Débito</th>
                  <th style={{ width: '15%' }}>Crédito</th>
                  <th style={{ width: '20%' }}>Descripción</th>
                  <th style={{ width: '5%' }}></th>
                </tr>
              </thead>
              <tbody>
                {formData.movements.map((movement, index) => (
                  <tr key={index}>
                    <td>
                      <AccountSelect
                        accounts={accounts}
                        value={movement.account}
                        onChange={(value) => updateMovement(index, 'account', value)}
                        error={errors.movements?.[index]?.account}
                      />
                    </td>
                    <td>
                      <ThirdPartySelect
                        thirdParties={thirdParties}
                        value={movement.third_party}
                        onChange={(value) => updateMovement(index, 'third_party', value)}
                        error={errors.movements?.[index]?.third_party}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        value={movement.debit}
                        onChange={(e) => updateMovement(index, 'debit', e.target.value)}
                        className="form-control"
                        placeholder="0.00"
                        min="0"
                        step="0.01"
                        style={{ textAlign: 'right' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        value={movement.credit}
                        onChange={(e) => updateMovement(index, 'credit', e.target.value)}
                        className="form-control"
                        placeholder="0.00"
                        min="0"
                        step="0.01"
                        style={{ textAlign: 'right' }}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={movement.description}
                        onChange={(e) => updateMovement(index, 'description', e.target.value)}
                        className="form-control"
                        placeholder="Opcional"
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => removeMovement(index)}
                        className="btn-glass-delete"
                        disabled={formData.movements.length <= 2}
                        title="Eliminar línea"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ fontWeight: 'bold', background: '#f8fafc' }}>
                  <td colSpan={2} style={{ textAlign: 'right' }}>TOTALES:</td>
                  <td style={{ textAlign: 'right' }} className="amount-debit">
                    ${formatNumber(totals.debit)}
                  </td>
                  <td style={{ textAlign: 'right' }} className="amount-credit">
                    ${formatNumber(totals.credit)}
                  </td>
                  <td colSpan={2}></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Estado del balance */}
        <div style={{
          marginTop: '20px',
          padding: '15px',
          borderRadius: '10px',
          background: totals.isBalanced ? '#ecfdf5' : '#fef2f2',
          border: `1px solid ${totals.isBalanced ? '#10b981' : '#ef4444'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {totals.isBalanced ? (
              <CheckCircle size={20} color="#10b981" />
            ) : (
              <AlertTriangle size={20} color="#ef4444" />
            )}
            <span style={{ fontWeight: '600', color: totals.isBalanced ? '#10b981' : '#ef4444' }}>
              {totals.isBalanced
                ? 'Asiento balanceado'
                : `Diferencia: $${formatNumber(totals.difference)}`}
            </span>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting || !totals.isBalanced}
          >
            {isSubmitting ? (
              <>
                <span className="loading"></span>
                Guardando...
              </>
            ) : (
              <>
                <Save size={18} />
                {initialData ? 'Actualizar' : 'Guardar'} Asiento
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TransactionForm;
