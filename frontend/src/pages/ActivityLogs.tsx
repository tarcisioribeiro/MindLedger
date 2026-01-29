import { useState, useEffect } from 'react';
import { ScrollText } from 'lucide-react';
import { activityLogsService } from '@/services/activity-logs-service';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/utils/error-utils';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { ActivityLog } from '@/types';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function ActivityLogs() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const data = await activityLogsService.getAll();
      setLogs(data);
    } catch (error: unknown) {
      toast({
        title: 'Erro ao carregar dados',
        description: getErrorMessage(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Logs de Atividade"
        icon={<ScrollText />}
      />

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Data/Hora</TableHead>
              <TableHead>Ação</TableHead>
              <TableHead>Descrição</TableHead>
              <TableHead>IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="font-medium">
                  {format(new Date(log.created_at), "dd/MM/yyyy HH:mm:ss", {
                    locale: ptBR,
                  })}
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{log.action_display}</Badge>
                </TableCell>
                <TableCell>{log.description}</TableCell>
                <TableCell>
                  {log.ip_address || '-'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {logs.length === 0 && (
        <div className="text-center py-12">
          <p>Nenhum log encontrado.</p>
        </div>
      )}
    </div>
  );
}
