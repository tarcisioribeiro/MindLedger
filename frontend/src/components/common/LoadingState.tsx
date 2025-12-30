/**
 * LoadingState Component
 *
 * Componente reutilizável para estados de carregamento.
 * Exibe spinner padronizado com tamanhos e opções configuráveis.
 */

import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  size = 'md',
  fullScreen = false,
  message,
}) => {
  const sizeClasses = {
    sm: 'h-32',
    md: 'h-64',
    lg: 'h-96',
  };

  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 ${
        fullScreen ? 'h-screen' : sizeClasses[size]
      }`}
    >
      <Loader2 className={`${iconSizes[size]} animate-spin text-primary`} />
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  );
};
