import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, CreditCard as CreditCardIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { CreditCardForm } from '@/components/credit-cards/CreditCardForm';
import { creditCardsService } from '@/services/credit-cards-service';
import { accountsService } from '@/services/accounts-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { translate } from '@/config/constants';
import { formatCurrency } from '@/lib/formatters';
import { sumByProperty } from '@/lib/helpers';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import type { CreditCard, CreditCardFormData, Account } from '@/types';

export default function CreditCards() {
  const [creditCards, setCreditCards] = useState<CreditCard[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState<CreditCard | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [cardsData, accountsData] = await Promise.all([
        creditCardsService.getAll(),
        accountsService.getAll(),
      ]);
      setCreditCards(cardsData);
      setAccounts(accountsData);
    } catch (error: any) {
      toast({ title: 'Erro ao carregar dados', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (data: CreditCardFormData) => {
    try {
      setIsSubmitting(true);
      if (selectedCard) {
        await creditCardsService.update(selectedCard.id, data);
        toast({ title: 'Cartão atualizado', description: 'O cartão foi atualizado com sucesso.' });
      } else {
        await creditCardsService.create(data);
        toast({ title: 'Cartão criado', description: 'O cartão foi criado com sucesso.' });
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
        description: 'É necessário ter pelo menos uma conta cadastrada antes de criar um cartão de crédito.',
        variant: 'destructive',
      });
      return;
    }
    setSelectedCard(undefined);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir cartão',
      description: 'Tem certeza que deseja excluir este cartão? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await creditCardsService.delete(id);
      toast({ title: 'Cartão excluído', description: 'O cartão foi excluído com sucesso.' });
      loadData();
    } catch (error: any) {
      toast({ title: 'Erro ao excluir', description: error.message, variant: 'destructive' });
    }
  };

  const totalLimit = sumByProperty(
    creditCards.map((c) => ({ value: parseFloat(c.credit_limit) })),
    'value'
  );

  const handleEdit = (card: CreditCard) => {
    setSelectedCard(card);
    setIsDialogOpen(true);
  };

  // Definir colunas da tabela
  const columns: Column<CreditCard>[] = [
    {
      key: 'name',
      label: 'Cartão',
      render: (card) => <div className="font-medium">{card.name}</div>,
    },
    {
      key: 'flag',
      label: 'Bandeira',
      render: (card) => <Badge>{translate('cardBrands', card.flag)}</Badge>,
    },
    {
      key: 'card_number_masked',
      label: 'Número',
      render: (card) => {
        if (!card.card_number_masked) return <span className="font-mono text-sm">N/A</span>;

        // Se já está mascarado (tem asteriscos ou é longo), mostra como está
        if (card.card_number_masked.includes('*') || card.card_number_masked.length > 4) {
          return <span className="font-mono text-sm">{card.card_number_masked}</span>;
        }

        // Se tem apenas os últimos 4 dígitos, formata com asteriscos
        if (card.card_number_masked.length === 4) {
          return <span className="font-mono text-sm">**** **** **** {card.card_number_masked}</span>;
        }

        // Caso contrário, mostra os últimos 4 dígitos do que vier
        return <span className="font-mono text-sm">**** **** **** {card.card_number_masked.slice(-4)}</span>;
      },
    },
    {
      key: 'credit_limit',
      label: 'Limite',
      align: 'right',
      render: (card) => (
        <span className="font-semibold">{formatCurrency(card.credit_limit)}</span>
      ),
    },
    {
      key: 'due_day',
      label: 'Vencimento',
      align: 'center',
      render: (card) => <span className="text-sm">Dia {card.due_day}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cartões de Crédito"
        description="Gerencie seus cartões de crédito"
        icon={<CreditCardIcon />}
        action={{
          label: 'Novo Cartão',
          icon: <Plus className="w-4 h-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="bg-card border rounded-xl p-4 flex justify-between items-center">
        <span className="text-sm text-muted-foreground">
          {creditCards.length} cartão(ões) cadastrado(s)
        </span>
        <span className="text-lg font-bold">Limite Total: {formatCurrency(totalLimit)}</span>
      </div>

      <DataTable
        data={creditCards}
        columns={columns}
        keyExtractor={(card) => card.id}
        isLoading={isLoading}
        emptyState={{
          message: 'Nenhum cartão cadastrado.',
        }}
        actions={(card) => (
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="icon" onClick={() => handleEdit(card)}>
              <Pencil className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => handleDelete(card.id)}>
              <Trash2 className="w-4 h-4 text-destructive" />
            </Button>
          </div>
        )}
      />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedCard ? 'Editar Cartão' : 'Novo Cartão'}</DialogTitle>
            <DialogDescription>{selectedCard ? 'Atualize as informações do cartão' : 'Adicione um novo cartão ao sistema'}</DialogDescription>
          </DialogHeader>
          <CreditCardForm creditCard={selectedCard} accounts={accounts} onSubmit={handleSubmit} onCancel={() => setIsDialogOpen(false)} isLoading={isSubmitting} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
