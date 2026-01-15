import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Eye, Download, FileText, File, Archive as ArchiveIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ArchiveForm } from '@/components/security/ArchiveForm';
import { archivesService } from '@/services/archives-service';
import { membersService } from '@/services/members-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { formatDate } from '@/lib/formatters';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import type { Archive, ArchiveFormData, Member } from '@/types';

const ARCHIVE_CATEGORIES: Record<string, string> = {
  personal: 'Pessoal',
  financial: 'Financeiro',
  legal: 'Jurídico',
  medical: 'Médico',
  tax: 'Fiscal',
  work: 'Trabalho',
  other: 'Outro',
};

const ARCHIVE_TYPES: Record<string, string> = {
  text: 'Texto',
  pdf: 'PDF',
  image: 'Imagem',
  document: 'Documento',
  other: 'Outro',
};

export default function Archives() {
  const [archives, setArchives] = useState<Archive[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isContentDialogOpen, setIsContentDialogOpen] = useState(false);
  const [selectedArchive, setSelectedArchive] = useState<Archive | undefined>();
  const [revealedContent, setRevealedContent] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRevealing, setIsRevealing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [archivesData, membersData] = await Promise.all([
        archivesService.getAll(),
        membersService.getAll(),
      ]);
      setArchives(archivesData);
      setMembers(membersData);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar dados',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedArchive(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = async (archive: Archive) => {
    // Se for arquivo de texto, carregar o conteúdo descriptografado
    if (archive.archive_type === 'text' && archive.has_text) {
      try {
        const data = await archivesService.reveal(archive.id);
        // Adiciona o texto descriptografado ao objeto archive
        setSelectedArchive({ ...archive, text_content: data.text_content });
      } catch (error: any) {
        toast({
          title: 'Erro ao carregar conteúdo',
          description: error.message,
          variant: 'destructive',
        });
        // Ainda abre o diálogo, mas sem o conteúdo
        setSelectedArchive(archive);
      }
    } else {
      setSelectedArchive(archive);
    }
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir arquivo',
      description:
        'Tem certeza que deseja excluir este arquivo confidencial? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await archivesService.delete(id);
      toast({
        title: 'Arquivo excluído',
        description: 'O arquivo foi excluído com sucesso.',
      });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleRevealContent = async (archive: Archive) => {
    if (archive.archive_type !== 'text') {
      toast({
        title: 'Ação não disponível',
        description: 'Apenas arquivos de texto podem ser visualizados diretamente.',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsRevealing(true);
      setSelectedArchive(archive);
      const data = await archivesService.reveal(archive.id);

      if (!data.text_content && data.text_content !== '') {
        toast({
          title: 'Conteúdo vazio',
          description: 'Este arquivo não possui conteúdo de texto armazenado.',
          variant: 'destructive',
        });
        return;
      }

      setRevealedContent(data.text_content || '');
      setIsContentDialogOpen(true);
      toast({
        title: 'Conteúdo revelado',
        description: 'O conteúdo do arquivo foi descriptografado com sucesso.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao revelar conteúdo',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsRevealing(false);
    }
  };

  const handleDownload = async (archive: Archive) => {
    if (archive.archive_type === 'text') {
      // Para texto, revelar conteúdo ao invés de download
      handleRevealContent(archive);
      return;
    }

    try {
      const blob = await archivesService.download(archive.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = archive.file_name || `${archive.title}.bin`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast({
        title: 'Download iniciado',
        description: 'O arquivo está sendo baixado.',
      });
    } catch (error: any) {
      toast({
        title: 'Erro ao baixar arquivo',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (data: ArchiveFormData & { file?: File }) => {
    try {
      setIsSubmitting(true);
      if (selectedArchive) {
        await archivesService.update(selectedArchive.id, data);
        toast({
          title: 'Arquivo atualizado',
          description: 'O arquivo foi atualizado com sucesso.',
        });
      } else {
        await archivesService.create(data);
        toast({
          title: 'Arquivo criado',
          description: 'O arquivo foi criado e criptografado com sucesso.',
        });
      }
      setIsDialogOpen(false);
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao salvar',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredArchives = archives.filter(
    (arc) =>
      arc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (arc.tags && arc.tags.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (arc.file_name && arc.file_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const columns: Column<Archive>[] = [
    {
      key: 'title',
      label: 'Título',
      render: (arc) => (
        <div className="flex items-center gap-2">
          {arc.archive_type === 'text' ? (
            <FileText className="w-4 h-4 text-muted-foreground" />
          ) : (
            <File className="w-4 h-4 text-muted-foreground" />
          )}
          <span className="font-medium">{arc.title}</span>
        </div>
      ),
    },
    {
      key: 'category',
      label: 'Categoria',
      render: (arc) => <Badge>{ARCHIVE_CATEGORIES[arc.category]}</Badge>,
    },
    {
      key: 'type',
      label: 'Tipo',
      render: (arc) => (
        <Badge variant="outline">{ARCHIVE_TYPES[arc.archive_type]}</Badge>
      ),
    },
    {
      key: 'file_size',
      label: 'Tamanho',
      align: 'right',
      render: (arc) => (
        <span className="text-sm text-muted-foreground">
          {formatFileSize(arc.file_size)}
        </span>
      ),
    },
    {
      key: 'tags',
      label: 'Tags',
      render: (arc) => (
        <div className="flex flex-wrap gap-1">
          {arc.tags?.split(',').slice(0, 3).map((tag, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs">
              {tag.trim()}
            </Badge>
          ))}
          {arc.tags && arc.tags.split(',').length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{arc.tags.split(',').length - 3}
            </Badge>
          )}
        </div>
      ),
    },
    {
      key: 'created_at',
      label: 'Criado em',
      render: (arc) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(arc.created_at, 'dd/MM/yyyy')}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Arquivos Confidenciais"
        description="Armazene documentos e textos de forma criptografada"
        icon={<ArchiveIcon />}
        action={{
          label: 'Novo Arquivo',
          icon: <Plus className="h-4 w-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="flex gap-4">
        <Input
          placeholder="Buscar arquivos..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <DataTable
        data={filteredArchives}
        columns={columns}
        keyExtractor={(arc) => arc.id}
        isLoading={isLoading}
        emptyState={{
          message: 'Nenhum arquivo confidencial encontrado.',
        }}
        actions={(arc) => (
          <div className="flex items-center justify-end gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                arc.archive_type === 'text'
                  ? handleRevealContent(arc)
                  : handleDownload(arc)
              }
              disabled={isRevealing}
            >
              {arc.archive_type === 'text' ? (
                <>
                  <Eye className="h-3 w-3 mr-1" />
                  Ver
                </>
              ) : (
                <>
                  <Download className="h-3 w-3 mr-1" />
                  Baixar
                </>
              )}
            </Button>
            <Button variant="ghost" size="icon" onClick={() => handleEdit(arc)}>
              <Pencil className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => handleDelete(arc.id)}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        )}
      />

      {/* Dialog para criar/editar arquivo */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle>
              {selectedArchive ? 'Editar' : 'Novo'} Arquivo Confidencial
            </DialogTitle>
            <DialogDescription>
              {selectedArchive
                ? 'Atualize as informações do arquivo'
                : 'Adicione um novo arquivo ao cofre criptografado'}
            </DialogDescription>
          </DialogHeader>
          <ArchiveForm
            archive={selectedArchive}
            members={members}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog para visualizar conteúdo de texto */}
      <Dialog open={isContentDialogOpen} onOpenChange={setIsContentDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle>{selectedArchive?.title}</DialogTitle>
            <DialogDescription>
              Conteúdo descriptografado - {ARCHIVE_CATEGORIES[selectedArchive?.category || 'other']}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={revealedContent}
              readOnly
              rows={20}
              className="font-mono text-sm"
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(revealedContent);
                  toast({
                    title: 'Copiado!',
                    description: 'Conteúdo copiado para a área de transferência.',
                  });
                }}
              >
                Copiar
              </Button>
              <Button onClick={() => setIsContentDialogOpen(false)}>Fechar</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
