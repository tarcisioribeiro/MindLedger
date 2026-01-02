import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { TaskCard } from '@/types';

interface KanbanCardProps {
  card: TaskCard;
}

export function KanbanCard({ card }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      health: 'bg-green-500',
      studies: 'bg-blue-500',
      spiritual: 'bg-purple-500',
      exercise: 'bg-orange-500',
      nutrition: 'bg-emerald-500',
      meditation: 'bg-indigo-500',
      reading: 'bg-amber-500',
      writing: 'bg-pink-500',
      work: 'bg-slate-500',
      leisure: 'bg-cyan-500',
      family: 'bg-rose-500',
      social: 'bg-violet-500',
      finance: 'bg-teal-500',
      household: 'bg-lime-500',
      personal_care: 'bg-fuchsia-500',
      other: 'bg-gray-500',
    };
    return colors[category] || 'bg-gray-500';
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white p-4 rounded-lg border-2 border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing"
    >
      <div className="flex items-start gap-3">
        {/* Drag Handle */}
        <div
          {...attributes}
          {...listeners}
          className="mt-1 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="h-5 w-5" />
        </div>

        {/* Card Content */}
        <div className="flex-1 space-y-2">
          {/* Title and Category */}
          <div className="flex items-start justify-between gap-2">
            <h4 className="font-medium text-sm leading-tight">
              {card.task_name}
              {card.total_instances > 1 && (
                <span className="ml-2 text-xs text-muted-foreground">
                  ({card.index + 1}º {card.unit})
                </span>
              )}
            </h4>
            <Badge className={`${getCategoryColor(card.category)} shrink-0`}>
              {card.category_display}
            </Badge>
          </div>

          {/* Notes */}
          {card.notes && (
            <div className="p-2 bg-yellow-50 border-l-4 border-yellow-300 rounded-sm">
              <p className="text-xs italic text-gray-700">{card.notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
