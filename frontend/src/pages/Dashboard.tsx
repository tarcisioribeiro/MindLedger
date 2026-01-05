import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Wallet, TrendingDown, TrendingUp, CreditCard, LayoutDashboard } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedPage } from '@/components/common/AnimatedPage';
import { containerVariants, itemVariants } from '@/lib/animations';
import { StatCard } from '@/components/common/StatCard';
import { dashboardService } from '@/services/dashboard-service';
import { expensesService } from '@/services/expenses-service';
import { revenuesService } from '@/services/revenues-service';
import { useToast } from '@/hooks/use-toast';
import { translate } from '@/config/constants';
import { formatCurrency } from '@/lib/formatters';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import type { DashboardStats, Expense, Revenue } from '@/types';
import { Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { format, subMonths, startOfMonth, endOfMonth, eachMonthOfInterval } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useChartColors } from '@/lib/chart-colors';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [revenues, setRevenues] = useState<Revenue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [statsData, expensesData, revenuesData] = await Promise.all([
        dashboardService.getStats(),
        expensesService.getAll(),
        revenuesService.getAll(),
      ]);
      setStats(statsData);
      setExpenses(expensesData);
      setRevenues(revenuesData);
    } catch (error: any) {
      toast({ title: 'Erro ao carregar dados', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  // Memoize cálculos pesados para evitar re-renders desnecessários
  // Filtra apenas despesas pagas e receitas recebidas para os gráficos
  const expensesByCategory = useMemo(() => {
    return expenses
      .filter(exp => exp.payed) // Apenas despesas pagas
      .reduce((acc: any[], exp) => {
        const existing = acc.find(item => item.name === exp.category);
        if (existing) {
          existing.value += parseFloat(exp.value);
        } else {
          acc.push({ name: translate('expenseCategories', exp.category), value: parseFloat(exp.value) });
        }
        return acc;
      }, []).sort((a, b) => b.value - a.value).slice(0, 5);
  }, [expenses]);

  const revenuesByCategory = useMemo(() => {
    return revenues
      .filter(rev => rev.received) // Apenas receitas recebidas
      .reduce((acc: any[], rev) => {
        const existing = acc.find(item => item.name === rev.category);
        if (existing) {
          existing.value += parseFloat(rev.value);
        } else {
          acc.push({ name: translate('revenueCategories', rev.category), value: parseFloat(rev.value) });
        }
        return acc;
      }, []).sort((a, b) => b.value - a.value).slice(0, 5);
  }, [revenues]);

  const monthlyData = useMemo(() => {
    return eachMonthOfInterval({ start: subMonths(new Date(), 5), end: new Date() }).map(month => {
      const monthStart = startOfMonth(month);
      const monthEnd = endOfMonth(month);
      // Filtra apenas despesas pagas e receitas recebidas
      const monthExpenses = expenses
        .filter(e => e.payed && new Date(e.date) >= monthStart && new Date(e.date) <= monthEnd)
        .reduce((sum, e) => sum + parseFloat(e.value), 0);
      const monthRevenues = revenues
        .filter(r => r.received && new Date(r.date) >= monthStart && new Date(r.date) <= monthEnd)
        .reduce((sum, r) => sum + parseFloat(r.value), 0);
      return { month: format(month, 'MMM/yy', { locale: ptBR }), despesas: monthExpenses, receitas: monthRevenues, saldo: monthRevenues - monthExpenses };
    });
  }, [expenses, revenues]);

  const COLORS = useChartColors();

  if (isLoading) {
    return <LoadingState fullScreen />;
  }

  return (
    <AnimatedPage>
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          description="Visão geral das suas finanças"
          icon={<LayoutDashboard />}
        />

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <StatCard
              title="Saldo Total"
              value={formatCurrency(stats?.total_balance || 0)}
              icon={<Wallet className="h-4 w-4" />}
              subtitle={`${stats?.accounts_count || 0} conta(s)`}
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              title="Despesas do Mês"
              value={formatCurrency(stats?.total_expenses || 0)}
              icon={<TrendingDown className="h-4 w-4" />}
              subtitle={`${expenses.length} transação(ões)`}
              variant="danger"
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              title="Receitas do Mês"
              value={formatCurrency(stats?.total_revenues || 0)}
              icon={<TrendingUp className="h-4 w-4" />}
              subtitle={`${revenues.length} transação(ões)`}
              variant="success"
            />
          </motion.div>

          <motion.div variants={itemVariants}>
            <StatCard
              title="Limite de Crédito"
              value={formatCurrency(stats?.total_credit_limit || 0)}
              icon={<CreditCard className="h-4 w-4" />}
              subtitle={`${stats?.credit_cards_count || 0} cartão(ões)`}
            />
          </motion.div>
        </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Despesas por Categoria (Top 5)</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição das maiores categorias de gastos</p>
          </CardHeader>
          <CardContent>
            {expensesByCategory.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">Nenhuma despesa cadastrada</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={expensesByCategory} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={150} />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]} name="Valor">
                      {expensesByCategory.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {expensesByCategory.map((category, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                        <span>{category.name}</span>
                      </div>
                      <span className="font-semibold text-destructive">{formatCurrency(category.value)}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Receitas por Categoria (Top 5)</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição das fontes de receita</p>
          </CardHeader>
          <CardContent>
            {revenuesByCategory.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">Nenhuma receita cadastrada</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={revenuesByCategory} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={150} />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]} name="Valor">
                      {revenuesByCategory.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {revenuesByCategory.map((category, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                        <span>{category.name}</span>
                      </div>
                      <span className="font-semibold text-success">{formatCurrency(category.value)}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Evolução Mensal (Últimos 6 Meses)</CardTitle></CardHeader>
        <CardContent>
          {monthlyData.length === 0 ? (
            <div className="h-80 flex items-center justify-center text-muted-foreground">Nenhum dado disponível</div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px'
                  }}
                />
                <Legend />
                <Line type="monotone" dataKey="despesas" stroke={COLORS[5]} strokeWidth={2} name="Despesas" />
                <Line type="monotone" dataKey="receitas" stroke={COLORS[3]} strokeWidth={2} name="Receitas" />
                <Line type="monotone" dataKey="saldo" stroke={COLORS[0]} strokeWidth={2} name="Saldo" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
    </AnimatedPage>
  );
}
