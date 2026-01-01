import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { storedAccountSchema, type StoredBankAccountFormData } from '@/lib/validations';
import type { StoredBankAccount, Account, Member } from '@/types';

const ACCOUNT_TYPES = [
  { value: 'CC', label: 'Conta Corrente' },
  { value: 'CS', label: 'Conta Salário' },
  { value: 'CP', label: 'Conta Poupança' },
  { value: 'CI', label: 'Conta Investimento' },
  { value: 'OTHER', label: 'Outro' },
];

interface StoredAccountFormProps {
  account?: StoredBankAccount;
  financeAccounts?: Account[];
  members: Member[];
  onSubmit: (data: StoredBankAccountFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function StoredAccountForm({
  account,
  financeAccounts = [],
  members,
  onSubmit,
  onCancel,
  isLoading = false,
}: StoredAccountFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [showSecondPassword, setShowSecondPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<StoredBankAccountFormData>({
    resolver: zodResolver(storedAccountSchema),
    defaultValues: account
      ? {
          name: account.name,
          institution_name: account.institution_name,
          account_type: account.account_type as any,
          account_number: account.account_number || '',
          agency: account.agency || '',
          password: '', // Não carregar senha por segurança
          digital_password: '',
          notes: account.notes || '',
          owner: account.owner,
          finance_account: account.finance_account || undefined,
        }
      : {
          name: '',
          institution_name: '',
          account_type: 'CC',
          account_number: '',
          agency: '',
          password: '',
          digital_password: '',
          notes: '',
          owner: members[0]?.id || 0,
          finance_account: undefined,
        },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="name">Nome *</Label>
          <Input
            id="name"
            {...register('name')}
            placeholder="Ex: Conta Banco X"
          />
          {errors.name && (
            <p className="text-sm text-destructive mt-1">{errors.name.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="institution_name">Instituição *</Label>
          <Input
            id="institution_name"
            {...register('institution_name')}
            placeholder="Nome do banco"
          />
          {errors.institution_name && (
            <p className="text-sm text-destructive mt-1">
              {errors.institution_name.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="account_type">Tipo de Conta *</Label>
          <Select
            value={watch('account_type')}
            onValueChange={(value) => setValue('account_type', value as any)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACCOUNT_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.account_type && (
            <p className="text-sm text-destructive mt-1">
              {errors.account_type.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="account_number">Número da Conta *</Label>
          <Input
            id="account_number"
            {...register('account_number')}
            placeholder="Ex: 12345-6"
          />
          {errors.account_number && (
            <p className="text-sm text-destructive mt-1">
              {errors.account_number.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="agency">Agência</Label>
          <Input
            id="agency"
            {...register('agency')}
            placeholder="Ex: 1234"
          />
          {errors.agency && (
            <p className="text-sm text-destructive mt-1">{errors.agency.message}</p>
          )}
        </div>

        <div className="col-span-2">
          <Label htmlFor="password">Senha de Acesso</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              {...register('password')}
              placeholder={account ? 'Deixe vazio para manter a atual' : 'Senha do app/site'}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
          {errors.password && (
            <p className="text-sm text-destructive mt-1">{errors.password.message}</p>
          )}
          {account && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              Deixe vazio para manter a senha atual (criptografada)
            </p>
          )}
        </div>

        <div className="col-span-2">
          <Label htmlFor="digital_password">Senha Digital (Cartão/Token)</Label>
          <div className="relative">
            <Input
              id="digital_password"
              type={showSecondPassword ? 'text' : 'password'}
              {...register('digital_password')}
              placeholder={account ? 'Deixe vazio para manter a atual' : 'Senha do cartão'}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3"
              onClick={() => setShowSecondPassword(!showSecondPassword)}
            >
              {showSecondPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
          {errors.digital_password && (
            <p className="text-sm text-destructive mt-1">{errors.digital_password.message}</p>
          )}
        </div>

        <div className="col-span-2">
          <Label htmlFor="owner">Proprietário *</Label>
          <Select
            value={watch('owner')?.toString()}
            onValueChange={(value) => setValue('owner', parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {members.map((member) => (
                <SelectItem key={member.id} value={member.id.toString()}>
                  {member.member_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.owner && (
            <p className="text-sm text-destructive mt-1">{errors.owner.message}</p>
          )}
        </div>

        {financeAccounts.length > 0 && (
          <div className="col-span-2">
            <Label htmlFor="finance_account">Conta Financeira Vinculada (Opcional)</Label>
            <Select
              value={watch('finance_account')?.toString() || 'none'}
              onValueChange={(value) =>
                setValue('finance_account', value === 'none' ? undefined : parseInt(value))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Nenhuma" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Nenhuma</SelectItem>
                {financeAccounts.map((acc) => (
                  <SelectItem key={acc.id} value={acc.id.toString()}>
                    {acc.account_name} - {acc.institution}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground mt-1">
              Vincule esta conta armazenada a uma conta do módulo financeiro
            </p>
          </div>
        )}

        <div className="col-span-2">
          <Label htmlFor="notes">Observações</Label>
          <Textarea
            id="notes"
            {...register('notes')}
            placeholder="Notas adicionais sobre a conta..."
            rows={3}
          />
          {errors.notes && (
            <p className="text-sm text-destructive mt-1">{errors.notes.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Salvando...
            </>
          ) : (
            'Salvar'
          )}
        </Button>
      </div>
    </form>
  );
}
