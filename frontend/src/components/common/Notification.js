// components/common/Notification.js
/**
 * Componente de notificaciones
 */

import React from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

const iconMap = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const Notification = ({ notification, onClose }) => {
  if (!notification) return null;

  const { message, type = 'info' } = notification;
  const Icon = iconMap[type] || Info;

  return (
    <div className={`notification ${type}`}>
      <Icon size={20} />
      <span>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="notification-close"
          aria-label="Cerrar notificación"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};

export default Notification;
