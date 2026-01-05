import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formata uma data para string YYYY-MM-DD sem conversão de timezone
 * Evita o bug de selecionar dia anterior ao usar toISOString()
 */
export function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Parse uma string de data no formato YYYY-MM-DD, incluindo anos negativos (AC)
 * Retorna undefined se a data for inválida
 */
export function parseLocalDate(dateStr: string): Date | undefined {
  if (!dateStr || dateStr.trim() === '') return undefined;

  // Suporta formato YYYY-MM-DD com anos negativos (ex: -0384-MM-DD)
  const match = dateStr.match(/^(-?\d+)-(\d{2})-(\d{2})$/);
  if (!match) return undefined;

  const year = parseInt(match[1], 10);
  const month = parseInt(match[2], 10) - 1; // JavaScript months are 0-indexed
  const day = parseInt(match[3], 10);

  const date = new Date(year, month, day);

  // Validar se a data é válida
  if (date.getFullYear() !== year || date.getMonth() !== month || date.getDate() !== day) {
    return undefined;
  }

  return date;
}
