import {
  CheckSquare,
  AlertTriangle,
  Receipt,
  HandCoins,
  CreditCard,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Notification } from '@/types';

const iconMap: Record<string, React.ElementType> = {
  task_today: CheckSquare,
  task_overdue: AlertTriangle,
  payable_due_soon: Receipt,
  payable_overdue: Receipt,
  loan_due_soon: HandCoins,
  loan_overdue: HandCoins,
  bill_due_soon: CreditCard,
  bill_overdue: CreditCard,
};

const colorMap: Record<string, string> = {
  task_today: 'text-primary',
  task_overdue: 'text-destructive',
  payable_due_soon: 'text-warning',
  payable_overdue: 'text-destructive',
  loan_due_soon: 'text-warning',
  loan_overdue: 'text-destructive',
  bill_due_soon: 'text-warning',
  bill_overdue: 'text-destructive',
};

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: number) => void;
}

export function NotificationItem({
  notification,
  onMarkAsRead,
}: NotificationItemProps) {
  const Icon = iconMap[notification.notification_type] || AlertTriangle;
  const iconColor = colorMap[notification.notification_type] || 'text-muted-foreground';

  return (
    <button
      className={cn(
        'w-full flex items-start gap-3 p-3 text-left rounded-md transition-colors hover:bg-accent',
        !notification.is_read && 'bg-accent/50'
      )}
      onClick={() => {
        if (!notification.is_read) {
          onMarkAsRead(notification.id);
        }
      }}
    >
      <div className={cn('mt-0.5 shrink-0', iconColor)}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p
            className={cn(
              'text-sm truncate',
              !notification.is_read && 'font-semibold'
            )}
          >
            {notification.title}
          </p>
          {!notification.is_read && (
            <span className="shrink-0 w-2 h-2 rounded-full bg-primary" />
          )}
        </div>
        {notification.message && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {notification.message}
          </p>
        )}
      </div>
    </button>
  );
}
