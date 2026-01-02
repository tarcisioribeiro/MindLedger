import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TRANSLATIONS } from '@/config/constants';
import { accountSchema, type AccountFormData } from '@/lib/validations';
import { membersService } from '@/services/members-service';
import type { Account } from '@/types';

interface AccountFormProps {
  account?: Account;
  members: Array<{ id: number; name: string }>;
  onSubmit: (data: AccountFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const AccountForm: React.FC<AccountFormProps> = ({
  account,
  members,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [currentUserMemberId, setCurrentUserMemberId] = useState<number | null>(null);
  const [isLoadingMember, setIsLoadingMember] = useState(true);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<AccountFormData>({
    resolver: zodResolver(accountSchema),
    defaultValues: account
      ? {
          account_name: account.account_name,
          account_type: account.account_type as AccountFormData['account_type'],
          institution: account.institution as AccountFormData['institution'],
          account_number: '', // Can't show encrypted number
          balance: parseFloat(account.balance),
          owner: account.owner,
        }
      : {
          account_name: '',
          account_type: 'CC',
          institution: 'NUB',
          account_number: '',
          balance: 0,
          owner: 0,
        },
  });

  // Buscar o membro do usuário logado ao criar nova conta
  useEffect(() => {
    const loadCurrentUserMember = async () => {
      if (!account) { // Apenas ao criar nova conta
        try {
          setIsLoadingMember(true);
          const member = await membersService.getCurrentUserMember();
          setCurrentUserMemberId(member.id);
          setValue('owner', member.id);
        } catch (error) {
          console.error('Erro ao carregar membro do usuário:', error);
        } finally {
          setIsLoadingMember(false);
        }
      } else {
        setIsLoadingMember(false);
      }
    };

    loadCurrentUserMember();
  }, [account, setValue]);

  const accountType = watch('account_type') || 'CC';
  const institution = watch('institution') || 'NUB';
  const owner = watch('owner');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account_type">Tipo de Conta *</Label>
          <Select
            value={accountType}
            onValueChange={(value) => setValue('account_type', value as AccountFormData['account_type'])}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione o tipo" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.accountTypes).map(([key, value]) => (
                <SelectItem key={key} value={key}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.account_type && (
            <p className="text-sm text-destructive">{errors.account_type.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="institution">Instituição *</Label>
          <Select
            value={institution}
            onValueChange={(value) => setValue('institution', value as AccountFormData['institution'])}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione a instituição" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(TRANSLATIONS.institutions).map(([key, value]) => (
                <SelectItem key={key} value={key}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.institution && (
            <p className="text-sm text-destructive">{errors.institution.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="account_name">Nome da Conta *</Label>
          <Input
            id="account_name"
            {...register('account_name')}
            placeholder="Ex: Conta Corrente Principal"
            disabled={isLoading}
          />
          {errors.account_name && (
            <p className="text-sm text-destructive">{errors.account_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="account_number">Número da Conta *</Label>
          <Input
            id="account_number"
            {...register('account_number')}
            placeholder="Ex: 12345-6"
            disabled={isLoading}
          />
          {errors.account_number && (
            <p className="text-sm text-destructive">{errors.account_number.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="balance">Saldo Inicial</Label>
          <Input
            id="balance"
            type="number"
            step="0.01"
            {...register('balance', { valueAsNumber: true })}
            placeholder="0.00"
            disabled={isLoading}
          />
          {errors.balance && (
            <p className="text-sm text-destructive">{errors.balance.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="owner">Proprietário *</Label>
          {!account ? (
            // Ao criar nova conta: campo somente leitura com o membro do usuário
            <Input
              id="owner"
              value={isLoadingMember ? 'Carregando...' : members.find(m => m.id === currentUserMemberId)?.name || 'Carregando...'}
              disabled
              className="bg-muted"
            />
          ) : (
            // Ao editar conta: permite alterar o proprietário
            <Select
              value={owner?.toString() || ''}
              onValueChange={(value) => setValue('owner', parseInt(value, 10))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o proprietário" />
              </SelectTrigger>
              <SelectContent>
                {members.map((member) => (
                  <SelectItem key={member.id} value={member.id.toString()}>
                    {member.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {errors.owner && (
            <p className="text-sm text-destructive">{errors.owner.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Salvando...' : account ? 'Atualizar' : 'Criar'}
        </Button>
      </div>
    </form>
  );
};
