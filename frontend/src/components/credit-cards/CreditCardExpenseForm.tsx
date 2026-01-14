import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { TRANSLATIONS } from '@/config/constants';
import type { CreditCardExpense, CreditCardExpenseFormData, CreditCard, CreditCardBill } from '@/types';

import { formatLocalDate } from '@/lib/utils';
interface CreditCardExpenseFormProps {
  expense?: CreditCardExpense;
  creditCards: CreditCard[];
  bills?: CreditCardBill[];
  onSubmit: (data: CreditCardExpenseFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const CreditCardExpenseForm: React.FC<CreditCardExpenseFormProps> = ({
  expense,
  creditCards,
  bills = [],
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { showAlert } = useAlertDialog();
  const { register, handleSubmit, setValue, watch } = useForm<CreditCardExpenseFormData>({
    defaultValues: {
      description: '',
      value: 0,
      date: formatLocalDate(new Date()),
      horary: new Date().toTimeString().split(' ')[0].substring(0, 5),
      category: '',
      card: 0,
      total_installments: 1,
      bill: null,
      member: null,
      notes: '',
    },
  });

  // Watch valores para cálculo de parcela
  const watchedValue = watch('value');
  const watchedTotalInstallments = watch('total_installments');
  const watchedCard = watch('card');

  // Calcular valor por parcela
  const installmentValue = watchedTotalInstallments > 0
    ? (watchedValue / watchedTotalInstallments)
    : watchedValue;

  // Função para encontrar a fatura atual de um cartão
  const getCurrentBill = (cardId: number) => {
    if (!bills || bills.length === 0) return null;

    const today = new Date();
    const cardBills = bills.filter(b => b.credit_card === cardId);

    // Encontrar fatura cujo período inclui a data atual
    const currentBill = cardBills.find(b => {
      const beginDate = new Date(b.invoice_beginning_date);
      const endDate = new Date(b.invoice_ending_date);
      return today >= beginDate && today <= endDate;
    });

    if (currentBill) return currentBill.id;

    // Se não encontrar, pegar a fatura mais recente em aberto
    const openBills = cardBills.filter(b => b.status === 'open');
    if (openBills.length > 0) {
      openBills.sort((a, b) => new Date(b.invoice_beginning_date).getTime() - new Date(a.invoice_beginning_date).getTime());
      return openBills[0].id;
    }

    return null;
  };

  // Atualizar membro e fatura automaticamente quando cartão é selecionado
  useEffect(() => {
    if (watchedCard && creditCards.length > 0 && !expense) {
      const selectedCard = creditCards.find(c => c.id === watchedCard);

      // Atualizar membro
      if (selectedCard?.owner) {
        setValue('member', selectedCard.owner);
      }

      // Atualizar fatura automaticamente
      const billId = getCurrentBill(watchedCard);
      if (billId) {
        setValue('bill', billId);
      }
    }
  }, [watchedCard, creditCards, bills, setValue, expense]);

  useEffect(() => {
    if (expense) {
      setValue('description', expense.description);
      setValue('value', parseFloat(expense.value));
      setValue('date', expense.date);
      setValue('horary', expense.horary);
      setValue('category', expense.category);
      setValue('card', expense.card);
      setValue('total_installments', expense.total_installments);
      setValue('bill', expense.bill);
      setValue('member', expense.member);
      setValue('notes', expense.notes || '');
    } else if (creditCards.length > 0) {
      // Seleciona automaticamente o primeiro cartão
      setValue('card', creditCards[0].id);
    }
  }, [expense, creditCards, setValue]);

  const handleFormSubmit = async (data: CreditCardExpenseFormData) => {
    if (!data.card || data.card === 0) {
      await showAlert({
        title: 'Campo obrigatório',
        description: 'Por favor, selecione um cartão de crédito',
        confirmText: 'Ok',
      });
      return;
    }
    if (!data.category) {
      await showAlert({
        title: 'Campo obrigatório',
        description: 'Por favor, selecione uma categoria',
        confirmText: 'Ok',
      });
      return;
    }
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="description">Descrição *</Label>
          <Input
            id="description"
            {...register('description', { required: true })}
            placeholder="Ex: Compra no mercado"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="value">Valor *</Label>
          <Input
            id="value"
            type="number"
            step="0.01"
            {...register('value', { required: true, valueAsNumber: true })}
            placeholder="0.00"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label>Categoria *</Label>
          <Select value={watch('category') || ''} onValueChange={(v) => setValue('category', v)}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.expenseCategories).map(([k, v]) => (
                <SelectItem key={k} value={k}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="date">Data *</Label>
          <DatePicker
            value={watch('date')}
            onChange={(date) => setValue('date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="horary">Horário *</Label>
          <Input
            id="horary"
            type="time"
            {...register('horary', { required: true })}
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label>Cartão de Crédito *</Label>
          <Select
            value={watch('card')?.toString() || ''}
            onValueChange={(v) => setValue('card', parseInt(v))}
          >
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {creditCards.map((c) => {
                // Extrai apenas os dígitos do número mascarado
                const digitsOnly = c.card_number_masked ? c.card_number_masked.replace(/[^\d]/g, '') : '';
                const last4 = digitsOnly && digitsOnly.length >= 4 ? digitsOnly.slice(-4) : '****';
                return (
                  <SelectItem key={c.id} value={c.id.toString()}>
                    {c.on_card_name} ****{last4}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="total_installments">Número de Parcelas *</Label>
          <Input
            id="total_installments"
            type="number"
            min="1"
            {...register('total_installments', { required: true, valueAsNumber: true })}
            disabled={isLoading}
          />
          <p className="text-xs text-muted-foreground">
            {watchedTotalInstallments > 1
              ? `Serão criadas ${watchedTotalInstallments} parcelas de ${new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(installmentValue)} cada`
              : 'Pagamento à vista'}
          </p>
        </div>

        {bills.length > 0 && (
          <div className="space-y-2">
            <Label>Fatura Associada</Label>
            <Select
              value={watch('bill')?.toString() || 'none'}
              onValueChange={(v) => setValue('bill', v === 'none' ? null : parseInt(v))}
            >
              <SelectTrigger><SelectValue placeholder="Selecione (opcional)" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Nenhuma</SelectItem>
                {bills.map((b) => (
                  <SelectItem key={b.id} value={b.id.toString()}>
                    {TRANSLATIONS.months[b.month as keyof typeof TRANSLATIONS.months]}/{b.year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}


        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="notes">Observações</Label>
          <Textarea
            id="notes"
            {...register('notes')}
            placeholder="Informações adicionais..."
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Salvando...' : expense ? 'Atualizar' : 'Criar'}
        </Button>
      </div>
    </form>
  );
};
