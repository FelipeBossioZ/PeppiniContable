// components/layout/Navigation.js
/**
 * Componente de navegación por pestañas
 */

import React from 'react';
import {
  FileText,
  PlusCircle,
  BarChart3,
  Settings,
  Brain,
  Download
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

const tabs = [
  { id: 'transactions', label: 'Transacciones', icon: FileText },
  { id: 'new', label: 'Nuevo Asiento', icon: PlusCircle },
  { id: 'reports', label: 'Reportes', icon: BarChart3 },
  { id: 'rules', label: 'Reglas IA', icon: Brain },
  { id: 'export', label: 'Exportar', icon: Download },
  { id: 'settings', label: 'Configuración', icon: Settings },
];

const Navigation = () => {
  const { activeTab, setActiveTab } = useApp();

  return (
    <div className="tabs">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon size={18} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default Navigation;
