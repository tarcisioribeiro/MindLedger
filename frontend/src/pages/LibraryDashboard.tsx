import { useState, useEffect } from 'react';
import { Library, BookOpen, User, Building2, FileText, BookMarked, BookCheck, Star, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { libraryDashboardService, type LibraryDashboardStats } from '@/services/library-dashboard-service';
import { useToast } from '@/hooks/use-toast';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, LineChart, Line, Legend } from 'recharts';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useChartColors } from '@/lib/chart-colors';

export default function LibraryDashboard() {
  const [stats, setStats] = useState<LibraryDashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await libraryDashboardService.getStats();
      setStats(data);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar dados',
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const COLORS = useChartColors();

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating
                ? 'fill-warning text-warning'
                : 'fill-muted text-muted'
            }`}
          />
        ))}
      </div>
    );
  };

  if (isLoading) {
    return <LoadingState fullScreen />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard de Leitura"
        description="Acompanhe seu progresso e estatísticas de leitura"
        icon={<Library />}
      />

      {/* Métricas Principais - Grid 4 colunas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Livros</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_books || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_books === 1 ? 'livro cadastrado' : 'livros cadastrados'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Autores</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_authors || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_authors === 1 ? 'autor' : 'autores'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Editoras</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_publishers || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.total_publishers === 1 ? 'editora' : 'editoras'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Páginas Lidas</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_pages_read || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Média: {stats?.average_rating?.toFixed(1) || 0} ★
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Progresso de Leitura - Grid 3 colunas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lendo</CardTitle>
            <BookMarked className="h-4 w-4 text-info" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-info">
              {stats?.books_reading || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.books_reading === 1 ? 'livro em andamento' : 'livros em andamento'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Para Ler</CardTitle>
            <BookOpen className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">
              {stats?.books_to_read || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.books_to_read === 1 ? 'livro na fila' : 'livros na fila'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lidos</CardTitle>
            <BookCheck className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">
              {stats?.books_read || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats?.books_read === 1 ? 'livro completo' : 'livros completos'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Novas Estatísticas - Grid 4 colunas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Tempo Total de Leitura */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tempo de Leitura</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_reading_time_hours || 0}h</div>
            <p className="text-xs text-muted-foreground mt-1">
              Tempo total registrado
            </p>
          </CardContent>
        </Card>

        {/* Card 2: Média de Páginas por Livro */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Média por Livro</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.average_pages_per_book?.toFixed(0) || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Páginas por livro
            </p>
          </CardContent>
        </Card>

        {/* Card 3: Autor Mais Lido */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Autor Mais Lido</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {stats?.most_read_author ? (
              <>
                <div className="text-lg font-bold truncate" title={stats.most_read_author.name}>
                  {stats.most_read_author.name}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.most_read_author.books_count} {stats.most_read_author.books_count === 1 ? 'livro lido' : 'livros lidos'}
                </p>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Nenhum livro lido</div>
            )}
          </CardContent>
        </Card>

        {/* Card 4: Editora Mais Lida */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Editora Mais Lida</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {stats?.most_read_publisher ? (
              <>
                <div className="text-lg font-bold truncate" title={stats.most_read_publisher.name}>
                  {stats.most_read_publisher.name}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.most_read_publisher.books_count} {stats.most_read_publisher.books_count === 1 ? 'livro lido' : 'livros lidos'}
                </p>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Nenhum livro lido</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Livros por Gênero */}
        <Card>
          <CardHeader>
            <CardTitle>Livros por Gênero (Top 5)</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição por gênero literário</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.books_by_genre.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum livro cadastrado
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.books_by_genre} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="genre_display" type="category" width={120} />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'livro' : 'livros'}`, 'Quantidade']}
                    />
                    <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                      {stats.books_by_genre.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.books_by_genre.map((genre, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>{genre.genre_display}</span>
                      </div>
                      <span className="font-semibold">
                        {genre.count} {genre.count === 1 ? 'livro' : 'livros'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Top 3 Avaliações */}
        <Card>
          <CardHeader>
            <CardTitle>Top 3 Avaliações</CardTitle>
            <p className="text-sm text-muted-foreground">Livros mais bem avaliados</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.top_rated_books.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum livro avaliado
              </div>
            ) : (
              <div className="space-y-4">
                {stats.top_rated_books.map((book, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">{book.title}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {book.authors_names.join(', ')}
                      </p>
                      <div className="mt-2">{renderStars(book.rating)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gráfico: Status de Leitura (Donut/Pie) */}
        <Card>
          <CardHeader>
            <CardTitle>Status de Leitura</CardTitle>
            <p className="text-sm text-muted-foreground">Distribuição por status</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.reading_status_distribution.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum livro cadastrado
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats.reading_status_distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="count"
                      label
                      labelLine={false}
                    >
                      {stats.reading_status_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any, name: string, props: any) => {
                        const status = props.payload.status_display || name;
                        return [`${value} ${value === 1 ? 'livro' : 'livros'}`, status];
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.reading_status_distribution.map((item, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>{item.status_display}</span>
                      </div>
                      <span className="font-semibold">
                        {item.count} {item.count === 1 ? 'livro' : 'livros'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 5: Timeline e Top Autores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico: Timeline de Leituras (Line) */}
        <Card>
          <CardHeader>
            <CardTitle>Linha do Tempo de Leitura</CardTitle>
            <p className="text-sm text-muted-foreground">Páginas lidas por mês (últimos 6 meses)</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.reading_timeline_monthly.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhuma leitura registrada
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.reading_timeline_monthly}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(value) => {
                      const [year, month] = value.split('-');
                      const date = new Date(parseInt(year), parseInt(month) - 1);
                      return format(date, 'MMM/yy', { locale: ptBR });
                    }}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip
                    labelFormatter={(value) => {
                      const [year, month] = value.split('-');
                      const date = new Date(parseInt(year), parseInt(month) - 1);
                      return format(date, 'MMMM yyyy', { locale: ptBR });
                    }}
                    labelStyle={{ color: 'hsl(var(--foreground))' }}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px'
                    }}
                    formatter={(value: any, name: string) => {
                      if (name === 'Páginas Lidas') return [value, 'Páginas'];
                      if (name === 'Tempo (horas)') return [`${value}h`, 'Tempo'];
                      return [value, name];
                    }}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="pages_read"
                    stroke={COLORS[0]}
                    strokeWidth={2}
                    name="Páginas Lidas"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="reading_time_hours"
                    stroke={COLORS[1]}
                    strokeWidth={2}
                    name="Tempo (horas)"
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Gráfico: Top 5 Autores (Horizontal Bar) */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Autores</CardTitle>
            <p className="text-sm text-muted-foreground">Autores com mais livros</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.top_authors.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum autor cadastrado
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.top_authors} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={120} />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'livro' : 'livros'}`, 'Quantidade']}
                    />
                    <Bar dataKey="books_count" radius={[0, 8, 8, 0]} name="Livros">
                      {stats.top_authors.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.top_authors.map((author, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span className="truncate max-w-[200px]" title={author.name}>
                          {author.name}
                        </span>
                      </div>
                      <span className="font-semibold">
                        {author.books_count} {author.books_count === 1 ? 'livro' : 'livros'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 6: Ratings e Distribuições */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico: Distribuição de Ratings (Vertical Bar) */}
        <Card>
          <CardHeader>
            <CardTitle>Distribuição de Avaliações</CardTitle>
            <p className="text-sm text-muted-foreground">Livros por faixa de avaliação (1-10)</p>
          </CardHeader>
          <CardContent>
            {!stats || stats.rating_distribution.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                Nenhum livro avaliado
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats.rating_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="rating_range" />
                    <YAxis />
                    <Tooltip
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px'
                      }}
                      formatter={(value: any) => [`${value} ${value === 1 ? 'livro' : 'livros'}`, 'Quantidade']}
                    />
                    <Bar dataKey="count" radius={[8, 8, 0, 0]} name="Livros">
                      {stats.rating_distribution.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {stats.rating_distribution.map((rating, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span>Avaliação {rating.rating_range}</span>
                      </div>
                      <span className="font-semibold">
                        {rating.count} {rating.count === 1 ? 'livro' : 'livros'}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Card: Distribuições (Idioma e Mídia) */}
        <Card>
          <CardHeader>
            <CardTitle>Distribuições</CardTitle>
            <p className="text-sm text-muted-foreground">Por idioma e tipo de mídia</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Seção: Por Idioma */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Por Idioma</h4>
                {stats?.books_by_language && stats.books_by_language.length > 0 ? (
                  <div className="space-y-2">
                    {stats.books_by_language.map((lang, index) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: COLORS[index % COLORS.length] }}
                          ></div>
                          <span>{lang.language_display}</span>
                        </div>
                        <span className="font-semibold">
                          {lang.count} {lang.count === 1 ? 'livro' : 'livros'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Nenhum livro cadastrado</p>
                )}
              </div>

              {/* Seção: Por Tipo de Mídia */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Por Tipo de Mídia</h4>
                {stats?.books_by_media_type && stats.books_by_media_type.length > 0 ? (
                  <div className="space-y-2">
                    {stats.books_by_media_type.map((media, index) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: COLORS[(index + 3) % COLORS.length] }}
                          ></div>
                          <span>{media.media_type_display}</span>
                        </div>
                        <span className="font-semibold">
                          {media.count} {media.count === 1 ? 'livro' : 'livros'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Nenhum livro com mídia definida</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Leituras Recentes */}
      <Card>
        <CardHeader>
          <CardTitle>Leituras Recentes</CardTitle>
          <p className="text-sm text-muted-foreground">Últimas 5 sessões de leitura</p>
        </CardHeader>
        <CardContent>
          {!stats || stats.recent_readings.length === 0 ? (
            <div className="h-32 flex items-center justify-center text-muted-foreground">
              Nenhuma leitura registrada
            </div>
          ) : (
            <div className="space-y-3">
              {stats.recent_readings.map((reading, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{reading.book_title}</p>
                      <p className="text-xs text-muted-foreground">
                        {reading.pages_read} {reading.pages_read === 1 ? 'página' : 'páginas'}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(reading.reading_date), "dd 'de' MMM", { locale: ptBR })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
