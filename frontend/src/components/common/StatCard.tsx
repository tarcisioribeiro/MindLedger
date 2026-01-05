/**
 * StatCard Component
 *
 * Componente reutilizável para cards de estatísticas.
 * Usado principalmente no Dashboard para exibir métricas financeiras.
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cardVariants } from '@/lib/animations';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const useCounterAnimation = (end: number, duration = 1.5) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const increment = end / (duration * 60);
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 1000 / 60);

    return () => clearInterval(timer);
  }, [end, duration]);

  return count;
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  subtitle,
  trend,
  variant = 'default',
}) => {
  const variantClasses = {
    default: '',
    success: 'border-success/50 bg-success/5',
    warning: 'border-warning/50 bg-warning/5',
    danger: 'border-destructive/50 bg-destructive/5',
  };

  // Parse numeric value for counter animation
  // For currency strings (R$ 1.234,56), we need to extract the number correctly
  const extractNumber = (val: string | number): number => {
    if (typeof val === 'number') return val;
    // Remove currency symbol and convert pt-BR format (1.234,56) to standard (1234.56)
    const cleaned = String(val)
      .replace(/[^\d.,-]/g, '') // Remove non-numeric chars except . , -
      .replace(/\./g, '') // Remove thousands separator (dot in pt-BR)
      .replace(',', '.'); // Convert decimal separator (comma to dot)
    return parseFloat(cleaned);
  };

  const numericValue = extractNumber(value);
  const isNumeric = !isNaN(numericValue);
  const animatedCount = useCounterAnimation(isNumeric ? numericValue : 0);

  // Format the displayed value
  const displayValue = isNumeric && typeof value === 'string' && value.includes('R$')
    ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(animatedCount)
    : isNumeric
    ? animatedCount.toLocaleString('pt-BR')
    : value;

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover="hover"
      whileTap="tap"
    >
      <Card className={`transition-shadow ${variantClasses[variant]}`}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
          {icon && (
            <motion.div
              className="text-muted-foreground"
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ duration: 0.3 }}
            >
              {icon}
            </motion.div>
          )}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{displayValue}</div>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.2 }}
              >
                {trend.isPositive ? (
                  <TrendingUp className="w-4 h-4 text-success" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-destructive" />
                )}
              </motion.div>
              <span
                className={`text-xs font-medium ${
                  trend.isPositive
                    ? 'text-success'
                    : 'text-destructive'
                }`}
              >
                {trend.value > 0 ? '+' : ''}
                {trend.value}%
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};
