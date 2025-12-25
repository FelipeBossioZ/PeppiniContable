// components/common/Loading.js
/**
 * Componente de carga
 */

import React from 'react';
import { Loader2 } from 'lucide-react';

const Loading = ({ size = 'medium', text = 'Cargando...', fullScreen = false }) => {
  const sizeMap = {
    small: 16,
    medium: 24,
    large: 48,
  };

  const iconSize = sizeMap[size] || sizeMap.medium;

  if (fullScreen) {
    return (
      <div className="loading-overlay">
        <div className="loading-content">
          <Loader2 size={iconSize} className="loading-spinner" />
          {text && <span className="loading-text">{text}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="loading-container">
      <Loader2 size={iconSize} className="loading-spinner" />
      {text && <span className="loading-text">{text}</span>}
    </div>
  );
};

export default Loading;
