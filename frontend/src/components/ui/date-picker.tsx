import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Calendar as CalendarIcon, X, Edit3 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { cn, formatLocalDate, parseLocalDate } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  clearable?: boolean;
}

export function DatePicker({
  value,
  onChange,
  placeholder = 'Selecione uma data',
  disabled = false,
  className,
  clearable = true,
}: DatePickerProps) {
  const [manualInput, setManualInput] = useState<string>('');
  const [isManualMode, setIsManualMode] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (value && !isManualMode) {
      setManualInput(formatLocalDate(value));
    }
  }, [value, isManualMode]);

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setManualInput('');
    onChange?.(undefined);
  };

  const handleManualInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    setManualInput(inputValue);

    // Parse e valida a data
    const parsedDate = parseLocalDate(inputValue);
    if (parsedDate) {
      onChange?.(parsedDate);
    } else if (inputValue.trim() === '') {
      onChange?.(undefined);
    }
  };

  const handleCalendarSelect = (date: Date | undefined) => {
    if (date) {
      const formattedDate = formatLocalDate(date);
      setManualInput(formattedDate);
      onChange?.(date);
      setOpen(false);
    }
  };

  const toggleMode = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsManualMode(!isManualMode);
  };

  // Formatação da data para exibição
  const formatDisplayDate = (date: Date): string => {
    const year = date.getFullYear();

    // Se for ano negativo (AC), formata diferente
    if (year < 0) {
      const absYear = Math.abs(year);
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${day}/${month}/${absYear} AC`;
    }

    // Usa date-fns para datas normais
    return format(date, 'PPP', { locale: ptBR });
  };

  if (isManualMode) {
    return (
      <div className="relative">
        <Input
          type="text"
          value={manualInput}
          onChange={handleManualInputChange}
          placeholder="AAAA-MM-DD (use - para AC: -0384-01-15)"
          disabled={disabled}
          className={cn(
            'pr-20',
            className
          )}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
          {clearable && manualInput && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 hover:bg-accent"
              onClick={handleClear}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 hover:bg-accent"
            onClick={toggleMode}
          >
            <CalendarIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-full justify-start text-left font-normal group relative',
            'transition-all duration-200',
            'hover:border-primary/40 hover:bg-accent/5',
            'focus-visible:ring-2 focus-visible:ring-primary/30',
            !value && 'text-muted-foreground',
            disabled && 'opacity-50 cursor-not-allowed',
            className
          )}
          disabled={disabled}
        >
          <CalendarIcon className="mr-2 h-4 w-4 text-primary/70 group-hover:text-primary transition-colors" />
          <AnimatePresence mode="wait">
            {value ? (
              <motion.span
                key="date-value"
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                transition={{ duration: 0.15 }}
                className="flex-1 font-medium"
              >
                {formatDisplayDate(value)}
              </motion.span>
            ) : (
              <motion.span
                key="date-placeholder"
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                transition={{ duration: 0.15 }}
                className="flex-1"
              >
                {placeholder}
              </motion.span>
            )}
          </AnimatePresence>
          <div className="flex items-center gap-1 ml-2">
            {clearable && value && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <X
                  className="h-4 w-4 opacity-0 group-hover:opacity-60 hover:opacity-100 transition-opacity hover:text-destructive"
                  onClick={handleClear}
                />
              </motion.div>
            )}
            <Edit3
              className="h-3.5 w-3.5 opacity-0 group-hover:opacity-50 hover:opacity-100 transition-opacity text-muted-foreground"
              onClick={toggleMode}
            />
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto p-0 border shadow-xl"
        align="start"
        sideOffset={8}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          <Calendar
            mode="single"
            selected={value}
            onSelect={handleCalendarSelect}
            initialFocus
            locale={ptBR}
          />
        </motion.div>
      </PopoverContent>
    </Popover>
  );
}
