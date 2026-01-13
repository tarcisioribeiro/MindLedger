import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { KanbanCard } from './KanbanCard';
import type { TaskCard, KanbanStatus } from '@/types';

interface KanbanColumnProps {
  status: KanbanStatus;
  title: string;
  cards: TaskCard[];
}

export function KanbanColumn({ status, title, cards }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  const getColorClasses = () => {
    const colors = {
      todo: 'bg-muted/30 border-border',
      doing: 'bg-info/10 border-info/30',
      done: 'bg-success/10 border-success/30',
    };
    return colors[status] || colors.todo;
  };

  const getHeaderColor = () => {
    const colors = {
      todo: 'bg-muted-foreground',
      doing: 'bg-info',
      done: 'bg-success',
    };
    return colors[status] || colors.todo;
  };

  return (
    <div className="flex flex-col max-h-[calc(100vh-14rem)]">
      {/* Column Header */}
      <div className={`${getHeaderColor()} text-white px-4 py-3 rounded-t-lg flex-shrink-0`}>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-sm opacity-90">{cards.length} {cards.length === 1 ? 'tarefa' : 'tarefas'}</p>
      </div>

      {/* Column Body */}
      <div
        ref={setNodeRef}
        className={`flex-1 ${getColorClasses()} border-2 rounded-b-lg p-4 min-h-[200px] transition-colors overflow-y-auto kanban-scrollbar ${
          isOver ? 'border-dashed border-4 border-info bg-info/20' : ''
        }`}
      >
        <SortableContext
          items={cards.map((card) => card.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-3">
            {cards.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p className="text-sm">Nenhuma tarefa</p>
              </div>
            ) : (
              cards.map((card) => <KanbanCard key={card.id} card={card} />)
            )}
          </div>
        </SortableContext>
      </div>
    </div>
  );
}
