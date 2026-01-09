import type { ChartTooltipProps } from '@/lib/chart-types';

/**
 * Tooltip customizado para gráficos Recharts
 * Design moderno com:
 * - Visual limpo e minimalista
 * - Indicadores de cor arredondados
 * - Formatação de valores
 * - Suporte a múltiplos itens
 * - Animação suave
 */
export const EnhancedTooltip = ({
  active,
  payload,
  label,
  formatter,
}: ChartTooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div
      className="bg-popover/95 backdrop-blur-md border border-border
                 rounded-xl shadow-lg p-3 min-w-[140px] max-w-[280px]
                 animate-in fade-in-0 zoom-in-95 duration-150"
    >
      {/* Label/Título */}
      {label && (
        <p className="text-xs font-medium text-muted-foreground mb-2 pb-2 border-b border-border/50">
          {label}
        </p>
      )}

      {/* Lista de valores */}
      <div className="space-y-1.5">
        {payload.map((entry, index) => (
          <div
            key={`tooltip-item-${index}`}
            className="flex items-center justify-between gap-3"
          >
            {/* Indicador de cor + Nome */}
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0 ring-1 ring-white/20"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-foreground/80 truncate">
                {entry.name}
              </span>
            </div>

            {/* Valor */}
            <span className="text-sm font-semibold text-foreground tabular-nums">
              {formatter ? formatter(entry.value) : entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
