import { useForm } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { TRANSLATIONS } from '@/config/constants';
import { membersService } from '@/services/members-service';
import type { Expense, ExpenseFormData, Account, Member, Loan } from '@/types';

interface ExpenseFormProps {
  expense?: Expense;
  accounts: Account[];
  members?: Member[];
  loans?: Loan[];
  onSubmit: (data: ExpenseFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ExpenseForm: React.FC<ExpenseFormProps> = ({ expense, accounts, loans, onSubmit, onCancel, isLoading = false }) => {
  const [currentUserMember, setCurrentUserMember] = useState<Member | null>(null);
  const [eligibleLoans, setEligibleLoans] = useState<Loan[]>([]);
  const { showAlert } = useAlertDialog();

  const { register, handleSubmit, setValue, watch } = useForm<ExpenseFormData>({
    defaultValues: {
      description: '',
      value: 0,
      date: new Date().toISOString().split('T')[0],
      horary: new Date().toTimeString().split(' ')[0].substring(0, 5),
      payed: false,
      category: '',
      account: 0,
      member: null,
    },
  });

  useEffect(() => {
    const loadCurrentUserMember = async () => {
      try {
        const member = await membersService.getCurrentUserMember();
        setCurrentUserMember(member);
        // Se não estamos editando, define o membro automaticamente
        if (!expense) {
          setValue('member', member.id);
        }
      } catch (error) {
        console.error('Erro ao carregar membro do usuário:', error);
      }
    };

    loadCurrentUserMember();
  }, [expense, setValue]);

  useEffect(() => {
    if (loans && currentUserMember) {
      // Filtrar empréstimos onde o usuário atual é o benefited (pegou emprestado, está pagando)
      const filtered = loans.filter(loan =>
        loan.benefited === currentUserMember.id &&
        loan.status !== 'paid' &&
        loan.status !== 'cancelled'
      );
      setEligibleLoans(filtered);
    }
  }, [loans, currentUserMember]);

  useEffect(() => {
    if (expense) {
      setValue('description', expense.description);
      setValue('value', parseFloat(expense.value));
      setValue('date', expense.date);
      setValue('horary', expense.horary);
      setValue('category', expense.category);
      setValue('payed', expense.payed);
      setValue('account', expense.account);
      setValue('member', expense.member);
      setValue('related_loan', expense.related_loan || null);
    } else if (accounts.length > 0) {
      setValue('account', accounts[0].id);
    }
  }, [expense, accounts, setValue]);

  const handleFormSubmit = async (data: ExpenseFormData) => {
    console.log('Form data before submit:', data);

    // Validação adicional
    if (!data.account || data.account === 0) {
      await showAlert({
        title: 'Campo obrigatório',
        description: 'Por favor, selecione uma conta',
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
          <Input id="description" {...register('description', { required: true })} placeholder="Ex: Compra no supermercado" disabled={isLoading} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="value">Valor *</Label>
          <Input id="value" type="number" step="0.01" {...register('value', { required: true, valueAsNumber: true })} placeholder="0.00" disabled={isLoading} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="date">Data *</Label>
          <Input id="date" type="date" {...register('date', { required: true })} disabled={isLoading} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="horary">Horário *</Label>
          <Input id="horary" type="time" {...register('horary', { required: true })} disabled={isLoading} />
        </div>
        <div className="space-y-2">
          <Label>Categoria *</Label>
          <Select value={watch('category') || ''} onValueChange={(v) => setValue('category', v)}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.expenseCategories).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Status de Pagamento *</Label>
          <Select value={watch('payed') ? 'true' : 'false'} onValueChange={(v) => setValue('payed', v === 'true')}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="false">Pendente</SelectItem>
              <SelectItem value="true">Pago</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Conta *</Label>
          <Select value={watch('account')?.toString() || ''} onValueChange={(v) => setValue('account', parseInt(v))}>
            <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
            <SelectContent>
              {accounts.map((a) => <SelectItem key={a.id} value={a.id.toString()}>{a.account_name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Membro Responsável</Label>
          <Input
            value={currentUserMember?.name || 'Carregando...'}
            disabled
            className="bg-muted"
          />
          <p className="text-xs text-muted-foreground">O membro é automaticamente associado ao usuário logado</p>
        </div>
        <div className="space-y-2">
          <Label>Empréstimo Relacionado (Opcional)</Label>
          <Select
            value={watch('related_loan')?.toString() || 'none'}
            onValueChange={(v) => setValue('related_loan', v === 'none' ? null : parseInt(v))}
            disabled={isLoading}
          >
            <SelectTrigger><SelectValue placeholder="Selecione (opcional)" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Nenhum</SelectItem>
              {eligibleLoans.map((loan) => (
                <SelectItem key={loan.id} value={loan.id.toString()}>
                  {loan.description} - Saldo: R$ {loan.remaining_balance || '0.00'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Vincule esta despesa a um empréstimo que você está pagando
          </p>
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>Cancelar</Button>
        <Button type="submit" disabled={isLoading}>{isLoading ? 'Salvando...' : expense ? 'Atualizar' : 'Criar'}</Button>
      </div>
    </form>
  );
};
