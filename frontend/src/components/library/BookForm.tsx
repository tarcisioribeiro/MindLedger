import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { bookSchema, type BookFormData } from '@/lib/validations';
import {
  BOOK_LANGUAGES,
  BOOK_GENRES,
  LITERARY_TYPES,
  MEDIA_TYPES,
  READ_STATUS,
} from '@/types';
import type { Book, Author, Publisher } from '@/types';
import { useState } from 'react';

interface BookFormProps {
  book?: Book;
  authors: Author[];
  publishers: Publisher[];
  onSubmit: (data: BookFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function BookForm({
  book,
  authors,
  publishers,
  onSubmit,
  onCancel,
  isLoading = false,
}: BookFormProps) {
  const [selectedAuthors, setSelectedAuthors] = useState<number[]>(
    book?.authors || []
  );

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<BookFormData>({
    resolver: zodResolver(bookSchema),
    defaultValues: book
      ? {
          title: book.title,
          authors: book.authors,
          pages: book.pages,
          publisher: book.publisher,
          language: book.language,
          genre: book.genre,
          literarytype: book.literarytype,
          publish_date: book.publish_date || '',
          synopsis: book.synopsis,
          edition: book.edition,
          media_type: book.media_type || '',
          rating: book.rating,
          read_status: book.read_status,
          owner: book.owner,
        }
      : {
          title: '',
          authors: [],
          pages: 0,
          publisher: 0,
          language: 'Por',
          genre: 'Fiction',
          literarytype: 'book',
          publish_date: '',
          synopsis: '',
          edition: '1ª',
          media_type: '',
          rating: 0,
          read_status: 'to_read',
          owner: 0,
        },
  });

  const handleAuthorToggle = (authorId: number) => {
    const newAuthors = selectedAuthors.includes(authorId)
      ? selectedAuthors.filter((id) => id !== authorId)
      : [...selectedAuthors, authorId];
    setSelectedAuthors(newAuthors);
    setValue('authors', newAuthors);
  };

  const handleRemoveAuthor = (authorId: number) => {
    const newAuthors = selectedAuthors.filter((id) => id !== authorId);
    setSelectedAuthors(newAuthors);
    setValue('authors', newAuthors);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="title">Título *</Label>
          <Input
            id="title"
            {...register('title')}
            placeholder="Título do livro"
          />
          {errors.title && (
            <p className="text-sm text-destructive mt-1">{errors.title.message}</p>
          )}
        </div>

        <div className="col-span-2">
          <Label>Autores *</Label>
          <Select onValueChange={(value) => handleAuthorToggle(parseInt(value))}>
            <SelectTrigger>
              <SelectValue placeholder="Selecione os autores" />
            </SelectTrigger>
            <SelectContent>
              {authors.map((author) => (
                <SelectItem key={author.id} value={author.id.toString()}>
                  {author.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedAuthors.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {selectedAuthors.map((authorId) => {
                const author = authors.find((a) => a.id === authorId);
                return author ? (
                  <Badge key={authorId} variant="secondary">
                    {author.name}
                    <button
                      type="button"
                      onClick={() => handleRemoveAuthor(authorId)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ) : null;
              })}
            </div>
          )}
          {errors.authors && (
            <p className="text-sm text-destructive mt-1">{errors.authors.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="pages">Páginas *</Label>
          <Input
            id="pages"
            type="number"
            min="1"
            {...register('pages', {
              setValueAs: (value) => (value === '' ? 0 : parseInt(value)),
            })}
          />
          {errors.pages && (
            <p className="text-sm text-destructive mt-1">{errors.pages.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="publisher">Editora *</Label>
          <Select
            value={watch('publisher').toString()}
            onValueChange={(value) => setValue('publisher', parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione a editora" />
            </SelectTrigger>
            <SelectContent>
              {publishers.map((publisher) => (
                <SelectItem key={publisher.id} value={publisher.id.toString()}>
                  {publisher.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.publisher && (
            <p className="text-sm text-destructive mt-1">
              {errors.publisher.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="language">Idioma *</Label>
          <Select
            value={watch('language')}
            onValueChange={(value) => setValue('language', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {BOOK_LANGUAGES.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.language && (
            <p className="text-sm text-destructive mt-1">
              {errors.language.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="genre">Gênero *</Label>
          <Select
            value={watch('genre')}
            onValueChange={(value) => setValue('genre', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {BOOK_GENRES.map((genre) => (
                <SelectItem key={genre.value} value={genre.value}>
                  {genre.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.genre && (
            <p className="text-sm text-destructive mt-1">{errors.genre.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="literarytype">Tipo Literário *</Label>
          <Select
            value={watch('literarytype')}
            onValueChange={(value) => setValue('literarytype', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LITERARY_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.literarytype && (
            <p className="text-sm text-destructive mt-1">
              {errors.literarytype.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="media_type">Tipo de Mídia</Label>
          <Select
            value={watch('media_type') || ''}
            onValueChange={(value) => setValue('media_type', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Nenhum</SelectItem>
              {MEDIA_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.media_type && (
            <p className="text-sm text-destructive mt-1">
              {errors.media_type.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="edition">Edição *</Label>
          <Input
            id="edition"
            {...register('edition')}
            placeholder="Ex: 1ª edição"
          />
          {errors.edition && (
            <p className="text-sm text-destructive mt-1">{errors.edition.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="publish_date">Data de Publicação</Label>
          <Input
            id="publish_date"
            type="date"
            {...register('publish_date')}
          />
          {errors.publish_date && (
            <p className="text-sm text-destructive mt-1">
              {errors.publish_date.message}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="rating">Avaliação (0-5) *</Label>
          <Input
            id="rating"
            type="number"
            min="0"
            max="5"
            {...register('rating', {
              setValueAs: (value) => (value === '' ? 0 : parseInt(value)),
            })}
          />
          {errors.rating && (
            <p className="text-sm text-destructive mt-1">{errors.rating.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="read_status">Status de Leitura *</Label>
          <Select
            value={watch('read_status')}
            onValueChange={(value) => setValue('read_status', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {READ_STATUS.map((status) => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.read_status && (
            <p className="text-sm text-destructive mt-1">
              {errors.read_status.message}
            </p>
          )}
        </div>

        <div className="col-span-2">
          <Label htmlFor="synopsis">Sinopse *</Label>
          <Textarea
            id="synopsis"
            {...register('synopsis')}
            placeholder="Descrição do livro..."
            rows={5}
          />
          {errors.synopsis && (
            <p className="text-sm text-destructive mt-1">
              {errors.synopsis.message}
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
