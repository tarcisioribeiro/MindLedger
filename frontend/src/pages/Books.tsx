import { useState, useEffect } from 'react';
import { Plus, BookOpen, TrendingUp, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { booksService } from '@/services/books-service';
import { authorsService } from '@/services/authors-service';
import { publishersService } from '@/services/publishers-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import { formatDate } from '@/lib/formatters';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { BookForm } from '@/components/library/BookForm';
import type { Book, BookFormData, Author, Publisher } from '@/types';

export default function Books() {
  const [books, setBooks] = useState<Book[]>([]);
  const [authors, setAuthors] = useState<Author[]>([]);
  const [publishers, setPublishers] = useState<Publisher[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [booksData, authorsData, publishersData] = await Promise.all([
        booksService.getAll(),
        authorsService.getAll(),
        publishersService.getAll(),
      ]);
      setBooks(booksData);
      setAuthors(authorsData);
      setPublishers(publishersData);
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
    setSelectedBook(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = (book: Book) => {
    setSelectedBook(book);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir livro',
      description: 'Tem certeza que deseja excluir este livro? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await booksService.delete(id);
      toast({
        title: 'Livro excluído',
        description: 'O livro foi excluído com sucesso.',
      });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir livro',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (data: BookFormData) => {
    try {
      setIsSubmitting(true);
      if (selectedBook) {
        await booksService.update(selectedBook.id, data);
        toast({
          title: 'Livro atualizado',
          description: 'O livro foi atualizado com sucesso.',
        });
      } else {
        await booksService.create(data);
        toast({
          title: 'Livro criado',
          description: 'O livro foi criado com sucesso.',
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

  const filteredBooks = books.filter(
    (book) =>
      book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      book.authors_names.some((author) =>
        author.toLowerCase().includes(searchTerm.toLowerCase())
      ) ||
      book.publisher_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'read':
        return 'bg-green-500';
      case 'reading':
        return 'bg-blue-500';
      case 'to_read':
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Biblioteca"
        description="Gerencie sua coleção de livros"
        action={{
          label: 'Novo Livro',
          icon: <Plus className="h-4 w-4" />,
          onClick: handleCreate,
        }}
      />

      <div className="flex gap-4">
        <Input
          placeholder="Buscar livros, autores ou editoras..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredBooks.map((book) => (
          <Card key={book.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <CardTitle className="text-lg line-clamp-2">
                    {book.title}
                  </CardTitle>
                  <CardDescription className="line-clamp-1">
                    {book.authors_names.join(', ')}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    className={getStatusColor(book.read_status)}
                    variant="default"
                  >
                    {book.read_status_display}
                  </Badge>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleEdit(book)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleDelete(book.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {book.publisher_name}
                  </span>
                  <Badge variant="secondary">{book.genre_display}</Badge>
                </div>

                <div className="flex items-center gap-2 text-sm">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {book.pages} páginas
                  </span>
                  {book.media_type_display && (
                    <>
                      <span className="text-muted-foreground">•</span>
                      <span className="text-muted-foreground">
                        {book.media_type_display}
                      </span>
                    </>
                  )}
                </div>

                {book.reading_progress > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        Progresso
                      </span>
                      <span className="font-medium">
                        {book.reading_progress}%
                      </span>
                    </div>
                    <Progress value={book.reading_progress} className="h-2" />
                    <p className="text-xs text-muted-foreground">
                      {book.total_pages_read} de {book.pages} páginas lidas
                    </p>
                  </div>
                )}

                {book.has_summary && (
                  <Badge variant="outline" className="w-full justify-center">
                    ✓ Possui resumo
                  </Badge>
                )}

                <div className="text-xs text-muted-foreground pt-2">
                  Adicionado em {formatDate(book.created_at, 'dd/MM/yyyy')}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredBooks.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Nenhum livro encontrado.</p>
          <Button className="mt-4" onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Adicionar primeiro livro
          </Button>
        </div>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedBook ? 'Editar' : 'Novo'} Livro
            </DialogTitle>
            <DialogDescription>
              {selectedBook
                ? 'Atualize as informações do livro'
                : 'Adicione um novo livro à sua biblioteca'}
            </DialogDescription>
          </DialogHeader>
          <BookForm
            book={selectedBook}
            authors={authors}
            publishers={publishers}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
