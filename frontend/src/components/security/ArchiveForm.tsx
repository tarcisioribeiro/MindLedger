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

const FILE_TYPES_ACCEPT = [
  '.txt',
  '.pdf',
  '.doc',
  '.docx',
  '.xls',
  '.xlsx',
  '.ppt',
  '.pptx',
  '.json',
  '.xml',
  '.csv',
  '.jpg',
  '.jpeg',
  '.png',
  '.gif',
  '.svg',
  '.zip',
  '.rar',
  '.7z',
].join(',');

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
          archive_type: 'file' as any,
          text_content: archive.text_content || '',
          notes: archive.notes || '',
          tags: archive.tags || '',
          owner: archive.owner,
        }
      : {
          title: '',
          category: 'personal' as const,
          archive_type: 'file' as const,
          text_content: '',
          notes: '',
          tags: '',
          owner: members[0]?.id || 0,
        },
  });

  const handleFormSubmit = handleSubmit((data: ArchiveFormData) => {
    const fileInput = document.getElementById('file') as HTMLInputElement;
    const file = fileInput?.files?.[0];

    if (!archive && !file) {
      // Validação de arquivo para novos registros
      alert('Por favor, selecione um arquivo.');
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
                  {member.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.owner && (
            <p className="text-sm text-destructive mt-1">{errors.owner.message}</p>
          )}
        </div>

        <div className="col-span-2">
          <Label htmlFor="file">
            Arquivo {!archive && '*'}
          </Label>
          <Input
            id="file"
            type="file"
            accept={FILE_TYPES_ACCEPT}
          />
          {archive ? (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              Deixe vazio para manter o arquivo atual. Upload de novo arquivo substituirá o existente.
            </p>
          ) : (
            <p className="text-xs text-muted-foreground mt-1">
              O arquivo será criptografado antes de ser armazenado. Tipos suportados: PDF, Word, Excel, PowerPoint, JSON, XML, CSV, imagens, compactados, etc.
            </p>
          )}
        </div>

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
