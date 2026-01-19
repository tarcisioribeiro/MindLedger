import { useEffect, useRef, useCallback } from 'react';
import flatpickr from 'flatpickr';
import { Portuguese } from 'flatpickr/dist/l10n/pt';
import type { Options as FlatpickrOptions } from 'flatpickr/dist/types/options';
import { Calendar as CalendarIcon, X } from 'lucide-react';
import { cn, toLocalDate, formatLocalDate } from '@/lib/utils';

// Importa estilos customizados (sem usar os padrões do Flatpickr)
import '@/styles/flatpickr-custom.css';

interface DatePickerProps {
  value?: Date | string;
  onChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  clearable?: boolean;
}

// Parser customizado para formato DD/MM/YYYY
function parseDateBR(dateStr: string): Date | undefined {
  const match = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!match) return undefined;

  const day = parseInt(match[1], 10);
  const month = parseInt(match[2], 10) - 1;
  const year = parseInt(match[3], 10);

  const date = new Date(year, month, day);

  // Valida se a data é válida
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month ||
    date.getDate() !== day
  ) {
    return undefined;
  }

  return date;
}

/**
 * DatePicker component using Flatpickr
 * - Formato DD/MM/YYYY
 * - Localização pt-BR
 * - Permite digitação manual com validação
 * - Estilização customizada para temas Dracula/Alucard
 */
export function DatePicker({
  value,
  onChange,
  placeholder = 'Selecione uma data',
  disabled = false,
  className,
  clearable = true,
}: DatePickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const flatpickrRef = useRef<flatpickr.Instance | null>(null);

  // Converte value para Date
  const dateValue = toLocalDate(value);

  // Callback para mudança de data
  const handleChange = useCallback(
    (selectedDates: Date[]) => {
      if (selectedDates.length > 0) {
        onChange?.(selectedDates[0]);
      } else {
        onChange?.(undefined);
      }
    },
    [onChange]
  );

  // Inicializa Flatpickr
  useEffect(() => {
    if (!inputRef.current) return;

    const options: Partial<FlatpickrOptions> = {
      locale: Portuguese,
      dateFormat: 'd/m/Y',
      allowInput: true,
      clickOpens: !disabled,
      disableMobile: true,
      defaultDate: dateValue,
      onChange: handleChange,
      // Posiciona o calendário abaixo do input usando posicionamento inline
      // Isso garante que o calendário fique sempre junto ao campo
      static: true,
      wrap: false,
      // Posição abaixo do input
      positionElement: inputRef.current || undefined,
      // Parser customizado para aceitar DD/MM/YYYY digitado manualmente
      parseDate: (dateStr: string) => {
        const parsed = parseDateBR(dateStr);
        // Retorna data válida ou data inválida (que será ignorada pelo Flatpickr)
        return parsed ?? new Date(NaN);
      },
      onReady: (_selectedDates, _dateStr, instance) => {
        instance.calendarContainer.classList.add('flatpickr-calendar-custom');
      },
      // Validação ao fechar - mostra erro visual se data inválida
      onClose: (_selectedDates, dateStr, instance) => {
        if (dateStr && !parseDateBR(dateStr)) {
          instance.input.classList.add('flatpickr-invalid');
          setTimeout(() => {
            instance.input.classList.remove('flatpickr-invalid');
          }, 1500);
        }
      },
    };

    flatpickrRef.current = flatpickr(inputRef.current, options);

    return () => {
      flatpickrRef.current?.destroy();
    };
  }, [disabled, handleChange]);

  // Atualiza data quando value muda externamente
  useEffect(() => {
    if (flatpickrRef.current) {
      const currentDate = flatpickrRef.current.selectedDates[0];
      const newDate = dateValue;

      // Só atualiza se a data realmente mudou
      if (newDate && (!currentDate || formatLocalDate(currentDate) !== formatLocalDate(newDate))) {
        flatpickrRef.current.setDate(newDate, false);
      } else if (!newDate && currentDate) {
        flatpickrRef.current.clear(false);
      }
    }
  }, [dateValue]);

  // Handler para limpar a data
  const handleClear = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    flatpickrRef.current?.clear();
    onChange?.(undefined);
  };

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {/* Ícone do calendário */}
      <CalendarIcon
        className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-primary/70 pointer-events-none z-10"
      />

      {/* Input do Flatpickr */}
      <input
        ref={inputRef}
        type="text"
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'flatpickr-input',
          'w-full h-10 pl-10 pr-10 py-2',
          'bg-background border border-input rounded-md',
          'text-sm text-foreground placeholder:text-foreground',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary',
          'transition-all duration-200',
          'hover:border-primary/40',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      />

      {/* Botão para limpar */}
      {clearable && dateValue && !disabled && (
        <button
          type="button"
          onClick={handleClear}
          className={cn(
            'absolute right-3 top-1/2 -translate-y-1/2 z-10',
            'h-5 w-5 rounded-full',
            'flex items-center justify-center',
            'hover:text-destructive',
            'hover:bg-destructive/10',
            'transition-colors duration-150'
          )}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
