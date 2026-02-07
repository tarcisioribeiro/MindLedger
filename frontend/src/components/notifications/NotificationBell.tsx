import { useEffect } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { NotificationItem } from './NotificationItem';
import { useNotificationsStore } from '@/stores/notifications-store';

export function NotificationBell() {
  const {
    notifications,
    unreadCount,
    isLoading,
    isDropdownOpen,
    setDropdownOpen,
    markAsRead,
    markAllAsRead,
    startPolling,
    stopPolling,
  } = useNotificationsStore();

  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  return (
    <Popover open={isDropdownOpen} onOpenChange={setDropdownOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative hover:bg-secondary transition-all hover-lift"
          title="Notificações"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-primary-foreground bg-destructive rounded-full">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-80 p-0"
        sideOffset={8}
      >
        <div className="flex items-center justify-between p-3 border-b">
          <h4 className="font-semibold text-sm">Notificações</h4>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={markAllAsRead}
            >
              <CheckCheck className="w-3 h-3 mr-1" />
              Marcar todas como lidas
            </Button>
          )}
        </div>

        <ScrollArea className="max-h-80">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Carregando...
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Nenhuma notificação
            </div>
          ) : (
            <div className="p-1">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={markAsRead}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
