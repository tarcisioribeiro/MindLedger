import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Filter, CreditCard as CreditCardIcon, Receipt } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CreditCardBillForm } from '@/components/credit-cards/CreditCardBillForm';
import { creditCardBillsService } from '@/services/credit-card-bills-service';
import { creditCardsService } from '@/services/credit-cards-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { translate, TRANSLATIONS } from '@/config/constants';
import { formatCurrency, formatDate } from '@/lib/formatters';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import type { CreditCardBill, CreditCardBillFormData, CreditCard } from '@/types';

export default function CreditCardBills() {
  const [bills, setBills] = useState<CreditCardBill[]>([]);
  const [filteredBills, setFilteredBills] = useState<CreditCardBill[]>([]);
  const [creditCards, setCreditCards] = useState<CreditCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedBill, setSelectedBill] = useState<CreditCardBill | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cardFilter, setCardFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>('all');
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterBills();
  }, [cardFilter, statusFilter, yearFilter, bills]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [billsData, cardsData] = await Promise.all([
        creditCardBillsService.getAll(),
        creditCardsService.getAll(),
      ]);
      setBills(billsData);
      setFilteredBills(billsData);
      setCreditCards(cardsData);
    } catch (error: any) {
      toast({ title: 'Erro ao carregar dados', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const filterBills = () => {
    let filtered = [...bills];
    if (cardFilter !== 'all') {
      filtered = filtered.filter(b => b.credit_card.toString() === cardFilter);
    }
    if (statusFilter !== 'all') {
      filtered = filtered.filter(b => b.status === statusFilter);
    }
    if (yearFilter !== 'all') {
      filtered = filtered.filter(b => b.year === yearFilter);
    }
    setFilteredBills(filtered);
  };

  const handleSubmit = async (data: CreditCardBillFormData) => {
    try {
      setIsSubmitting(true);
      if (selectedBill) {
        await creditCardBillsService.update(selectedBill.id, data);
        toast({ title: 'Fatura atualizada', description: 'A fatura foi atualizada com sucesso.' });
      } else {
        await creditCardBillsService.create(data);
        toast({ title: 'Fatura criada', description: 'A fatura foi criada com sucesso.' });
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
        description: 'É necessário ter pelo menos um cartão de crédito cadastrado antes de criar uma fatura.',
        variant: 'destructive',
      });
      return;
    }
    setSelectedBill(undefined);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir fatura',
      description: 'Tem certeza que deseja excluir esta fatura? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });
    if (!confirmed) return;
    try {
      await creditCardBillsService.delete(id);
      toast({ title: 'Fatura excluída', description: 'A fatura foi excluída com sucesso.' });
      loadData();
    } catch (error: any) {
      toast({ title: 'Erro ao excluir', description: error.message, variant: 'destructive' });
    }
  };

  const getCardName = (bill: CreditCardBill) => {
    // Usa os dados que vêm diretamente da fatura (do backend expandido)
    const cardholderName = bill.credit_card_on_card_name || 'N/A';
    const last4 = bill.credit_card_number_masked || '****';

    // Verifica se last4 contém apenas dígitos e tem 4 caracteres
    const isValidNumber = last4 !== '****' && /^\d{4}$/.test(last4);
    const cardNumber = isValidNumber ? `**** ${last4}` : 'Não cadastrado';

    const flag = bill.credit_card_flag ? translate('cardBrands', bill.credit_card_flag) : 'N/A';
    const account = bill.credit_card_associated_account_name || 'N/A';

    return `${cardholderName} ${cardNumber} - ${flag} - ${account}`;
  };

  const handleEdit = (bill: CreditCardBill) => {
    setSelectedBill(bill);
    setIsDialogOpen(true);
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => (currentYear - 2 + i).toString());

  // Definir colunas da tabela
  const columns: Column<CreditCardBill>[] = [
    {
      key: 'credit_card',
      label: 'Cartão',
      render: (bill) => (
        <div className="flex items-center gap-2">
          <CreditCardIcon className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium">{getCardName(bill)}</span>
        </div>
      ),
    },
    {
      key: 'period',
      label: 'Período',
      render: (bill) => `${translate('months', bill.month)}/${bill.year}`,
    },
    {
      key: 'total_amount',
      label: 'Valor Total',
      align: 'right',
      render: (bill) => (
        <span className="font-semibold">{formatCurrency(bill.total_amount)}</span>
      ),
    },
    {
      key: 'minimum_payment',
      label: 'Pag. Mínimo',
      align: 'right',
      render: (bill) => (
        <span className="text-sm font-medium text-amber-600">
          {formatCurrency(bill.minimum_payment)}
        </span>
      ),
    },
    {
      key: 'paid_amount',
      label: 'Pago',
      align: 'right',
      render: (bill) => (
        <span className="font-semibold text-success">
          {formatCurrency(bill.paid_amount)}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (bill) => (
        <Badge
          variant={
            bill.status === 'paid'
              ? 'success'
              : bill.status === 'overdue'
              ? 'destructive'
              : bill.status === 'closed'
              ? 'secondary'
              : 'default'
          }
        >
          {translate('billStatus', bill.status)}
        </Badge>
      ),
    },
    {
      key: 'due_date',
      label: 'Vencimento',
      render: (bill) => (
        <span className="text-sm text-muted-foreground">
          {bill.due_date ? formatDate(bill.due_date) : 'N/A'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Faturas de Cartão"
        description="Gerencie suas faturas de cartão de crédito"
        icon={<Receipt />}
        action={{
          label: 'Nova Fatura',
          icon: <Plus className="w-4 h-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="bg-card border rounded-xl p-4 space-y-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="font-semibold">Filtros</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Select value={cardFilter} onValueChange={setCardFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Todos os Cartões" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Cartões</SelectItem>
              {creditCards.map((c) => (
                <SelectItem key={c.id} value={c.id.toString()}>
                  {c.on_card_name || c.card_number_masked}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Todos os Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Status</SelectItem>
              {Object.entries(TRANSLATIONS.billStatus).map(([k, v]) => (
                <SelectItem key={k} value={k}>
                  {v}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={yearFilter} onValueChange={setYearFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Todos os Anos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os Anos</SelectItem>
              {years.map((y) => (
                <SelectItem key={y} value={y}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex justify-between items-center pt-2 border-t">
          <span className="text-sm text-muted-foreground">
            {filteredBills.length} fatura(s) encontrada(s)
          </span>
        </div>
      </div>

      <DataTable
        data={filteredBills}
        columns={columns}
        keyExtractor={(bill) => bill.id}
        isLoading={isLoading}
        emptyState={{
          message: 'Nenhuma fatura encontrada.',
        }}
        actions={(bill) => (
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="icon" onClick={() => handleEdit(bill)}>
              <Pencil className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => handleDelete(bill.id)}>
              <Trash2 className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        )}
      />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedBill ? 'Editar' : 'Nova'} Fatura de Cartão</DialogTitle>
            <DialogDescription>Preencha os dados da fatura de cartão de crédito</DialogDescription>
          </DialogHeader>
          <CreditCardBillForm
            bill={selectedBill}
            creditCards={creditCards}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
