/**
 * SQL Display Component
 *
 * Renders SQL query information with syntax highlighting and metadata.
 * Used in AI Assistant to show generated SQL queries and their execution details.
 */

import { Database, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { SQLMetadata } from '@/stores/ai-chat-store';

interface SQLDisplayProps {
  sqlMetadata: SQLMetadata;
}

export function SQLDisplay({ sqlMetadata }: SQLDisplayProps) {
  const { query, explanation, executionTimeMs, rowCount, truncated } = sqlMetadata;

  if (!query) {
    return null;
  }

  return (
    <Card className="mt-4 border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <Database className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">
            Consulta SQL
          </h3>
          <Badge variant="outline" className="ml-auto text-xs">
            SQL
          </Badge>
        </div>

        {/* Explanation */}
        {explanation && (
          <p className="text-xs text-blue-800 dark:text-blue-200 mb-3 leading-relaxed">
            {explanation}
          </p>
        )}

        {/* SQL Query */}
        <div className="relative">
          <pre className="bg-slate-900 dark:bg-slate-950 rounded-lg p-4 overflow-x-auto">
            <code className="text-xs text-slate-100 font-mono leading-relaxed">
              {query}
            </code>
          </pre>
        </div>

        {/* Metadata Footer */}
        <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-blue-700 dark:text-blue-300">
          {/* Execution Time */}
          {executionTimeMs !== undefined && (
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              <span>{executionTimeMs.toFixed(2)}ms</span>
            </div>
          )}

          {/* Row Count */}
          {rowCount !== undefined && (
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>
                {rowCount} {rowCount === 1 ? 'linha' : 'linhas'}
              </span>
            </div>
          )}

          {/* Truncated Warning */}
          {truncated && (
            <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Resultados truncados</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
