/**
 * EmptyState Component
 *
 * Componente reutilizável para estados vazios.
 * Exibe ícone, mensagem e ação opcional quando não há dados.
 */

import React from 'react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, message, action }) => {
  return (
    <div className="bg-card border rounded-xl p-12 text-center space-y-4">
      {icon && (
        <div className="flex justify-center text-muted-foreground opacity-50">
          {icon}
        </div>
      )}
      {title && <h3 className="text-lg font-semibold">{title}</h3>}
      <p className="text-muted-foreground">{message}</p>
      {action && (
        <Button onClick={action.onClick} variant="outline" className="mt-4">
          {action.label}
        </Button>
      )}
    </div>
  );
};
