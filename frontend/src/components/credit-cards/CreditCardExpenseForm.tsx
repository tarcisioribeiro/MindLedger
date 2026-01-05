import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { TRANSLATIONS } from '@/config/constants';
import type { CreditCardExpense, CreditCardExpenseFormData, CreditCard, CreditCardBill, Member } from '@/types';

import { formatLocalDate } from '@/lib/utils';
interface CreditCardExpenseFormProps {
  expense?: CreditCardExpense;
  creditCards: CreditCard[];
  bills?: CreditCardBill[];
  members?: Member[];
  onSubmit: (data: CreditCardExpenseFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const CreditCardExpenseForm: React.FC<CreditCardExpenseFormProps> = ({
  expense,
  creditCards,
  bills = [],
  members = [],
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { showAlert } = useAlertDialog();
  const { register, handleSubmit, setValue, watch } = useForm<CreditCardExpenseFormData>({
    defaultValues: {
      description: '',
      value: 0,
      date: new Date().toISOString().split('T')[0],
      horary: new Date().toTimeString().split(' ')[0].substring(0, 5),
      category: '',
      card: 0,
      installment: 1,
      total_installments: 1,
      payed: false,
      merchant: '',
      transaction_id: '',
      location: '',
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
    : 0;

  // Atualizar membro automaticamente quando cartão é selecionado
  useEffect(() => {
    if (watchedCard && creditCards.length > 0) {
      const selectedCard = creditCards.find(c => c.id === watchedCard);
      if (selectedCard?.owner) {
        setValue('member', selectedCard.owner);
      }
    }
  }, [watchedCard, creditCards, setValue]);

  useEffect(() => {
    if (expense) {
      setValue('description', expense.description);
      setValue('value', parseFloat(expense.value));
      setValue('date', expense.date);
      setValue('horary', expense.horary);
      setValue('category', expense.category);
      setValue('card', expense.card);
      setValue('installment', expense.installment);
      setValue('total_installments', expense.total_installments);
      setValue('payed', expense.payed);
      setValue('merchant', expense.merchant || '');
      setValue('transaction_id', expense.transaction_id || '');
      setValue('location', expense.location || '');
      setValue('bill', expense.bill);
      setValue('member', expense.member);
      setValue('notes', expense.notes || '');
    } else if (creditCards.length > 0) {
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
            value={watch('date') ? new Date(watch('date')) : undefined}
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
                const last4 = c.card_number_masked ? c.card_number_masked.slice(-4) : '****';
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
          <Label htmlFor="installment">Parcela Atual *</Label>
          <Input
            id="installment"
            type="number"
            min="1"
            {...register('installment', { required: true, valueAsNumber: true })}
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="total_installments">Total de Parcelas *</Label>
          <Input
            id="total_installments"
            type="number"
            min="1"
            {...register('total_installments', { required: true, valueAsNumber: true })}
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label>Valor por Parcela</Label>
          <div className="px-3 py-2 border rounded-md bg-muted/50 text-sm font-semibold">
            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(installmentValue)}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="merchant">Estabelecimento</Label>
          <Input
            id="merchant"
            {...register('merchant')}
            placeholder="Ex: Mercado XYZ"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="location">Local</Label>
          <Input
            id="location"
            {...register('location')}
            placeholder="Ex: São Paulo - SP"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="transaction_id">ID da Transação</Label>
          <Input
            id="transaction_id"
            {...register('transaction_id')}
            placeholder="Ex: TRX123456"
            disabled={isLoading}
          />
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

        {members.length > 0 && (
          <div className="space-y-2">
            <Label>Membro Responsável</Label>
            <Select
              value={watch('member')?.toString() || 'none'}
              onValueChange={(v) => setValue('member', v === 'none' ? null : parseInt(v))}
            >
              <SelectTrigger><SelectValue placeholder="Selecione (opcional)" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Nenhum</SelectItem>
                {members.map((m) => (
                  <SelectItem key={m.id} value={m.id.toString()}>
                    {m.name}
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

        <div className="flex items-center space-x-2 md:col-span-2">
          <Checkbox
            id="payed"
            checked={watch('payed')}
            onCheckedChange={(checked: boolean) => setValue('payed', !!checked)}
            disabled={isLoading}
          />
          <Label htmlFor="payed" className="cursor-pointer">Despesa Paga</Label>
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
