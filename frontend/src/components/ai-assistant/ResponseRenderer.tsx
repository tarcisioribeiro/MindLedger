/**
 * Componente para renderizar respostas do AI Assistant.
 *
 * Suporta diferentes tipos de exibição: texto, tabela, lista, moeda, senha.
 */
import { formatCurrency } from '@/lib/formatters';
import { autoTranslate } from '@/config/constants';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ResponseRendererProps {
  content: string;
  displayType: string;
  data?: Record<string, unknown>[];
}

export function ResponseRenderer({
  content,
  displayType,
  data,
}: ResponseRendererProps) {
  // Renderiza o texto principal
  const renderText = () => (
    <div className="whitespace-pre-wrap text-foreground leading-relaxed">
      {content.split('\n').map((line, i) => {
        // Detecta linhas com bullet points
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return (
            <div key={i} className="flex gap-2 my-1">
              <span className="text-primary">•</span>
              <span>{line.substring(2)}</span>
            </div>
          );
        }
        // Detecta linhas numeradas
        const numberedMatch = line.match(/^(\d+)\.\s/);
        if (numberedMatch) {
          return (
            <div key={i} className="flex gap-2 my-1">
              <span className="text-primary font-medium min-w-[1.5rem]">
                {numberedMatch[1]}.
              </span>
              <span>{line.substring(numberedMatch[0].length)}</span>
            </div>
          );
        }
        // Linha normal
        return line ? <p key={i} className="my-1">{line}</p> : <br key={i} />;
      })}
    </div>
  );

  // Renderiza tabela de dados
  const renderTable = () => {
    if (!data || data.length === 0) return renderText();

    const columns = Object.keys(data[0]);

    return (
      <div className="space-y-3">
        {/* Texto de contexto */}
        {content && !content.startsWith('1.') && (
          <p className="text-foreground mb-3">{content}</p>
        )}

        {/* Tabela */}
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                {columns.map((col) => (
                  <TableHead key={col} className="font-semibold capitalize">
                    {formatColumnName(col)}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, i) => (
                <TableRow key={i}>
                  {columns.map((col) => (
                    <TableCell key={col}>
                      {formatCellValue(col, row[col])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  };

  // Renderiza valor monetário destacado
  const renderCurrency = () => {
    // Tenta extrair o valor do primeiro item de data
    let valorPrincipal: number | null = null;

    if (data && data.length > 0) {
      const firstItem = data[0];
      // Procura por campos comuns de valor
      const valueFields = ['total', 'saldo_total', 'valor', 'media', 'total_guardado'];
      for (const field of valueFields) {
        if (firstItem[field] !== undefined && typeof firstItem[field] === 'number') {
          valorPrincipal = firstItem[field] as number;
          break;
        }
      }
    }

    return (
      <div className="space-y-3">
        {valorPrincipal !== null && (
          <div className="bg-primary/10 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-primary">
              {formatCurrency(valorPrincipal)}
            </div>
          </div>
        )}
        <div className="text-foreground whitespace-pre-wrap">{content}</div>
      </div>
    );
  };

  // Renderiza informações de senha (com cuidado)
  const renderPassword = () => {
    return (
      <div className="space-y-3">
        <div className="text-foreground whitespace-pre-wrap">{content}</div>

        {data && data.length > 0 && (
          <div className="space-y-2">
            {data.map((item, i) => (
              <div
                key={i}
                className="bg-muted/50 rounded-lg p-3 flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">{item.titulo || item.title}</div>
                  <div className="text-sm text-muted-foreground">
                    {item.usuario || item.username}
                    {(item.site) && ` • ${item.site}`}
                  </div>
                </div>
                {(item.categoria || item.category) && (
                  <Badge variant="secondary">
                    {autoTranslate(String(item.categoria || item.category))}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          Por segurança, acesse o módulo de Segurança para ver as senhas completas.
        </p>
      </div>
    );
  };

  // Escolhe o renderizador baseado no tipo
  switch (displayType) {
    case 'table':
      return renderTable();
    case 'currency':
      return renderCurrency();
    case 'password':
      return renderPassword();
    case 'list':
    case 'text':
    default:
      return renderText();
  }
}

/**
 * Formata nome de coluna para exibição.
 */
function formatColumnName(name: string): string {
  const translations: Record<string, string> = {
    descricao: 'Descrição',
    valor: 'Valor',
    data: 'Data',
    categoria: 'Categoria',
    conta: 'Conta',
    banco: 'Banco',
    tipo: 'Tipo',
    saldo: 'Saldo',
    cartao: 'Cartão',
    bandeira: 'Bandeira',
    limite: 'Limite',
    limite_disponivel: 'Limite Disponível',
    limite_total: 'Limite Total',
    titulo: 'Título',
    tarefa: 'Tarefa',
    horario: 'Horário',
    status: 'Status',
    meta: 'Meta',
    realizado: 'Realizado',
    objetivo: 'Objetivo',
    atual: 'Atual',
    inicio: 'Início',
    livro: 'Livro',
    paginas: 'Páginas',
    minutos: 'Minutos',
    genero: 'Gênero',
    avaliacao: 'Avaliação',
    cofre: 'Cofre',
    rendimentos: 'Rendimentos',
    taxa_rendimento: 'Taxa',
    origem: 'Origem',
    destino: 'Destino',
    credor: 'Credor',
    devedor: 'Devedor',
    valor_total: 'Valor Total',
    valor_pago: 'Valor Pago',
    valor_restante: 'Restante',
    valor_recebido: 'Recebido',
    valor_a_receber: 'A Receber',
    quantidade: 'Quantidade',
    total: 'Total',
    media: 'Média',
    usuario: 'Usuário',
    site: 'Site',
    ultima_alteracao: 'Última Alteração',
    periodicidade: 'Periodicidade',
    unidade: 'Unidade',
    ativa: 'Ativa',
    concluidas: 'Concluídas',
    taxa_conclusao: 'Taxa de Conclusão',
    paginas_lidas: 'Páginas Lidas',
  };

  return translations[name.toLowerCase()] || name.replace(/_/g, ' ');
}

/**
 * Formata valor de célula para exibição.
 */
function formatCellValue(column: string, value: unknown): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">-</span>;
  }

  // Valores monetários
  const currencyColumns = [
    'valor', 'saldo', 'total', 'limite', 'limite_disponivel', 'limite_total',
    'valor_total', 'valor_pago', 'valor_restante', 'valor_recebido',
    'valor_a_receber', 'media', 'rendimentos', 'valor_fatura'
  ];
  if (currencyColumns.includes(column.toLowerCase()) && typeof value === 'number') {
    return (
      <span className={cn(value < 0 ? 'text-destructive' : 'text-success')}>
        {formatCurrency(value)}
      </span>
    );
  }

  // Datas
  if (column.toLowerCase() === 'data' && typeof value === 'string') {
    const date = new Date(value);
    return date.toLocaleDateString('pt-BR');
  }

  // Horários
  if (column.toLowerCase() === 'horario' && typeof value === 'string') {
    return value.substring(0, 5); // HH:MM
  }

  // Status
  if (column.toLowerCase() === 'status') {
    const statusColors: Record<string, string> = {
      active: 'bg-success/20 text-success',
      ativo: 'bg-success/20 text-success',
      completed: 'bg-success/20 text-success',
      concluido: 'bg-success/20 text-success',
      paid: 'bg-success/20 text-success',
      pago: 'bg-success/20 text-success',
      pending: 'bg-warning/20 text-warning',
      pendente: 'bg-warning/20 text-warning',
      in_progress: 'bg-info/20 text-info',
      overdue: 'bg-destructive/20 text-destructive',
      atrasado: 'bg-destructive/20 text-destructive',
      cancelled: 'bg-muted text-muted-foreground',
      cancelado: 'bg-muted text-muted-foreground',
    };
    const statusKey = String(value).toLowerCase();
    return (
      <Badge className={cn('font-normal', statusColors[statusKey] || '')}>
        {autoTranslate(String(value))}
      </Badge>
    );
  }

  // Categorias
  if (column.toLowerCase() === 'categoria' || column.toLowerCase() === 'category') {
    return autoTranslate(String(value));
  }

  // Booleanos
  if (typeof value === 'boolean') {
    return value ? 'Sim' : 'Não';
  }

  // Avaliação (rating)
  if (column.toLowerCase() === 'avaliacao' && typeof value === 'number') {
    return '⭐'.repeat(value);
  }

  // Percentuais
  if (column.toLowerCase().includes('taxa') && typeof value === 'number') {
    return `${(value * 100).toFixed(2)}%`;
  }

  return String(value);
}
