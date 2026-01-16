import { useState, useEffect } from 'react';
import { Plus, CheckSquare, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import { LoadingState } from '@/components/common/LoadingState';
import { RoutineTaskForm } from '@/components/personal-planning/RoutineTaskForm';
import { routineTasksService } from '@/services/routine-tasks-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import type { RoutineTask } from '@/types';
import { routineTaskSchema } from '@/lib/validations';
import { z } from 'zod';
import { PageContainer } from '@/components/common/PageContainer';

type RoutineTaskFormData = z.infer<typeof routineTaskSchema>;

export default function RoutineTasks() {
  const [tasks, setTasks] = useState<RoutineTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<RoutineTask | undefined>();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { showConfirm } = useAlertDialog();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const tasksData = await routineTasksService.getAll();
      setTasks(tasksData);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar dados',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedTask(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = (task: RoutineTask) => {
    setSelectedTask(task);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir tarefa',
      description:
        'Tem certeza que deseja excluir esta tarefa? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await routineTasksService.delete(id);
      toast({
        title: 'Tarefa excluída',
        description: 'A tarefa foi excluída com sucesso.',
      });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir tarefa',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (data: RoutineTaskFormData) => {
    try {
      setIsSubmitting(true);
      // Convert null to undefined for API compatibility
      const apiData = {
        ...data,
        weekday: data.weekday === null ? undefined : data.weekday,
        day_of_month: data.day_of_month === null ? undefined : data.day_of_month,
      };

      if (selectedTask) {
        await routineTasksService.update(selectedTask.id, apiData as any);
        toast({
          title: 'Tarefa atualizada',
          description: 'A tarefa foi atualizada com sucesso.',
        });
      } else {
        await routineTasksService.create(apiData as any);
        toast({
          title: 'Tarefa criada',
          description: 'A tarefa foi criada com sucesso.',
        });
      }
      setIsDialogOpen(false);
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao salvar',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCompletionRateColor = (rate: number) => {
    if (rate >= 80) return 'bg-success';
    if (rate >= 50) return 'bg-warning';
    return 'bg-destructive';
  };

  // Define table columns
  const columns: Column<RoutineTask>[] = [
    {
      key: 'name',
      label: 'Nome',
      render: (task) => <div className="font-medium">{task.name}</div>,
    },
    {
      key: 'category',
      label: 'Categoria',
      render: (task) => (
        <Badge variant="secondary">{task.category_display}</Badge>
      ),
    },
    {
      key: 'periodicity',
      label: 'Periodicidade',
      render: (task) => (
        <div className="text-sm">
          <div>{task.periodicity_display}</div>
          {task.weekday_display && (
            <div className="text-muted-foreground text-xs">
              {task.weekday_display}
            </div>
          )}
          {task.day_of_month && (
            <div className="text-muted-foreground text-xs">
              Dia {task.day_of_month}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'target',
      label: 'Meta',
      render: (task) => (
        <span className="text-sm">
          {task.target_quantity} {task.unit}
        </span>
      ),
    },
    {
      key: 'completion_rate',
      label: 'Taxa de Cumprimento',
      align: 'center',
      render: (task) => (
        <Badge className={getCompletionRateColor(task.completion_rate)}>
          {task.completion_rate.toFixed(0)}%
        </Badge>
      ),
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (task) => (
        <Badge variant={task.is_active ? 'success' : 'secondary'}>
          {task.is_active ? 'Ativa' : 'Inativa'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Ações',
      align: 'center',
      render: (task) => (
        <div className="flex gap-2 justify-center">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleEdit(task)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleDelete(task.id)}
          >
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageContainer>
      <PageHeader
        title="Tarefas Rotineiras"
        description="Gerencie suas tarefas e hábitos diários"
        icon={<CheckSquare />}
        action={{
          label: 'Nova Tarefa',
          icon: <Plus className="h-4 w-4" />,
          onClick: handleCreate,
        }}
      />

      <DataTable
        data={tasks}
        columns={columns}
        keyExtractor={(task) => task.id}
        isLoading={isLoading}
        emptyState={{
          icon: <CheckSquare className="h-12 w-12" />,
          title: 'Nenhuma tarefa encontrada',
          message: 'Comece criando sua primeira tarefa rotineira.',
        }}
      />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle>
              {selectedTask ? 'Editar Tarefa' : 'Nova Tarefa'}
            </DialogTitle>
            <DialogDescription>
              {selectedTask
                ? 'Atualize as informações da tarefa rotineira.'
                : 'Crie uma nova tarefa para acompanhar seus hábitos diários.'}
            </DialogDescription>
          </DialogHeader>
          <RoutineTaskForm
            task={selectedTask}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
