import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { authorSchema, type AuthorFormData } from '@/lib/validations';
import { membersService } from '@/services/members-service';
import { formatLocalDate } from '@/lib/utils';
import { NATIONALITIES } from '@/types';
import type { Author } from '@/types';

interface AuthorFormProps {
  author?: Author;
  onSubmit: (data: AuthorFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function AuthorForm({
  author,
  onSubmit,
  onCancel,
  isLoading = false,
}: AuthorFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AuthorFormData>({
    resolver: zodResolver(authorSchema),
    defaultValues: author
      ? {
          name: author.name,
          birthday: author.birthday || '',
          death_date: author.death_date || '',
          nationality: author.nationality || 'Brazilian',
          biography: author.biography || '',
          owner: author.owner,
        }
      : {
          name: '',
          birthday: '',
          death_date: '',
          nationality: 'Brazilian',
          biography: '',
          owner: 0,
        },
  });

  // Load current user member when creating new author
  useEffect(() => {
    const loadCurrentUserMember = async () => {
      if (!author) {
        try {
          const member = await membersService.getCurrentUserMember();
          setValue('owner', member.id);
        } catch (error) {
          console.error('Erro ao carregar membro do usuário:', error);
        }
      }
    };

    loadCurrentUserMember();
  }, [author, setValue]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Nome *</Label>
          <Input
            id="name"
            {...register('name')}
            placeholder="Nome completo do autor"
          />
          {errors.name && (
            <p className="text-sm text-destructive mt-1">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="birthday">Data de Nascimento</Label>
          <DatePicker
            value={watch('birthday') && watch('birthday') !== '' ? new Date(watch('birthday')!) : undefined}
            onChange={(date) => setValue('birthday', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de nascimento"
          />
          {errors.birthday && (
            <p className="text-sm text-destructive mt-1">
              {errors.birthday.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="death_date">Data de Falecimento</Label>
          <DatePicker
            value={watch('death_date') && watch('death_date') !== '' ? new Date(watch('death_date')!) : undefined}
            onChange={(date) => setValue('death_date', date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data de falecimento"
          />
          {errors.death_date && (
            <p className="text-sm text-destructive mt-1">
              {errors.death_date.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="nationality">Nacionalidade *</Label>
          <Select
            value={watch('nationality')}
            onValueChange={(value) => setValue('nationality', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {NATIONALITIES.map((nat) => (
                <SelectItem key={nat.value} value={nat.value}>
                  {nat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.nationality && (
            <p className="text-sm text-destructive mt-1">
              {errors.nationality.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="biography">Biografia</Label>
          <Textarea
            id="biography"
            {...register('biography')}
            placeholder="Informações sobre o autor..."
            rows={4}
          />
          {errors.biography && (
            <p className="text-sm text-destructive mt-1">
              {errors.biography.message}
            </p>
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
