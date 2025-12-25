// components/common/SearchableSelect.js
/**
 * Componente de selección con búsqueda
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, X, Search } from 'lucide-react';

const SearchableSelect = ({
  options = [],
  value,
  onChange,
  placeholder = 'Seleccionar...',
  searchPlaceholder = 'Buscar...',
  displayField = 'name',
  valueField = 'id',
  secondaryField = null,
  renderOption = null,
  disabled = false,
  error = null,
  label = null,
  required = false,
  className = '',
  emptyMessage = 'No se encontraron resultados',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Encontrar opción seleccionada
  const selectedOption = options.find((opt) => opt[valueField] === value);

  // Filtrar opciones por término de búsqueda
  const filteredOptions = options.filter((option) => {
    const searchLower = searchTerm.toLowerCase();
    const primaryMatch = String(option[displayField] || '')
      .toLowerCase()
      .includes(searchLower);
    const secondaryMatch = secondaryField
      ? String(option[secondaryField] || '').toLowerCase().includes(searchLower)
      : false;
    return primaryMatch || secondaryMatch;
  });

  // Cerrar al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus en el input cuando se abre
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Resetear highlighted index cuando cambia la búsqueda
  useEffect(() => {
    setHighlightedIndex(0);
  }, [searchTerm]);

  // Scroll al elemento highlighted
  useEffect(() => {
    if (isOpen && listRef.current && filteredOptions.length > 0) {
      const highlightedElement = listRef.current.children[highlightedIndex];
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen, filteredOptions.length]);

  const handleSelect = useCallback(
    (option) => {
      onChange(option[valueField]);
      setIsOpen(false);
      setSearchTerm('');
    },
    [onChange, valueField]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (!isOpen) {
        if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
          e.preventDefault();
          setIsOpen(true);
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < filteredOptions.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredOptions[highlightedIndex]) {
            handleSelect(filteredOptions[highlightedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          setSearchTerm('');
          break;
        default:
          break;
      }
    },
    [isOpen, filteredOptions, highlightedIndex, handleSelect]
  );

  const handleClear = (e) => {
    e.stopPropagation();
    onChange(null);
    setSearchTerm('');
  };

  const renderDefaultOption = (option, isHighlighted) => (
    <div className={`searchable-select-option ${isHighlighted ? 'searchable-select-option-highlight' : ''}`}>
      <div className="searchable-select-option-name">{option[displayField]}</div>
      {secondaryField && option[secondaryField] && (
        <div className="searchable-select-option-nit">{option[secondaryField]}</div>
      )}
    </div>
  );

  return (
    <div className={`searchable-select ${className}`} ref={containerRef}>
      {label && (
        <label className="form-group-label">
          {label}
          {required && <span className="required-indicator">*</span>}
        </label>
      )}

      <div
        className={`searchable-select-trigger ${disabled ? 'disabled' : ''} ${error ? 'error' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className={`searchable-select-value ${!selectedOption ? 'placeholder' : ''}`}>
          {selectedOption ? selectedOption[displayField] : placeholder}
        </span>

        <div className="searchable-select-icons">
          {selectedOption && !disabled && (
            <button
              type="button"
              className="searchable-select-clear"
              onClick={handleClear}
              tabIndex={-1}
            >
              <X size={14} />
            </button>
          )}
          <ChevronDown size={16} className={`searchable-select-chevron ${isOpen ? 'open' : ''}`} />
        </div>
      </div>

      {isOpen && (
        <div className="searchable-select-dropdown">
          <div className="searchable-select-search">
            <Search size={16} />
            <input
              ref={inputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={searchPlaceholder}
              className="searchable-select-input"
            />
          </div>

          {filteredOptions.length > 0 && (
            <div className="searchable-select-count">
              {filteredOptions.length} de {options.length} resultados
            </div>
          )}

          <div className="searchable-select-options" ref={listRef} role="listbox">
            {filteredOptions.length === 0 ? (
              <div className="searchable-select-empty">{emptyMessage}</div>
            ) : (
              filteredOptions.map((option, index) => (
                <div
                  key={option[valueField]}
                  onClick={() => handleSelect(option)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  role="option"
                  aria-selected={option[valueField] === value}
                >
                  {renderOption
                    ? renderOption(option, index === highlightedIndex)
                    : renderDefaultOption(option, index === highlightedIndex)}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {error && <span className="form-error">{error}</span>}
    </div>
  );
};

// Componente específico para cuentas contables
export const AccountSelect = ({ accounts = [], value, onChange, ...props }) => {
  return (
    <SearchableSelect
      options={accounts}
      value={value}
      onChange={onChange}
      displayField="name"
      secondaryField="code"
      valueField="id"
      placeholder="Buscar cuenta..."
      searchPlaceholder="Código o nombre..."
      renderOption={(option, isHighlighted) => (
        <div className={`searchable-select-option ${isHighlighted ? 'searchable-select-option-highlight' : ''}`}>
          <div className="searchable-select-option-code">{option.code}</div>
          <div className="searchable-select-option-name">{option.name}</div>
        </div>
      )}
      {...props}
    />
  );
};

// Componente específico para terceros
export const ThirdPartySelect = ({ thirdParties = [], value, onChange, ...props }) => {
  return (
    <SearchableSelect
      options={thirdParties}
      value={value}
      onChange={onChange}
      displayField="name"
      secondaryField="nit"
      valueField="id"
      placeholder="Buscar tercero..."
      searchPlaceholder="Nombre o NIT..."
      renderOption={(option, isHighlighted) => (
        <div className={`searchable-select-option ${isHighlighted ? 'searchable-select-option-highlight' : ''}`}>
          <div className="searchable-select-option-name">{option.name}</div>
          <div className="searchable-select-option-nit">NIT: {option.nit}</div>
        </div>
      )}
      {...props}
    />
  );
};

export default SearchableSelect;
