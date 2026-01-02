import { useEffect, useState } from 'react';
import { TrendingDown, TrendingUp, Calendar, DollarSign } from 'lucide-react';
import { StatCard } from '@/components/common/StatCard';
import { fixedExpensesService } from '@/services/fixed-expenses-service';
import { formatCurrency } from '@/lib/formatters';
import type { FixedExpenseStats as StatsType } from '@/types';

export const FixedExpenseStats = () => {
  const [stats, setStats] = useState<StatsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setIsLoading(true);
      const data = await fixedExpensesService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !stats) {
    return <div className="text-muted-foreground">Carregando estatísticas...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Modelos Ativos"
        value={stats.active_templates}
        icon={<Calendar className="w-5 h-5" />}
        variant="default"
      />
      <StatCard
        title="Total do Mês"
        value={formatCurrency(stats.current_month.total_value)}
        icon={<DollarSign className="w-5 h-5" />}
        variant="danger"
        subtitle={`${stats.current_month.total_count} despesas`}
      />
      <StatCard
        title="Pagas / Pendentes"
        value={`${stats.current_month.paid_count} / ${stats.current_month.pending_count}`}
        icon={<TrendingDown className="w-5 h-5" />}
        variant={stats.current_month.pending_count > 0 ? 'warning' : 'success'}
      />
      <StatCard
        title="Vs. Mês Anterior"
        value={formatCurrency(Math.abs(stats.comparison.difference))}
        icon={
          stats.comparison.difference >= 0 ? (
            <TrendingUp className="w-5 h-5" />
          ) : (
            <TrendingDown className="w-5 h-5" />
          )
        }
        variant={stats.comparison.difference >= 0 ? 'danger' : 'success'}
        subtitle={`${stats.comparison.percentage_change.toFixed(1)}%`}
      />
    </div>
  );
};
