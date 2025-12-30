import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { archiveSchema, type ArchiveFormData } from '@/lib/validations';
import type { Archive, Member } from '@/types';

const ARCHIVE_CATEGORIES = [
  { value: 'personal', label: 'Pessoal' },
  { value: 'financial', label: 'Financeiro' },
  { value: 'legal', label: 'Jurídico' },
  { value: 'medical', label: 'Médico' },
  { value: 'tax', label: 'Fiscal' },
  { value: 'work', label: 'Trabalho' },
  { value: 'other', label: 'Outro' },
];

const ARCHIVE_TYPES = [
  { value: 'text', label: 'Texto' },
  { value: 'pdf', label: 'PDF' },
  { value: 'image', label: 'Imagem' },
  { value: 'document', label: 'Documento' },
  { value: 'other', label: 'Outro' },
];

interface ArchiveFormProps {
  archive?: Archive;
  members: Member[];
  onSubmit: (data: ArchiveFormData & { file?: File }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ArchiveForm({
  archive,
  members,
  onSubmit,
  onCancel,
  isLoading = false,
}: ArchiveFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ArchiveFormData>({
    resolver: zodResolver(archiveSchema),
    defaultValues: archive
      ? {
          title: archive.title,
          category: archive.category as any,
          archive_type: archive.archive_type as any,
          text_content: archive.text_content || '',
          notes: archive.notes || '',
          tags: archive.tags || '',
          owner: archive.owner,
        }
      : {
          title: '',
          category: 'personal' as const,
          archive_type: 'text' as const,
          text_content: '',
          notes: '',
          tags: '',
          owner: members[0]?.id || 0,
        },
  });

  const archiveType = watch('archive_type');

  const handleFormSubmit = handleSubmit((data: ArchiveFormData) => {
    const fileInput = document.getElementById('file') as HTMLInputElement;
    const file = fileInput?.files?.[0];

    if (archiveType !== 'text' && !archive && !file) {
      // Validação de arquivo para novos arquivos não-texto
      return;
    }

    onSubmit({ ...data, file });
  });

  return (
    <form onSubmit={handleFormSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="title">Título *</Label>
          <Input
            id="title"
            {...register('title')}
            placeholder="Nome descritivo do arquivo"
          />
          {errors.title && (
            <p className="text-sm text-destructive mt-1">{errors.title.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="category">Categoria *</Label>
          <Select
            value={watch('category')}
            onValueChange={(value) => setValue('category', value as any)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ARCHIVE_CATEGORIES.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.category && (
            <p className="text-sm text-destructive mt-1">{errors.category.message}</p>
          )}
        </div>

        <div>
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

        <div className="col-span-2">
          <Label>Tipo de Arquivo *</Label>
          <RadioGroup
            value={watch('archive_type')}
            onValueChange={(value: string) => setValue('archive_type', value as any)}
            className="grid grid-cols-3 gap-4 mt-2"
          >
            {ARCHIVE_TYPES.map((type) => (
              <div key={type.value} className="flex items-center space-x-2">
                <RadioGroupItem value={type.value} id={type.value} />
                <Label
                  htmlFor={type.value}
                  className="font-normal cursor-pointer"
                >
                  {type.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
          {errors.archive_type && (
            <p className="text-sm text-destructive mt-1">
              {errors.archive_type.message}
            </p>
          )}
        </div>

        {archiveType === 'text' ? (
          <div className="col-span-2">
            <Label htmlFor="text_content">Conteúdo de Texto</Label>
            <Textarea
              id="text_content"
              {...register('text_content')}
              placeholder="Digite o conteúdo que será criptografado..."
              rows={10}
              className="font-mono text-sm"
            />
            {errors.text_content && (
              <p className="text-sm text-destructive mt-1">
                {errors.text_content.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              O texto será criptografado antes de ser armazenado
            </p>
          </div>
        ) : (
          <div className="col-span-2">
            <Label htmlFor="file">
              Arquivo {!archive && '*'}
            </Label>
            <Input id="file" type="file" />
            {archive ? (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Deixe vazio para manter o arquivo atual. Upload de novo arquivo substituirá o existente.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground mt-1">
                O arquivo será criptografado antes de ser armazenado
              </p>
            )}
          </div>
        )}

        <div className="col-span-2">
          <Label htmlFor="tags">Tags</Label>
          <Input
            id="tags"
            {...register('tags')}
            placeholder="tag1, tag2, tag3"
          />
          {errors.tags && (
            <p className="text-sm text-destructive mt-1">{errors.tags.message}</p>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Separe as tags com vírgulas
          </p>
        </div>

        <div className="col-span-2">
          <Label htmlFor="notes">Observações</Label>
          <Textarea
            id="notes"
            {...register('notes')}
            placeholder="Notas adicionais sobre o arquivo..."
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
