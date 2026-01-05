import { DayPicker, type DayPickerProps } from 'react-day-picker';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';

export type CalendarProps = DayPickerProps;

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn('p-4', className)}
      classNames={{
        months: 'flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0',
        month: 'space-y-4',
        caption: 'flex justify-center pt-1 relative items-center mb-1',
        caption_label: 'text-base font-semibold text-foreground tracking-tight',
        nav: 'space-x-1 flex items-center',
        nav_button: cn(
          buttonVariants({ variant: 'outline' }),
          'h-8 w-8 bg-transparent hover:bg-primary/10 hover:text-primary',
          'p-0 transition-all duration-200 border-transparent hover:border-primary/20',
          'rounded-lg'
        ),
        nav_button_previous: 'absolute left-1',
        nav_button_next: 'absolute right-1',
        table: 'w-full border-collapse space-y-1 mt-2',
        head_row: 'flex mb-2',
        head_cell:
          'text-muted-foreground/80 rounded-md w-10 font-medium text-xs uppercase tracking-wider',
        row: 'flex w-full mt-1',
        cell: cn(
          'h-10 w-10 text-center text-sm p-0 relative',
          '[&:has([aria-selected].day-range-end)]:rounded-r-lg',
          '[&:has([aria-selected].day-outside)]:bg-accent/50',
          '[&:has([aria-selected])]:bg-accent',
          'first:[&:has([aria-selected])]:rounded-l-lg',
          'last:[&:has([aria-selected])]:rounded-r-lg',
          'focus-within:relative focus-within:z-20'
        ),
        day: cn(
          buttonVariants({ variant: 'ghost' }),
          'h-10 w-10 p-0 font-normal rounded-lg',
          'transition-all duration-200',
          'hover:bg-primary/10 hover:text-primary hover:scale-110',
          'focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-1',
          'aria-selected:opacity-100'
        ),
        day_range_end: 'day-range-end',
        day_selected: cn(
          'bg-primary text-primary-foreground font-semibold',
          'hover:bg-primary hover:text-primary-foreground',
          'focus:bg-primary focus:text-primary-foreground',
          'shadow-md scale-110',
          'transition-all duration-200',
          'ring-2 ring-primary/30 ring-offset-2 ring-offset-background'
        ),
        day_today: cn(
          'bg-accent text-accent-foreground font-bold',
          'ring-2 ring-primary/40',
          'transition-all duration-200'
        ),
        day_outside:
          'day-outside text-muted-foreground/30 opacity-40 aria-selected:bg-accent/50 aria-selected:text-muted-foreground aria-selected:opacity-30',
        day_disabled: 'text-muted-foreground/20 opacity-20 line-through cursor-not-allowed',
        day_range_middle:
          'aria-selected:bg-accent aria-selected:text-accent-foreground',
        day_hidden: 'invisible',
        ...classNames,
      }}
      {...props}
    />
  );
}
Calendar.displayName = 'Calendar';

export { Calendar };
