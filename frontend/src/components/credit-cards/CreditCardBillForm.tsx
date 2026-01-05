import { useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { TRANSLATIONS } from '@/config/constants';
import type { CreditCardBill, CreditCardBillFormData, CreditCard } from '@/types';

import { formatLocalDate } from '@/lib/utils';
interface CreditCardBillFormProps {
  bill?: CreditCardBill;
  creditCards: CreditCard[];
  onSubmit: (data: CreditCardBillFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const CreditCardBillForm: React.FC<CreditCardBillFormProps> = ({
  bill,
  creditCards,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { showAlert } = useAlertDialog();
  const { register, handleSubmit, setValue, watch } = useForm<CreditCardBillFormData>({
    defaultValues: {
      credit_card: 0,
      year: new Date().getFullYear().toString(),
      month: 'Jan',
      invoice_beginning_date: formatLocalDate(new Date()),
      invoice_ending_date: formatLocalDate(new Date()),
      closed: false,
      total_amount: 0,
      minimum_payment: 0,
      paid_amount: 0,
      interest_charged: 0,
      late_fee: 0,
      status: 'open',
    },
  });

  useEffect(() => {
    if (bill) {
      setValue('credit_card', bill.credit_card);
      setValue('year', bill.year);
      setValue('month', bill.month);
      setValue('invoice_beginning_date', bill.invoice_beginning_date);
      setValue('invoice_ending_date', bill.invoice_ending_date);
      setValue('closed', bill.closed);
      setValue('total_amount', parseFloat(bill.total_amount));
      setValue('minimum_payment', parseFloat(bill.minimum_payment));
      setValue('paid_amount', parseFloat(bill.paid_amount));
      setValue('interest_charged', parseFloat(bill.interest_charged));
      setValue('late_fee', parseFloat(bill.late_fee));
      setValue('status', bill.status);
      if (bill.due_date) setValue('due_date', bill.due_date);
      if (bill.payment_date) setValue('payment_date', bill.payment_date);
    } else if (creditCards.length > 0) {
      setValue('credit_card', creditCards[0].id);
    }
  }, [bill, creditCards, setValue]);

  const handleFormSubmit = async (data: CreditCardBillFormData) => {
    if (!data.credit_card || data.credit_card === 0) {
      await showAlert({
        title: 'Campo obrigatório',
        description: 'Por favor, selecione um cartão de crédito',
        confirmText: 'Ok',
      });
      return;
    }

    // Garantir que campos de data vazios sejam enviados como undefined ao invés de strings vazias
    const sanitizedData = {
      ...data,
      due_date: data.due_date && data.due_date.trim() !== '' ? data.due_date : undefined,
      payment_date: data.payment_date && data.payment_date.trim() !== '' ? data.payment_date : undefined,
    };

    onSubmit(sanitizedData);
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => (currentYear - 1 + i).toString());

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2 md:col-span-2">
          <Label>Cartão de Crédito *</Label>
          <Select
            value={watch('credit_card')?.toString() || ''}
            onValueChange={(v) => setValue('credit_card', parseInt(v))}
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
          <Label>Ano *</Label>
          <Select value={watch('year')} onValueChange={(v) => setValue('year', v)}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {years.map((y) => <SelectItem key={y} value={y}>{y}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Mês *</Label>
          <Select value={watch('month')} onValueChange={(v) => setValue('month', v)}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.months).map(([k, v]) => (
                <SelectItem key={k} value={k}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="invoice_beginning_date">Data de Início *</Label>
          <DatePicker
            value={watch('invoice_beginning_date') ? new Date(watch('invoice_beginning_date')) : undefined}
            onChange={(date) => setValue('invoice_beginning_date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de início"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="invoice_ending_date">Data de Fim *</Label>
          <DatePicker
            value={watch('invoice_ending_date') ? new Date(watch('invoice_ending_date')) : undefined}
            onChange={(date) => setValue('invoice_ending_date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de fim"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="due_date">Data de Vencimento</Label>
          <DatePicker
            value={watch('due_date') && watch('due_date') !== '' ? new Date(watch('due_date')!) : undefined}
            onChange={(date) => setValue('due_date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de vencimento"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="total_amount">Valor Total</Label>
          <Input
            id="total_amount"
            type="number"
            step="0.01"
            {...register('total_amount', { valueAsNumber: true })}
            placeholder="0.00"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="minimum_payment">Pagamento Mínimo</Label>
          <Input
            id="minimum_payment"
            type="number"
            step="0.01"
            {...register('minimum_payment', { valueAsNumber: true })}
            placeholder="0.00"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="paid_amount">Valor Pago</Label>
          <Input
            id="paid_amount"
            type="number"
            step="0.01"
            {...register('paid_amount', { valueAsNumber: true })}
            placeholder="0.00"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="payment_date">Data de Pagamento</Label>
          <DatePicker
            value={watch('payment_date') && watch('payment_date') !== '' ? new Date(watch('payment_date')!) : undefined}
            onChange={(date) => setValue('payment_date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de pagamento"
            disabled={isLoading}
          />
        </div>

        <div className="space-y-2">
          <Label>Status *</Label>
          <Select value={watch('status')} onValueChange={(v: any) => setValue('status', v)}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.billStatus).map(([k, v]) => (
                <SelectItem key={k} value={k}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2 md:col-span-2 pt-2">
          <Checkbox
            id="closed"
            checked={watch('closed')}
            onCheckedChange={(checked: boolean) => setValue('closed', !!checked)}
            disabled={isLoading}
          />
          <Label htmlFor="closed" className="cursor-pointer">Fatura Fechada</Label>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Salvando...' : bill ? 'Atualizar' : 'Criar'}
        </Button>
      </div>
    </form>
  );
};
