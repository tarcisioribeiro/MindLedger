import { useState, useEffect, useMemo } from 'react';
import { Save, CheckCircle2 } from 'lucide-react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragOverEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingState } from '@/components/common/LoadingState';
import { KanbanColumn } from '@/components/personal-planning/KanbanColumn';
import { KanbanCard } from '@/components/personal-planning/KanbanCard';
import { dailyTaskRecordsService } from '@/services/daily-task-records-service';
import { dailyReflectionsService } from '@/services/daily-reflections-service';
import { membersService } from '@/services/members-service';
import { appService } from '@/services/app-service';
import { useToast } from '@/hooks/use-toast';
import { MOOD_CHOICES, type TaskForToday, type TaskCard, type KanbanStatus } from '@/types';

import { formatLocalDate, parseLocalDate } from '@/lib/utils';
export default function DailyChecklist() {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [tasksData, setTasksData] = useState<TaskForToday[]>([]);
  const [cards, setCards] = useState<TaskCard[]>([]);
  const [activeCard, setActiveCard] = useState<TaskCard | null>(null);
  const [reflection, setReflection] = useState('');
  const [mood, setMood] = useState<string>('');
  const [reflectionId, setReflectionId] = useState<number | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [ownerId, setOwnerId] = useState(0);
  const { toast } = useToast();

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Convert TaskForToday[] to TaskCard[]
  const convertTasksToCards = (tasks: TaskForToday[]): TaskCard[] => {
    const newCards: TaskCard[] = [];

    tasks.forEach((task) => {
      // Create individual cards for each instance of the task
      for (let i = 0; i < task.target_quantity; i++) {
        let status: KanbanStatus = 'todo';

        // Determine status based on quantity_completed
        if (i < task.quantity_completed) {
          status = 'done';
        } else if (task.quantity_completed > 0 && i === task.quantity_completed) {
          // Next uncompleted task goes to "doing" if there's progress
          status = 'doing';
        }

        newCards.push({
          id: `${task.task_id}-${i}`,
          task_id: task.task_id,
          task_name: task.task_name,
          description: task.description,
          category: task.category,
          category_display: task.category_display,
          unit: task.unit,
          index: i,
          total_instances: task.target_quantity,
          status,
          notes: task.notes,
          record_id: task.record_id,
        });
      }
    });

    return newCards;
  };

  // Group cards by status
  const cardsByStatus = useMemo(() => {
    return {
      todo: cards.filter((card) => card.status === 'todo'),
      doing: cards.filter((card) => card.status === 'doing'),
      done: cards.filter((card) => card.status === 'done'),
    };
  }, [cards]);

  useEffect(() => {
    const initializeDate = async () => {
      try {
        const serverDate = await appService.getCurrentDate();
        setSelectedDate(serverDate);
      } catch (error) {
        // Fallback to browser date if server request fails
        setSelectedDate(formatLocalDate(new Date()));
      }
    };

    loadCurrentUserMember();
    initializeDate();
  }, []);

  useEffect(() => {
    if (ownerId > 0 && selectedDate) {
      loadData();
    }
  }, [selectedDate, ownerId]);

  useEffect(() => {
    // Convert tasks to cards whenever tasksData changes
    if (tasksData.length > 0) {
      setCards(convertTasksToCards(tasksData));
    } else {
      setCards([]);
    }
  }, [tasksData]);

  const loadCurrentUserMember = async () => {
    try {
      const member = await membersService.getCurrentUserMember();
      setOwnerId(member.id);
    } catch (error: any) {
      toast({
        title: 'Erro ao carregar usuário',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [tasksResponse, reflections] = await Promise.all([
        dailyTaskRecordsService.getTasksForToday(selectedDate),
        dailyReflectionsService.getAll(),
      ]);

      setTasksData(tasksResponse.tasks);

      // Find reflection for selected date
      const dayReflection = reflections.find((r) => r.date === selectedDate);
      if (dayReflection) {
        setReflection(dayReflection.reflection);
        setMood(dayReflection.mood || '');
        setReflectionId(dayReflection.id);
      } else {
        setReflection('');
        setMood('');
        setReflectionId(undefined);
      }
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

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const card = cards.find((c) => c.id === active.id);
    setActiveCard(card || null);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find active and over cards
    const activeCard = cards.find((c) => c.id === activeId);
    const overCard = cards.find((c) => c.id === overId);

    if (!activeCard) return;

    // Determine target status
    let targetStatus: KanbanStatus | undefined;

    if (overCard) {
      // Dropped on a card
      targetStatus = overCard.status;
    } else if (['todo', 'doing', 'done'].includes(overId)) {
      // Dropped on a column
      targetStatus = overId as KanbanStatus;
    }

    if (!targetStatus || activeCard.status === targetStatus) return;

    // Update card status
    setCards((cards) =>
      cards.map((card) =>
        card.id === activeId ? { ...card, status: targetStatus! } : card
      )
    );
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCard(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    const activeCard = cards.find((c) => c.id === activeId);
    const overCard = cards.find((c) => c.id === overId);

    if (!activeCard) return;

    // Determine final status
    let finalStatus: KanbanStatus | undefined;

    if (overCard) {
      finalStatus = overCard.status;
    } else if (['todo', 'doing', 'done'].includes(overId)) {
      finalStatus = overId as KanbanStatus;
    }

    if (!finalStatus) return;

    // Reorder within the same column
    if (activeCard.status === finalStatus && overCard) {
      const activeIndex = cards.findIndex((c) => c.id === activeId);
      const overIndex = cards.findIndex((c) => c.id === overId);

      setCards((cards) => arrayMove(cards, activeIndex, overIndex));
    } else {
      // Moved to different column - status already updated in handleDragOver
    }

    // Update tasksData based on new card statuses
    updateTasksFromCards();
  };

  const updateTasksFromCards = () => {
    setTasksData((prevTasks) =>
      prevTasks.map((task) => {
        const taskCards = cards.filter((card) => card.task_id === task.task_id);
        const doneCards = taskCards.filter((card) => card.status === 'done');
        const quantityCompleted = doneCards.length;
        const completed = quantityCompleted === task.target_quantity;

        return {
          ...task,
          completed,
          quantity_completed: quantityCompleted,
        };
      })
    );
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      // Calculate completion status from cards
      const taskCompletionMap = new Map<number, { completed: boolean; quantity: number }>();

      cards.forEach((card) => {
        const current = taskCompletionMap.get(card.task_id) || { completed: false, quantity: 0 };
        if (card.status === 'done') {
          current.quantity += 1;
        }
        taskCompletionMap.set(card.task_id, current);
      });

      // Update completed status
      taskCompletionMap.forEach((value, taskId) => {
        const task = tasksData.find((t) => t.task_id === taskId);
        if (task) {
          value.completed = value.quantity === task.target_quantity;
        }
      });

      // Save daily task records
      const taskSavePromises = tasksData.map(async (task) => {
        const completion = taskCompletionMap.get(task.task_id) || { completed: false, quantity: 0 };

        const recordData = {
          task: task.task_id,
          date: selectedDate,
          completed: completion.completed,
          quantity_completed: completion.quantity,
          notes: task.notes,
          owner: ownerId,
        };

        if (task.record_id) {
          // Update existing record
          return dailyTaskRecordsService.update(task.record_id, recordData);
        } else if (completion.completed || completion.quantity > 0) {
          // Create new record only if there's some progress
          return dailyTaskRecordsService.create(recordData);
        }
      });

      // Save or update reflection if there's content
      let reflectionPromise;
      if (reflection.trim().length >= 10) {
        const reflectionData = {
          date: selectedDate,
          reflection: reflection.trim(),
          mood: mood || undefined,
          owner: ownerId,
        };

        if (reflectionId) {
          reflectionPromise = dailyReflectionsService.update(reflectionId, reflectionData);
        } else {
          reflectionPromise = dailyReflectionsService.create(reflectionData);
        }
      }

      await Promise.all([...taskSavePromises, reflectionPromise].filter(Boolean));

      toast({
        title: 'Dados salvos',
        description: 'Seu checklist e reflexão foram salvos com sucesso!',
      });

      // Reload data to get updated IDs and counts
      loadData();
    } catch (error: any) {
      toast({
        title: 'Erro ao salvar',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const completedTasks = cardsByStatus.done.length;

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Checklist Diário"
        description="Organize suas tarefas no quadro kanban"
        icon={<CheckCircle2 />}
      />

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Label htmlFor="date">Data</Label>
          <DatePicker
            value={selectedDate ? parseLocalDate(selectedDate) : undefined}
            onChange={(date) => setSelectedDate(date ? formatLocalDate(date) : '')}
            placeholder="Selecione a data"
            className="max-w-xs"
          />
        </div>
        <div className="text-lg font-semibold">
          {completedTasks} de {cards.length} itens concluídos
        </div>
      </div>

      {cards.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Nenhuma tarefa programada para este dia.</p>
              <p className="text-sm">
                Crie tarefas rotineiras para começar seu acompanhamento!
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-3 gap-6">
            <KanbanColumn
              status="todo"
              title="A Fazer"
              cards={cardsByStatus.todo}
            />
            <KanbanColumn
              status="doing"
              title="Fazendo"
              cards={cardsByStatus.doing}
            />
            <KanbanColumn
              status="done"
              title="Concluído"
              cards={cardsByStatus.done}
            />
          </div>

          <DragOverlay>
            {activeCard ? <KanbanCard card={activeCard} /> : null}
          </DragOverlay>
        </DndContext>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Reflexão do Dia</CardTitle>
          <CardDescription>
            Como foi o seu dia? Registre seus pensamentos e sentimentos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="mood">Como você se sentiu hoje?</Label>
            <Select value={mood} onValueChange={setMood}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione seu humor..." />
              </SelectTrigger>
              <SelectContent>
                {MOOD_CHOICES.map((choice) => (
                  <SelectItem key={choice.value} value={choice.value}>
                    {choice.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="reflection">Reflexão</Label>
            <Textarea
              id="reflection"
              value={reflection}
              onChange={(e) => setReflection(e.target.value)}
              placeholder="Escreva sobre o seu dia, conquistas, desafios, aprendizados..."
              rows={6}
            />
            {reflection.length > 0 && reflection.length < 10 && (
              <p className="text-sm text-destructive mt-1">
                A reflexão deve ter no mínimo 10 caracteres
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving} size="lg">
          {isSaving ? (
            <>
              <Save className="mr-2 h-4 w-4 animate-pulse" />
              Salvando...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Salvar
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
