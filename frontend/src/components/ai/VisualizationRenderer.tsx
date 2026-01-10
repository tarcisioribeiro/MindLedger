/**
 * Visualization Renderer
 *
 * Renders different types of visualizations for AI Assistant responses:
 * - Charts (pie, bar, line)
 * - Stat cards
 * - Tables
 */

import React from 'react';
import { AIVisualization } from '@/stores/ai-chat-store';
import { StatCard } from '@/components/common/StatCard';
import { EnhancedPieChart, EnhancedBarChart, EnhancedLineChart } from '@/components/charts';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface VisualizationRendererProps {
  visualization: AIVisualization;
}

export const VisualizationRenderer: React.FC<VisualizationRendererProps> = ({
  visualization,
}) => {
  if (!visualization) return null;

  switch (visualization.type) {
    case 'cards':
      return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          {visualization.cards?.map((card, idx) => (
            <StatCard
              key={idx}
              title={card.title}
              value={card.value}
              variant={card.variant as any}
            />
          ))}
        </div>
      );

    case 'chart':
      if (!visualization.data) return null;

      return (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-sm">Visualização</CardTitle>
          </CardHeader>
          <CardContent>
            {visualization.data.type === 'pie' && (
              <EnhancedPieChart
                data={visualization.data.data}
                dataKey={visualization.data.config?.dataKey || 'value'}
                nameKey={visualization.data.config?.nameKey || 'name'}
                height={300}
              />
            )}

            {visualization.data.type === 'bar' && (
              <EnhancedBarChart
                data={visualization.data.data}
                dataKey={visualization.data.config?.dataKey || 'value'}
                nameKey={visualization.data.config?.nameKey || 'name'}
                height={300}
                layout={visualization.data.config?.layout}
              />
            )}

            {visualization.data.type === 'line' && (
              <EnhancedLineChart
                data={visualization.data.data}
                dataKeys={visualization.data.config?.dataKeys || [visualization.data.config?.dataKey || 'value']}
                nameKey={visualization.data.config?.nameKey || 'name'}
                height={300}
                withArea={visualization.data.config?.withArea}
                labels={visualization.data.config?.labels}
              />
            )}
          </CardContent>
        </Card>
      );

    case 'table':
      if (!visualization.columns || !visualization.rows) return null;

      return (
        <Card className="mt-4">
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {visualization.columns.map((col) => (
                      <TableHead key={col.key}>{col.label}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visualization.rows.map((row, idx) => (
                    <TableRow key={idx}>
                      {visualization.columns!.map((col) => (
                        <TableCell key={col.key}>{row[col.key]}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      );

    default:
      return null;
  }
};
