import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { EnhancedTooltip } from './EnhancedTooltip';

interface EnhancedPieChartProps {
  data: any[];
  dataKey: string;
  nameKey: string;
  formatter?: (value: any) => string;
  colors: string[];
  customColors?: (entry: any) => string;
  height?: number;
}

/**
 * Gráfico de pizza aprimorado com:
 * - Gradientes radiais simulando profundidade 3D
 * - Drop shadow para efeito de elevação
 * - Animações suaves
 * - Tooltip customizado
 * - Suporte a cores customizadas
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
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <defs>
          {/* Gradientes radiais para simular profundidade 3D */}
          {colors.map((color, idx) => (
            <radialGradient
              key={`radial-gradient-${idx}`}
              id={`radial-gradient-${idx}`}
              cx="30%"
              cy="30%"
            >
              <stop offset="0%" stopColor={color} stopOpacity={1} />
              <stop offset="50%" stopColor={color} stopOpacity={0.85} />
              <stop offset="100%" stopColor={color} stopOpacity={0.6} />
            </radialGradient>
          ))}

          {/* Drop shadow filter para efeito de elevação */}
          <filter id="pie-shadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.15" />
          </filter>
        </defs>

        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey={dataKey}
          label={(entry) => entry[nameKey]}
          animationBegin={0}
          animationDuration={800}
          animationEasing="ease-in-out"
          style={{ filter: 'url(#pie-shadow)' }}
        >
          {data.map((entry, index) => {
            const fillColor = customColors
              ? customColors(entry)
              : `url(#radial-gradient-${index % colors.length})`;

            return (
              <Cell
                key={`cell-${index}`}
                fill={fillColor}
                className="hover:opacity-80 transition-opacity cursor-pointer"
              />
            );
          })}
        </Pie>

        <Tooltip content={<EnhancedTooltip formatter={formatter} />} />
        <Legend
          formatter={(value, entry: any) => {
            // Se o entry tem o nameKey, use-o para exibir o nome traduzido
            return entry.payload?.[nameKey] || value;
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};
