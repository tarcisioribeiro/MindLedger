import * as React from 'react';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface FormFieldProps {
  id: string;
  label: string;
  error?: string;
  required?: boolean;
  description?: string;
  children: React.ReactElement<React.HTMLProps<HTMLElement>>;
  className?: string;
}

/**
 * FormField wrapper que adiciona acessibilidade automaticamente.
 *
 * Features:
 * - aria-describedby linkando campo a mensagem de erro/descricao
 * - aria-invalid quando ha erro
 * - aria-required quando campo e obrigatorio
 * - IDs consistentes para label, erro e descricao
 *
 * Uso:
 * ```tsx
 * <FormField
 *   id="email"
 *   label="Email"
 *   error={errors.email?.message}
 *   required
 * >
 *   <Input {...register('email')} />
 * </FormField>
 * ```
 */
export function FormField({
  id,
  label,
  error,
  required,
  description,
  children,
  className,
}: FormFieldProps) {
  const errorId = `${id}-error`;
  const descriptionId = `${id}-description`;

  // Constroi aria-describedby baseado nas props presentes
  const describedByParts: string[] = [];
  if (error) describedByParts.push(errorId);
  if (description) describedByParts.push(descriptionId);
  const ariaDescribedBy = describedByParts.length > 0 ? describedByParts.join(' ') : undefined;

  // Clona o children (input) adicionando props de acessibilidade
  const enhancedChild = React.cloneElement(children, {
    id,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': ariaDescribedBy,
    'aria-required': required ? true : undefined,
  });

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-destructive ml-1" aria-hidden="true">*</span>}
      </Label>

      {enhancedChild}

      {description && !error && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}

      {error && (
        <p
          id={errorId}
          className="text-sm text-destructive"
          role="alert"
          aria-live="polite"
        >
          {error}
        </p>
      )}
    </div>
  );
}

export default FormField;
