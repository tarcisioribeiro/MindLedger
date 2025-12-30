import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { authorsService } from '@/services/authors-service';
import type { Author, AuthorFormData } from '@/types';
import { Plus, Search, Edit, Trash2, BookOpen, User } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { AuthorForm } from '@/components/library/AuthorForm';

export default function Authors() {
  const [authors, setAuthors] = useState<Author[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedAuthor, setSelectedAuthor] = useState<Author | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadAuthors();
  }, []);

  const loadAuthors = async () => {
    try {
      setLoading(true);
      const data = await authorsService.getAll();
      setAuthors(data);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar autores',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedAuthor(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = (author: Author) => {
    setSelectedAuthor(author);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir autor',
      description: 'Tem certeza que deseja excluir este autor? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await authorsService.delete(id);
      toast({
        title: 'Autor excluído',
        description: 'O autor foi excluído com sucesso.',
      });
      loadAuthors();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir autor',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (data: AuthorFormData) => {
    try {
      setIsSubmitting(true);
      if (selectedAuthor) {
        await authorsService.update(selectedAuthor.id, data);
        toast({
          title: 'Autor atualizado',
          description: 'O autor foi atualizado com sucesso.',
        });
      } else {
        await authorsService.create(data);
        toast({
          title: 'Autor criado',
          description: 'O autor foi criado com sucesso.',
        });
      }
      setIsDialogOpen(false);
      loadAuthors();
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

  const filteredAuthors = authors.filter(
    (author) =>
      author.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (author.nationality?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Autores"
        description="Gerencie os autores da sua biblioteca"
        action={{
          label: 'Novo Autor',
          icon: <Plus className="h-4 w-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Buscar autores..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {filteredAuthors.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <User className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">Nenhum autor encontrado</p>
            <p className="text-sm text-muted-foreground mb-4">
              {searchTerm
                ? 'Tente ajustar sua pesquisa'
                : 'Comece adicionando seu primeiro autor'}
            </p>
            {!searchTerm && (
              <Button onClick={handleCreate}>
                <Plus className="w-4 h-4 mr-2" />
                Adicionar Autor
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredAuthors.map((author) => (
            <Card key={author.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{author.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {author.nationality_display}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEdit(author)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(author.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {author.biography && (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {author.biography}
                  </p>
                )}
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {author.books_count} {author.books_count === 1 ? 'livro' : 'livros'}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedAuthor ? 'Editar' : 'Novo'} Autor
            </DialogTitle>
            <DialogDescription>
              {selectedAuthor
                ? 'Atualize as informações do autor'
                : 'Adicione um novo autor à sua biblioteca'}
            </DialogDescription>
          </DialogHeader>
          <AuthorForm
            author={selectedAuthor}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
