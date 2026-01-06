import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Area, ResponsiveContainer, AreaChart } from 'recharts';
import { EnhancedTooltip } from './EnhancedTooltip';

interface LineConfig {
  dataKey: string;
  stroke: string;
  yAxisId?: string;
  name?: string;
}

interface YAxisConfig {
  dataKey: string;
  label?: string;
  color: string;
}

interface DualYAxisConfig {
  left: YAxisConfig;
  right: YAxisConfig;
}

interface EnhancedLineChartProps {
  data: any[];
  dataKey?: string;
  nameKey?: string;
  formatter?: (value: any) => string;
  colors: string[];
  lines?: LineConfig[];
  dualYAxis?: DualYAxisConfig;
  height?: number;
  withArea?: boolean;
}

/**
 * Gráfico de linhas aprimorado com:
 * - Área preenchida com gradiente para transparente
 * - Suporte a dual Y-axis (esquerda/direita)
 * - Suporte a múltiplas linhas
 * - Dots aprimorados com shadow no hover
 * - CartesianGrid sutil
 * - Animações suaves
 * - Tooltip customizado
 */
export const EnhancedLineChart = ({
  data,
  dataKey,
  nameKey = 'name',
  formatter,
  colors,
  lines,
  dualYAxis,
  height = 300,
  withArea = true,
}: EnhancedLineChartProps) => {
  // Modo single line (dataKey único)
  const isSingleLine = !lines && dataKey;

  // Configuração de linhas
  const lineConfigs: LineConfig[] = lines || (isSingleLine ? [{ dataKey: dataKey!, stroke: colors[0] }] : []);

  const ChartComponent = withArea ? AreaChart : LineChart;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent data={data}>
        <defs>
          {/* Gradientes para área fill (transparente no bottom) */}
          {lineConfigs.map((line, idx) => (
            <linearGradient
              key={`area-gradient-${idx}`}
              id={`area-gradient-${idx}`}
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="5%" stopColor={line.stroke} stopOpacity={0.4} />
              <stop offset="95%" stopColor={line.stroke} stopOpacity={0.05} />
            </linearGradient>
          ))}
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />

        <XAxis dataKey={nameKey} />

        {dualYAxis ? (
          <>
            <YAxis yAxisId="left" stroke={dualYAxis.left.color} />
            <YAxis yAxisId="right" orientation="right" stroke={dualYAxis.right.color} />
          </>
        ) : (
          <YAxis />
        )}

        <Tooltip content={<EnhancedTooltip formatter={formatter} />} />

        {lineConfigs.length > 1 && (
          <Legend
            formatter={(value) => {
              // Se houver configuração de linha com nome customizado, use-o
              const lineConfig = lineConfigs.find(l => l.dataKey === value);
              return lineConfig?.name || value;
            }}
          />
        )}

        {withArea
          ? lineConfigs.map((line, idx) => (
              <Area
                key={`area-${idx}`}
                type="monotone"
                dataKey={line.dataKey}
                stroke={line.stroke}
                fill={`url(#area-gradient-${idx})`}
                strokeWidth={3}
                yAxisId={line.yAxisId}
                name={line.name}
                dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
                activeDot={{
                  r: 8,
                  strokeWidth: 3,
                  style: {
                    filter: 'drop-shadow(0 0 6px currentColor)',
                    cursor: 'pointer',
                  },
                }}
                animationDuration={800}
                animationEasing="ease-in-out"
              />
            ))
          : lineConfigs.map((line, idx) => (
              <Line
                key={`line-${idx}`}
                type="monotone"
                dataKey={line.dataKey}
                stroke={line.stroke}
                strokeWidth={3}
                yAxisId={line.yAxisId}
                name={line.name}
                dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
                activeDot={{
                  r: 8,
                  strokeWidth: 3,
                  style: {
                    filter: 'drop-shadow(0 0 6px currentColor)',
                    cursor: 'pointer',
                  },
                }}
                animationDuration={800}
                animationEasing="ease-in-out"
              />
            ))}
      </ChartComponent>
    </ResponsiveContainer>
  );
};
