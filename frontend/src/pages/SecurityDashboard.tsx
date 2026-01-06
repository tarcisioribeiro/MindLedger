import { useState, useEffect } from 'react';
import { Shield, Key, CreditCard, Wallet, Archive } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { securityDashboardService, type SecurityDashboardStats } from '@/services/security-dashboard-service';
import { useToast } from '@/hooks/use-toast';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, LineChart, Line, Legend } from 'recharts';
import { format } from 'date-fns';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useChartColors } from '@/lib/chart-colors';

export default function SecurityDashboard() {
  const [stats, setStats] = useState<SecurityDashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await securityDashboardService.getStats();
      setStats(data);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar dados',
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const COLORS = useChartColors();

  if (isLoading) {
    return <LoadingState fullScreen />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard de Segurança"
        description="Visão geral das suas informações de segurança"
        icon={<Shield />}
      />

      {/* Métricas Principais - Grid 2x2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Senhas</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_passwords || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_passwords === 1 ? 'senha cadastrada' : 'senhas cadastradas'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cartões Armazenados</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_stored_cards || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_stored_cards === 1 ? 'cartão armazenado' : 'cartões armazenados'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contas Bancárias</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_stored_accounts || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_stored_accounts === 1 ? 'conta armazenada' : 'contas armazenadas'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Arquivos</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_archives || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_archives === 1 ? 'arquivo armazenado' : 'arquivos armazenados'}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição de Itens */}
        <Card>
          <CardHeader>
            <CardTitle>Distribuição de Itens</CardTitle>
            <p className="text-sm text-muted-foreground">Tipos de itens armazenados</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.items_distribution.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum item cadastrado
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats.items_distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="count"
                      label
                      labelLine={false}
                    >
                      {stats.items_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any, name: string, props: any) => {
                        const type = props.payload.type_display || name;
                        return [`${value} ${value === 1 ? 'item' : 'itens'}`, type];
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.items_distribution.map((item, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>{item.type_display}</span>
                      </div>
                      <span className="font-semibold">
                        {item.count} {item.count === 1 ? 'item' : 'itens'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Senhas por Categoria */}
        <Card>
          <CardHeader>
            <CardTitle>Senhas por Categoria (Top 5)</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição de senhas por categoria</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.passwords_by_category.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma senha cadastrada
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.passwords_by_category} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="category_display" type="category" width={150} />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'senha' : 'senhas'}`, 'Quantidade']}
                    />
                    <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                      {stats.passwords_by_category.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.passwords_by_category.map((category, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>{category.category_display}</span>
                      </div>
                      <span className="font-semibold">
                        {category.count} {category.count === 1 ? 'senha' : 'senhas'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Força das Senhas */}
        <Card>
          <CardHeader>
            <CardTitle>Análise de Segurança das Senhas</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição por nível de segurança</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.password_strength_distribution.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma senha cadastrada
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.password_strength_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="strength_display" />
                    <YAxis />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'senha' : 'senhas'}`, 'Quantidade']}
                    />
                    <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                      {stats.password_strength_distribution.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            entry.strength === 'weak' ? '#ef4444' :
                            entry.strength === 'medium' ? '#f59e0b' :
                            '#22c55e'
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.password_strength_distribution.map((strength, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor:
                              strength.strength === 'weak' ? '#ef4444' :
                              strength.strength === 'medium' ? '#f59e0b' :
                              '#22c55e'
                          }}
                        ></div>
                        <span>{strength.strength_display}</span>
                      </div>
                      <span className="font-semibold">
                        {strength.count} {strength.count === 1 ? 'senha' : 'senhas'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Atividades por Tipo de Ação */}
        <Card>
          <CardHeader>
            <CardTitle>Atividades por Tipo de Ação</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição de ações realizadas</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.activities_by_action.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma atividade registrada
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.activities_by_action} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="action_display" type="category" width={100} />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'ação' : 'ações'}`, 'Quantidade']}
                    />
                    <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                      {stats.activities_by_action.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.activities_by_action.map((action, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>{action.action_display}</span>
                      </div>
                      <span className="font-semibold">
                        {action.count} {action.count === 1 ? 'ação' : 'ações'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row: Timeline + Atividades Recentes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline de Atividades */}
        <Card>
          <CardHeader>
            <CardTitle>Timeline de Atividades</CardTitle>
            <p className="text-sm text-muted-foreground">Atividades nos últimos 6 meses</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.activities_timeline.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma atividade registrada
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.activities_timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(value) => {
                      const [year, month] = value.split('-');
                      const date = new Date(parseInt(year), parseInt(month) - 1);
                      return format(date, 'MMM/yy', { locale: ptBR });
                    }}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => {
                      const [year, month] = value.split('-');
                      const date = new Date(parseInt(year), parseInt(month) - 1);
                      return format(date, 'MMMM yyyy', { locale: ptBR });
                    }}
                    labelStyle={{ color: 'hsl(var(--foreground))' }}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                    formatter={(value: any) => [`${value} ${value === 1 ? 'atividade' : 'atividades'}`, 'Quantidade']}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke={COLORS[0]}
                    strokeWidth={2}
                    name="Atividades"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Atividades Recentes */}
        <Card>
          <CardHeader>
            <CardTitle>Atividades Recentes</CardTitle>
            <p className="text-sm text-muted-foreground">Últimas 10 ações realizadas</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.recent_activity.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma atividade registrada
              </div>
            ) : (
              <div className="space-y-4 max-h-[350px] overflow-y-auto">
                {stats.recent_activity.map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-4 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {activity.description}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {activity.action_display} · {activity.model_name} · {
                          formatDistanceToNow(new Date(activity.created_at), {
                            addSuffix: true,
                            locale: ptBR
                          })
                        }
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
