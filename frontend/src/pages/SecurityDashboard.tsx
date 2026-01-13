import { useState, useEffect } from 'react';
import { Shield, Key, CreditCard, Wallet, Archive } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { securityDashboardService, type SecurityDashboardStats } from '@/services/security-dashboard-service';
import { useToast } from '@/hooks/use-toast';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { useChartColors } from '@/lib/chart-colors';
import { ChartContainer } from '@/components/charts';

type PasswordStrength = 'weak' | 'medium' | 'strong';

const strengthColors: Record<PasswordStrength, string> = {
    weak: '#ff5555',    // Dracula red
    medium: '#f1fa8c',  // Dracula yellow
    strong: '#50fa7b'   // Dracula green
};

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
            <ChartContainer
              chartId="security-items-distribution"
              data={stats?.items_distribution || []}
              dataKey="count"
              nameKey="type_display"
              formatter={(value) => `${value} ${value === 1 ? 'item' : 'itens'}`}
              colors={COLORS}
              emptyMessage="Nenhum item cadastrado"
              enabledTypes={['pie']}
            />
            {stats && stats.items_distribution.length > 0 && (
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
            <ChartContainer
              chartId="security-passwords-category"
              data={stats?.passwords_by_category || []}
              dataKey="count"
              nameKey="category_display"
              formatter={(value) => `${value} ${value === 1 ? 'senha' : 'senhas'}`}
              colors={COLORS}
              emptyMessage="Nenhuma senha cadastrada"
              defaultType="pie"
              layout="horizontal"
              enabledTypes={['pie']}
            />
            {stats && stats.passwords_by_category.length > 0 && (
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
            <ChartContainer
              chartId="security-password-strength"
              data={stats?.password_strength_distribution || []}
              dataKey="count"
              nameKey="strength_display"
              formatter={(value) => `${value} ${value === 1 ? 'senha' : 'senhas'}`}
              colors={COLORS}
              customColors={(entry) => strengthColors[entry.strength as PasswordStrength] || COLORS[0]}
              emptyMessage="Nenhuma senha cadastrada"
              layout="horizontal"
              enabledTypes={['pie']}
            />
            {stats && stats.password_strength_distribution.length > 0 && (
              <div className="mt-4 space-y-2">
                {stats.password_strength_distribution.map((strength, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor:
                            strength.strength === 'weak' ? '#ff5555' :      // Dracula red
                            strength.strength === 'medium' ? '#f1fa8c' :    // Dracula yellow
                            '#50fa7b'                                        // Dracula green
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
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
