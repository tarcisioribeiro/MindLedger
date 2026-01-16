import { useState, useEffect, useMemo } from 'react';
import { Plus, Pencil, Trash2, Filter, ShoppingCart, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CreditCardExpenseForm } from '@/components/credit-cards/CreditCardExpenseForm';
import { creditCardExpensesService } from '@/services/credit-card-expenses-service';
import { creditCardsService } from '@/services/credit-cards-service';
import { creditCardBillsService } from '@/services/credit-card-bills-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { translate, TRANSLATIONS, EXPENSE_CATEGORIES_CANONICAL } from '@/config/constants';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { CreditCardExpense, CreditCardExpenseFormData, CreditCard, CreditCardBill } from '@/types';
import { PageContainer } from '@/components/common/PageContainer';

export default function CreditCardExpenses() {
  const [expenses, setExpenses] = useState<CreditCardExpense[]>([]);
  const [filteredExpenses, setFilteredExpenses] = useState<CreditCardExpense[]>([]);
  const [creditCards, setCreditCards] = useState<CreditCard[]>([]);
  const [bills, setBills] = useState<CreditCardBill[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState<CreditCardExpense | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cardFilter, setCardFilter] = useState<string>('all');
  const [billFilter, setBillFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'list' | 'grouped'>('grouped');
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterExpenses();
  }, [cardFilter, billFilter, categoryFilter, statusFilter, expenses]);

  // Faturas filtradas pelo cartão selecionado
  const availableBills = useMemo(() => {
    if (cardFilter === 'all') return bills;
    return bills.filter(b => b.credit_card.toString() === cardFilter);
  }, [cardFilter, bills]);

  // Reset bill filter when card changes
  useEffect(() => {
    if (cardFilter !== 'all') {
      const currentBillValid = availableBills.some(b => b.id.toString() === billFilter);
      if (!currentBillValid) {
        setBillFilter('all');
      }
    }
  }, [cardFilter, availableBills, billFilter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [expensesData, cardsData, billsData] = await Promise.all([
        creditCardExpensesService.getAll(),
        creditCardsService.getAll(),
        creditCardBillsService.getAll(),
      ]);
      setExpenses(expensesData);
      setFilteredExpenses(expensesData);
      setCreditCards(cardsData);
      setBills(billsData);
    } catch (error: any) {
      toast({ title: 'Erro ao carregar dados', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const filterExpenses = () => {
    let filtered = [...expenses];
    if (cardFilter !== 'all') filtered = filtered.filter(e => e.card.toString() === cardFilter);
    if (billFilter !== 'all') filtered = filtered.filter(e => e.bill?.toString() === billFilter);
    if (categoryFilter !== 'all') filtered = filtered.filter(e => e.category === categoryFilter);
    if (statusFilter !== 'all') filtered = filtered.filter(e => statusFilter === 'paid' ? e.payed : !e.payed);
    setFilteredExpenses(filtered);
  };

  // Agrupar despesas por mês
  const expensesByMonth = useMemo(() => {
    const grouped: Record<string, CreditCardExpense[]> = {};

    filteredExpenses.forEach(expense => {
      const date = new Date(expense.date);
      const monthKey = format(date, 'yyyy-MM');

      if (!grouped[monthKey]) {
        grouped[monthKey] = [];
      }
      grouped[monthKey].push(expense);
    });

    // Ordenar por data decrescente
    return Object.entries(grouped)
      .sort(([a], [b]) => b.localeCompare(a))
      .map(([key, monthExpenses]) => ({
        key,
        label: format(new Date(key + '-01'), 'MMMM yyyy', { locale: ptBR }),
        expenses: monthExpenses.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
        total: monthExpenses.reduce((sum, e) => sum + parseFloat(e.value), 0)
      }));
  }, [filteredExpenses]);

  const handleSubmit = async (data: CreditCardExpenseFormData) => {
    try {
      setIsSubmitting(true);

      if (selectedExpense) {
        await creditCardExpensesService.update(selectedExpense.id, data);
        toast({ title: 'Despesa atualizada', description: 'A despesa foi atualizada com sucesso.' });
      } else {
        const totalInstallments = data.total_installments || 1;

        if (totalInstallments > 1) {
          const installmentValue = data.value / totalInstallments;
          const baseDate = new Date(data.date);
          const promises = [];

          for (let i = 0; i < totalInstallments; i++) {
            const installmentDate = new Date(baseDate);
            installmentDate.setDate(installmentDate.getDate() + (i * 30));

            let installmentBill = data.bill;
            if (bills.length > 0) {
              const matchingBill = bills.find(b => {
                if (b.credit_card !== data.card) return false;
                const beginDate = new Date(b.invoice_beginning_date);
                const endDate = new Date(b.invoice_ending_date);
                return installmentDate >= beginDate && installmentDate <= endDate;
              });
              if (matchingBill) {
                installmentBill = matchingBill.id;
              }
            }

            const installmentData = {
              ...data,
              value: installmentValue,
              date: installmentDate.toISOString().split('T')[0],
              installment: i + 1,
              total_installments: totalInstallments,
              bill: installmentBill,
              payed: false,
            };

            promises.push(creditCardExpensesService.create(installmentData));
          }

          await Promise.all(promises);
          toast({
            title: 'Despesas criadas',
            description: `${totalInstallments} parcelas foram criadas com sucesso.`,
          });
        } else {
          const expenseData = {
            ...data,
            installment: 1,
            total_installments: 1,
            payed: false,
          };
          await creditCardExpensesService.create(expenseData);
          toast({ title: 'Despesa criada', description: 'A despesa foi criada com sucesso.' });
        }
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
    if (creditCards.length === 0) {
      toast({
        title: 'Ação não permitida',
        description: 'É necessário ter pelo menos um cartão de crédito cadastrado antes de criar uma despesa de cartão.',
        variant: 'destructive',
      });
      return;
    }
    setSelectedExpense(undefined);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir despesa',
      description: 'Tem certeza que deseja excluir esta despesa? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });
    if (!confirmed) return;
    try {
      await creditCardExpensesService.delete(id);
      toast({ title: 'Despesa excluída', description: 'A despesa foi excluída com sucesso.' });
      loadData();
    } catch (error: any) {
      toast({ title: 'Erro ao excluir', description: error.message, variant: 'destructive' });
    }
  };

  const getCardDisplayName = (cardId: number) => {
    const card = creditCards.find(c => c.id === cardId);
    if (card) {
      const digitsOnly = card.card_number_masked?.replace(/[^\d]/g, '') || '';
      const last4 = digitsOnly.length >= 4 ? digitsOnly.slice(-4) : '****';
      const brandName = TRANSLATIONS.cardBrands[card.flag as keyof typeof TRANSLATIONS.cardBrands] || card.flag;
      return `${card.name} **** ${last4} - ${brandName}`;
    }
    return 'N/A';
  };

  const getCardName = (cardId: number) => {
    const card = creditCards.find(c => c.id === cardId);
    if (card) {
      const digitsOnly = card.card_number_masked?.replace(/[^\d]/g, '') || '';
      const last4 = digitsOnly.length >= 4 ? digitsOnly.slice(-4) : '****';
      return `${card.name} **** ${last4}`;
    }
    return 'N/A';
  };

  const totalExpenses = filteredExpenses.reduce((sum, exp) => sum + parseFloat(exp.value), 0);

  const handleEdit = (expense: CreditCardExpense) => {
    setSelectedExpense(expense);
    setIsDialogOpen(true);
  };

  const columns: Column<CreditCardExpense>[] = [
    {
      key: 'description',
      label: 'Descrição',
      render: (expense) => (
        <div>
          <div className="font-medium">{expense.description}</div>
          {expense.merchant && <div className="text-sm text-muted-foreground">{expense.merchant}</div>}
        </div>
      ),
    },
    {
      key: 'card',
      label: 'Cartão',
      render: (expense) => <span className="text-sm">{getCardName(expense.card)}</span>,
    },
    {
      key: 'value',
      label: 'Valor',
      align: 'right',
      render: (expense) => (
        <span className="font-semibold text-destructive">
          {formatCurrency(expense.value)}
        </span>
      ),
    },
    {
      key: 'category',
      label: 'Categoria',
      render: (expense) => (
        <Badge variant="secondary">{translate('expenseCategories', expense.category)}</Badge>
      ),
    },
    {
      key: 'installment',
      label: 'Parcela',
      align: 'center',
      render: (expense) => (
        <span className="text-sm">
          {expense.installment}/{expense.total_installments}
        </span>
      ),
    },
    {
      key: 'payed',
      label: 'Status',
      render: (expense) => (
        <Badge variant={expense.payed ? 'success' : 'warning'}>
          {expense.payed ? 'Paga' : 'Pendente'}
        </Badge>
      ),
    },
    {
      key: 'date',
      label: 'Data',
      render: (expense) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(expense.date, 'dd/MM/yyyy')}
        </span>
      ),
    },
  ];

  // Colunas simplificadas para visualização agrupada (sem coluna de data)
  const groupedColumns: Column<CreditCardExpense>[] = columns.filter(c => c.key !== 'date');

  return (
    <PageContainer>
      <PageHeader
        title="Despesas de Cartão"
        description="Gerencie suas despesas de cartão de crédito"
        icon={<ShoppingCart />}
        action={{
          label: 'Nova Despesa',
          icon: <Plus className="w-4 h-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="bg-card border rounded-xl p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="font-semibold">Filtros</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Visualização:</span>
            <Select value={viewMode} onValueChange={(v) => setViewMode(v as 'list' | 'grouped')}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="grouped">Por Mês</SelectItem>
                <SelectItem value="list">Lista</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Select value={cardFilter} onValueChange={setCardFilter}>
            <SelectTrigger><SelectValue placeholder="Todos os Cartões" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Cartões</SelectItem>
              {creditCards.map((c) => (
                <SelectItem key={c.id} value={c.id.toString()}>
                  {getCardDisplayName(c.id)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={billFilter} onValueChange={setBillFilter} disabled={availableBills.length === 0}>
            <SelectTrigger>
              <SelectValue placeholder={availableBills.length === 0 ? "Nenhuma fatura" : "Todas as Faturas"} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as Faturas</SelectItem>
              {availableBills.map((b) => (
                <SelectItem key={b.id} value={b.id.toString()}>
                  {TRANSLATIONS.months[b.month as keyof typeof TRANSLATIONS.months]}/{b.year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger><SelectValue placeholder="Todas as Categorias" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as Categorias</SelectItem>
              {EXPENSE_CATEGORIES_CANONICAL.map(({ key, label }) => (
                <SelectItem key={key} value={key}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger><SelectValue placeholder="Todos os Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Status</SelectItem>
              <SelectItem value="paid">Pago</SelectItem>
              <SelectItem value="pending">Pendente</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex justify-between items-center pt-2 border-t">
          <span className="text-sm text-muted-foreground">{filteredExpenses.length} despesa(s) encontrada(s)</span>
          <span className="text-lg font-bold text-destructive">Total: {formatCurrency(totalExpenses)}</span>
        </div>
      </div>

      {viewMode === 'grouped' ? (
        <div className="space-y-6">
          {expensesByMonth.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Nenhuma despesa encontrada.
              </CardContent>
            </Card>
          ) : (
            expensesByMonth.map(({ key, label, expenses: monthExpenses, total }) => (
              <Card key={key}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-lg capitalize">
                      <Calendar className="w-5 h-5 text-primary" />
                      {label}
                    </CardTitle>
                    <span className="text-lg font-bold text-destructive">
                      {formatCurrency(total)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <DataTable
                    data={monthExpenses}
                    columns={groupedColumns}
                    keyExtractor={(expense) => expense.id}
                    isLoading={false}
                    emptyState={{ message: 'Nenhuma despesa.' }}
                    actions={(expense) => (
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(expense)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(expense.id)}>
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    )}
                  />
                </CardContent>
              </Card>
            ))
          )}
        </div>
      ) : (
        <DataTable
          data={filteredExpenses}
          columns={columns}
          keyExtractor={(expense) => expense.id}
          isLoading={isLoading}
          emptyState={{
            message: 'Nenhuma despesa encontrada.',
          }}
          actions={(expense) => (
            <div className="flex items-center justify-end gap-2">
              <Button variant="ghost" size="icon" onClick={() => handleEdit(expense)}>
                <Pencil className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={() => handleDelete(expense.id)}>
                <Trash2 className="w-4 h-4 text-destructive" />
              </Button>
            </div>
          )}
        />
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle>{selectedExpense ? 'Editar' : 'Nova'} Despesa de Cartão</DialogTitle>
            <DialogDescription>Preencha os dados da despesa de cartão de crédito</DialogDescription>
          </DialogHeader>
          <CreditCardExpenseForm
            expense={selectedExpense}
            creditCards={creditCards}
            bills={bills}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
