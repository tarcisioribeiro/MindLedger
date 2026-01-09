import { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { EnhancedTooltip } from './EnhancedTooltip';
import { useChartGradientId } from '@/lib/chart-colors';
import { truncateLabel } from '@/lib/chart-formatters';
import type { ChartDataPoint } from '@/lib/chart-types';

interface EnhancedPieChartProps {
  data: ChartDataPoint[];
  dataKey: string;
  nameKey: string;
  formatter?: (value: number | string) => string;
  colors: string[];
  customColors?: (entry: ChartDataPoint) => string;
  height?: number;
}

/**
 * Gráfico de pizza/donut aprimorado
 *
 * Recursos:
 * - Estilo donut moderno (com furo central)
 * - Gradientes radiais para profundidade
 * - Sombra sutil para elevação
 * - Legenda personalizada e limpa
 * - Animações suaves
 * - Tooltip customizado
 * - Sem labels sobrepostos (usa legenda)
 * - IDs únicos para gradientes
 */
export const EnhancedPieChart = ({
  data,
  dataKey,
  nameKey,
  formatter,
  colors,
  customColors,
  height = 300,
}: EnhancedPieChartProps) => {
  // Gera IDs únicos para gradientes
  const getGradientId = useChartGradientId('pie-radial');
  const shadowId = useChartGradientId('pie-shadow');

  // Definições de gradientes memoizadas
  const gradientDefs = useMemo(
    () => (
      <>
        {colors.map((color, idx) => (
          <radialGradient
            key={getGradientId(idx)}
            id={getGradientId(idx)}
            cx="30%"
            cy="30%"
          >
            <stop offset="0%" stopColor={color} stopOpacity={1} />
            <stop offset="70%" stopColor={color} stopOpacity={0.85} />
            <stop offset="100%" stopColor={color} stopOpacity={0.7} />
          </radialGradient>
        ))}
        <filter id={shadowId(0)} x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.1" />
        </filter>
      </>
    ),
    [colors, getGradientId, shadowId]
  );

  // Calcula o total para percentuais na legenda
  const total = useMemo(
    () => data.reduce((sum, item) => sum + Number(item[dataKey] || 0), 0),
    [data, dataKey]
  );

  // Renderizador customizado da legenda
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderLegend = (props: any) => {
    const { payload } = props as { payload?: Array<{ value: string; color: string; payload: ChartDataPoint }> };
    if (!payload) return null;

    return (
      <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-2 px-2">
        {payload.map((entry, index) => {
          const value = Number(entry.payload[dataKey] || 0);
          const percent = total > 0 ? ((value / total) * 100).toFixed(0) : 0;

          return (
            <li
              key={`legend-${index}`}
              className="flex items-center gap-1.5 text-xs"
            >
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-foreground/80 truncate max-w-[100px]" title={entry.value}>
                {truncateLabel(entry.value, 12)}
              </span>
              <span className="text-muted-foreground font-medium">
                {percent}%
              </span>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <defs>{gradientDefs}</defs>

        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius="55%"
          outerRadius="85%"
          paddingAngle={2}
          dataKey={dataKey}
          nameKey={nameKey}
          animationBegin={0}
          animationDuration={600}
          animationEasing="ease-out"
          style={{ filter: `url(#${shadowId(0)})` }}
        >
          {data.map((entry, index) => {
            const fillColor = customColors
              ? customColors(entry)
              : `url(#${getGradientId(index % colors.length)})`;

            return (
              <Cell
                key={`cell-${index}`}
                fill={fillColor}
                stroke="hsl(var(--background))"
                strokeWidth={2}
                className="transition-opacity duration-200 hover:opacity-80"
                style={{ cursor: 'pointer' }}
              />
            );
          })}
        </Pie>

        <Tooltip content={<EnhancedTooltip formatter={formatter} />} />

        <Legend
          content={renderLegend}
          verticalAlign="bottom"
          align="center"
        />
      </PieChart>
    </ResponsiveContainer>
  );
};
