import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { RevenueForm } from '@/components/revenues/RevenueForm';
import { revenuesService } from '@/services/revenues-service';
import { accountsService } from '@/services/accounts-service';
import { loansService } from '@/services/loans-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { translate } from '@/config/constants';
import { formatCurrency, formatDateTime } from '@/lib/formatters';
import { sumByProperty } from '@/lib/helpers';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import type { Revenue, RevenueFormData, Account, Loan } from '@/types';

export default function Revenues() {
  const [revenues, setRevenues] = useState<Revenue[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedRevenue, setSelectedRevenue] = useState<Revenue | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [revenuesData, accountsData, loansData] = await Promise.all([
        revenuesService.getAll(),
        accountsService.getAll(),
        loansService.getAll(),
      ]);
      setRevenues(revenuesData);
      setAccounts(accountsData);
      setLoans(Array.isArray(loansData) ? loansData : []);
    } catch (error: any) {
      toast({ title: 'Erro ao carregar dados', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (data: RevenueFormData) => {
    try {
      setIsSubmitting(true);
      if (selectedRevenue) {
        await revenuesService.update(selectedRevenue.id, data);
        toast({ title: 'Receita atualizada', description: 'A receita foi atualizada com sucesso.' });
      } else {
        await revenuesService.create(data);
        toast({ title: 'Receita criada', description: 'A receita foi criada com sucesso.' });
      }
      setIsDialogOpen(false);
      loadData();
    } catch (error: any) {
      toast({ title: 'Erro ao salvar', description: error.message, variant: 'destructive' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreate = () => {
    if (accounts.length === 0) {
      toast({
        title: 'Ação não permitida',
        description: 'É necessário ter pelo menos uma conta cadastrada antes de criar uma receita.',
        variant: 'destructive',
      });
      return;
    }
    setSelectedRevenue(undefined);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir receita',
      description: 'Tem certeza que deseja excluir esta receita? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });
    if (!confirmed) return;
    try {
      await revenuesService.delete(id);
      toast({ title: 'Receita excluída', description: 'A receita foi excluída com sucesso.' });
      loadData();
    } catch (error: any) {
      toast({ title: 'Erro ao excluir', description: error.message, variant: 'destructive' });
    }
  };

  const totalRevenues = sumByProperty(
    revenues.map((r) => ({ value: parseFloat(r.value) })),
    'value'
  );

  const handleEdit = (revenue: Revenue) => {
    setSelectedRevenue(revenue);
    setIsDialogOpen(true);
  };

  // Definir colunas da tabela
  const columns: Column<Revenue>[] = [
    {
      key: 'description',
      label: 'Descrição',
      render: (revenue) => (
        <div>
          <div className="font-medium">{revenue.description}</div>
          {revenue.source && (
            <div className="text-xs text-muted-foreground">Origem: {revenue.source}</div>
          )}
        </div>
      ),
    },
    {
      key: 'value',
      label: 'Valor',
      align: 'right',
      render: (revenue) => (
        <span className="font-semibold text-success">
          {formatCurrency(revenue.value)}
        </span>
      ),
    },
    {
      key: 'account',
      label: 'Conta',
      render: (revenue) => (
        <span className="text-sm">{revenue.account_name || 'N/A'}</span>
      ),
    },
    {
      key: 'category',
      label: 'Categoria',
      render: (revenue) => (
        <Badge variant="success">{translate('revenueCategories', revenue.category)}</Badge>
      ),
    },
    {
      key: 'received',
      label: 'Status',
      render: (revenue) => (
        <Badge variant={revenue.received ? 'success' : 'secondary'}>
          {revenue.received ? 'Recebido' : 'Pendente'}
        </Badge>
      ),
    },
    {
      key: 'date',
      label: 'Data',
      render: (revenue) => (
        <div>
          <div className="text-sm">{formatDateTime(revenue.date, revenue.horary)}</div>
          {revenue.member_name && (
            <div className="text-xs text-muted-foreground">Membro: {revenue.member_name}</div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Receitas"
        description="Acompanhe suas receitas"
        icon={<TrendingUp />}
        action={{
          label: 'Nova Receita',
          icon: <Plus className="w-4 h-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="bg-card border rounded-xl p-4 flex justify-between items-center">
        <span className="text-sm text-muted-foreground">
          {revenues.length} receita(s) cadastrada(s)
        </span>
        <span className="text-lg font-bold text-success">
          Total: {formatCurrency(totalRevenues)}
        </span>
      </div>

      <DataTable
        data={revenues}
        columns={columns}
        keyExtractor={(revenue) => revenue.id}
        isLoading={isLoading}
        emptyState={{
          message: 'Nenhuma receita cadastrada.',
        }}
        actions={(revenue) => (
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="icon" onClick={() => handleEdit(revenue)}>
              <Pencil className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => handleDelete(revenue.id)}>
              <Trash2 className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        )}
      />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedRevenue ? 'Editar Receita' : 'Nova Receita'}</DialogTitle>
            <DialogDescription>{selectedRevenue ? 'Atualize as informações da receita' : 'Adicione uma nova receita ao sistema'}</DialogDescription>
          </DialogHeader>
          <RevenueForm revenue={selectedRevenue} accounts={accounts} loans={loans} onSubmit={handleSubmit} onCancel={() => setIsDialogOpen(false)} isLoading={isSubmitting} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
