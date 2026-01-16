import { useState, useEffect } from 'react';
import { Plus, Trophy, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
import { GoalForm } from '@/components/personal-planning/GoalForm';
import { goalsService } from '@/services/goals-service';
import { routineTasksService } from '@/services/routine-tasks-service';
import { useToast } from '@/hooks/use-toast';
import { useAlertDialog } from '@/hooks/use-alert-dialog';
import type { Goal, RoutineTask } from '@/types';
import { goalSchema } from '@/lib/validations';
import { z } from 'zod';
import { PageContainer } from '@/components/common/PageContainer';

type GoalFormData = z.infer<typeof goalSchema>;

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [tasks, setTasks] = useState<RoutineTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedGoal, setSelectedGoal] = useState<Goal | undefined>();
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
      const [goalsData, tasksData] = await Promise.all([
        goalsService.getAll(),
        routineTasksService.getAll(),
      ]);
      setGoals(goalsData);
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
    setSelectedGoal(undefined);
    setIsDialogOpen(true);
  };

  const handleEdit = (goal: Goal) => {
    setSelectedGoal(goal);
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    const confirmed = await showConfirm({
      title: 'Excluir objetivo',
      description:
        'Tem certeza que deseja excluir este objetivo? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      cancelText: 'Cancelar',
      variant: 'destructive',
    });

    if (!confirmed) return;

    try {
      await goalsService.delete(id);
      toast({
        title: 'Objetivo excluído',
        description: 'O objetivo foi excluído com sucesso.',
      });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao excluir objetivo',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (data: GoalFormData) => {
    try {
      setIsSubmitting(true);
      // Convert null to undefined for API compatibility
      const apiData = {
        ...data,
        related_task: data.related_task === null ? undefined : data.related_task,
      };

      if (selectedGoal) {
        await goalsService.update(selectedGoal.id, apiData as any);
        toast({
          title: 'Objetivo atualizado',
          description: 'O objetivo foi atualizado com sucesso.',
        });
      } else {
        await goalsService.create(apiData as any);
        toast({
          title: 'Objetivo criado',
          description: 'O objetivo foi criado com sucesso.',
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-info';
      case 'completed':
        return 'bg-success';
      case 'failed':
        return 'bg-destructive';
      case 'cancelled':
        return 'bg-muted';
      default:
        return 'bg-muted';
    }
  };

  // Define table columns
  const columns: Column<Goal>[] = [
    {
      key: 'title',
      label: 'Título',
      render: (goal) => <div className="font-medium">{goal.title}</div>,
    },
    {
      key: 'goal_type',
      label: 'Tipo',
      render: (goal) => (
        <Badge variant="secondary">{goal.goal_type_display}</Badge>
      ),
    },
    {
      key: 'related_task',
      label: 'Tarefa Relacionada',
      render: (goal) => (
        <span className="text-sm">
          {goal.related_task_name || '-'}
        </span>
      ),
    },
    {
      key: 'progress',
      label: 'Progresso',
      render: (goal) => (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span>
              {goal.current_value} / {goal.target_value}
            </span>
            <span className="font-medium">
              {goal.progress_percentage.toFixed(0)}%
            </span>
          </div>
          <Progress value={goal.progress_percentage} className="h-2" />
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (goal) => (
        <Badge className={getStatusColor(goal.status)}>
          {goal.status_display}
        </Badge>
      ),
    },
    {
      key: 'days_active',
      label: 'Dias Ativos',
      align: 'center',
      render: (goal) => (
        <span className="text-sm font-medium">{goal.days_active}</span>
      ),
    },
    {
      key: 'actions',
      label: 'Ações',
      align: 'center',
      render: (goal) => (
        <div className="flex gap-2 justify-center">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleEdit(goal)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleDelete(goal.id)}
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
        title="Objetivos"
        description="Acompanhe seus objetivos e metas pessoais"
        icon={<Trophy />}
        action={{
          label: 'Novo Objetivo',
          icon: <Plus className="h-4 w-4" />,
          onClick: handleCreate,
        }}
      />

      <DataTable
        data={goals}
        columns={columns}
        keyExtractor={(goal) => goal.id}
        isLoading={isLoading}
        emptyState={{
          icon: <Trophy className="h-12 w-12" />,
          title: 'Nenhum objetivo encontrado',
          message: 'Comece criando seu primeiro objetivo.',
        }}
      />

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle>
              {selectedGoal ? 'Editar Objetivo' : 'Novo Objetivo'}
            </DialogTitle>
            <DialogDescription>
              {selectedGoal
                ? 'Atualize as informações do objetivo.'
                : 'Crie um novo objetivo para acompanhar seu progresso.'}
            </DialogDescription>
          </DialogHeader>
          <GoalForm
            goal={selectedGoal}
            routineTasks={tasks}
            onSubmit={handleSubmit}
            onCancel={() => setIsDialogOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
