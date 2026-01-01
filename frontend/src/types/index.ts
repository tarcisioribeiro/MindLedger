// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Authentication Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  groups: string[];
}

export interface Permission {
  app_label: string;
  codename: string;
  name: string;
}

// Account Types
export interface Account {
  id: number;
  uuid: string;
  account_name: string;
  account_type: string;
  institution: string;
  account_number_masked: string;
  balance: string;
  created_at: string;
  updated_at: string;
  owner: number;
  owner_name?: string;
}

export interface AccountFormData {
  account_name: string;
  account_type: string;
  institution: string;
  account_number: string;
  balance: number;
  owner: number;
}

// Expense Types
export interface Expense {
  id: number;
  uuid: string;
  description: string;
  value: string;
  date: string;
  horary: string;
  category: string;
  payed: boolean;
  account: number;
  account_name?: string;
  member: number | null;
  member_name?: string;
  merchant?: string;
  location?: string;
  payment_method?: string;
  notes?: string;
  recurring?: boolean;
  frequency?: string;
  created_at: string;
  updated_at: string;
}

export interface ExpenseFormData {
  description: string;
  value: number;
  date: string;
  horary: string;
  category: string;
  payed: boolean;
  account: number;
  member?: number | null;
  merchant?: string;
  location?: string;
  payment_method?: string;
  notes?: string;
  recurring?: boolean;
  frequency?: string;
}

// Revenue Types
export interface Revenue {
  id: number;
  description: string;
  value: string;
  date: string;
  horary: string;
  category: string;
  account: number;
  account_name?: string;
  current_balance?: string;
  received: boolean;
  source?: string;
  tax_amount?: string;
  net_amount?: string;
  member?: number | null;
  member_name?: string;
  receipt?: string | null;
  recurring?: boolean;
  frequency?: string | null;
  notes?: string;
}

export interface RevenueFormData {
  description: string;
  value: number;
  date: string;
  horary: string;
  category: string;
  account: number;
  received: boolean;
  source?: string;
  tax_amount?: number;
  member?: number | null;
  receipt?: string | null;
  recurring?: boolean;
  frequency?: string | null;
  notes?: string;
}

// Credit Card Types
export interface CreditCard {
  id: number;
  uuid: string;
  name: string;
  on_card_name: string;
  card_number_masked: string;
  flag: string;
  validation_date: string;
  credit_limit: string;
  max_limit: string;
  due_day: number;
  closing_day: number;
  associated_account: number;
  associated_account_name?: string;
  is_active: boolean;
  interest_rate?: string;
  annual_fee?: string;
  owner?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreditCardFormData {
  name: string;
  on_card_name: string;
  card_number: string;
  flag: string;
  security_code: string;
  validation_date: string;
  credit_limit: number;
  max_limit: number;
  due_day: number;
  closing_day: number;
  associated_account: number;
  is_active?: boolean;
  interest_rate?: number;
  annual_fee?: number;
  owner?: number;
  notes?: string;
}

// Credit Card Bill Types
export interface CreditCardBill {
  id: number;
  uuid: string;
  credit_card: number;
  credit_card_name?: string;
  year: string;
  month: string;
  invoice_beginning_date: string;
  invoice_ending_date: string;
  closed: boolean;
  total_amount: string;
  minimum_payment: string;
  due_date: string | null;
  paid_amount: string;
  payment_date: string | null;
  interest_charged: string;
  late_fee: string;
  status: 'open' | 'closed' | 'paid' | 'overdue';
  created_at: string;
  updated_at: string;
}

export interface CreditCardBillFormData {
  credit_card: number;
  year: string;
  month: string;
  invoice_beginning_date: string;
  invoice_ending_date: string;
  closed: boolean;
  total_amount: number;
  minimum_payment: number;
  due_date?: string;
  paid_amount?: number;
  payment_date?: string;
  interest_charged?: number;
  late_fee?: number;
  status?: 'open' | 'closed' | 'paid' | 'overdue';
}

// Credit Card Expense Types
export interface CreditCardExpense {
  id: number;
  uuid: string;
  description: string;
  value: string;
  date: string;
  horary: string;
  category: string;
  card: number;
  card_name?: string;
  installment: number;
  payed: boolean;
  total_installments: number;
  merchant?: string;
  transaction_id?: string;
  location?: string;
  bill?: number | null;
  bill_info?: string;
  member?: number | null;
  member_name?: string;
  notes?: string;
  receipt?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreditCardExpenseFormData {
  description: string;
  value: number;
  date: string;
  horary: string;
  category: string;
  card: number;
  installment: number;
  payed: boolean;
  total_installments: number;
  merchant?: string;
  transaction_id?: string;
  location?: string;
  bill?: number | null;
  member?: number | null;
  notes?: string;
}

// Transfer Types
export interface Transfer {
  id: number;
  uuid: string;
  description: string;
  value: string;
  date: string;
  horary: string;
  category: string;
  transfered: boolean;
  origin_account: number;
  origin_account_name?: string;
  destiny_account: number;
  destiny_account_name?: string;
  created_at: string;
  updated_at: string;
}

export interface TransferFormData {
  description: string;
  value: number;
  date: string;
  horary: string;
  category: string;
  transfered: boolean;
  origin_account: number;
  destiny_account: number;
}

// Loan Types
export interface Loan {
  id: number;
  uuid: string;
  description: string;
  value: string;
  payed_value: string;
  date: string;
  horary: string;
  category: string;
  account: number;
  account_name?: string;
  benefited: number;
  benefited_name?: string;
  creditor: number;
  creditor_name?: string;
  payed: boolean;
  interest_rate?: string;
  installments: number;
  due_date?: string;
  contract_document?: string | null;
  payment_frequency: string;
  late_fee: string;
  guarantor?: number | null;
  guarantor_name?: string;
  notes?: string;
  status: string;
  created_at: string;
  updated_at: string;
  created_by?: number;
  updated_by?: number;
}

export interface LoanFormData {
  description: string;
  value: number;
  payed_value: number;
  date: string;
  horary: string;
  category: string;
  account: number;
  benefited: number;
  creditor: number;
  payed: boolean;
  interest_rate?: number;
  installments?: number;
  due_date?: string;
  contract_document?: File | null;
  payment_frequency?: string;
  late_fee?: number;
  guarantor?: number | null;
  notes?: string;
  status?: string;
}

// Member Types
export interface Member {
  id: number;
  uuid: string;
  member_name: string;
  member_type: string;
  user: number | null;
  created_at: string;
  updated_at: string;
}

export interface MemberFormData {
  member_name: string;
  member_type: string;
}

// API Error Types
export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}

// Dashboard/Analytics Types
export interface DashboardStats {
  total_balance: number;
  total_expenses: number;
  total_revenues: number;
  total_credit_limit: number;
  accounts_count: number;
  credit_cards_count: number;
}

export interface ChartData {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesData {
  date: string;
  expenses: number;
  revenues: number;
}

// ============================================================================
// SECURITY MODULE TYPES
// ============================================================================

// Password Types
export interface Password {
  id: number;
  uuid: string;
  title: string;
  site?: string;
  username: string;
  category: string;
  category_display: string;
  notes?: string;
  last_password_change: string;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface PasswordFormData {
  title: string;
  site?: string;
  username: string;
  password: string;
  category: string;
  notes?: string;
  owner: number;
}

export interface PasswordReveal {
  id: number;
  title: string;
  username: string;
  password: string;
}

// Stored Credit Card Types
export interface StoredCreditCard {
  id: number;
  uuid: string;
  name: string;
  card_number_masked: string;
  last_four_digits?: string;
  cardholder_name: string;
  expiration_month: number;
  expiration_year: number;
  flag: string;
  flag_display: string;
  notes?: string;
  owner: number;
  owner_name: string;
  finance_card?: number | null;
  finance_card_name?: string;
  created_at: string;
  updated_at: string;
}

export interface StoredCreditCardFormData {
  name: string;
  card_number: string;
  security_code: string;
  cardholder_name: string;
  expiration_month: number;
  expiration_year: number;
  flag: string;
  notes?: string;
  owner: number;
  finance_card?: number | null;
}

export interface StoredCreditCardReveal {
  id: number;
  name: string;
  card_number: string;
  security_code: string;
  cardholder_name: string;
  expiration_month: number;
  expiration_year: number;
}

// Stored Bank Account Types
export interface StoredBankAccount {
  id: number;
  uuid: string;
  name: string;
  institution_name: string;
  account_type: string;
  account_type_display: string;
  account_number?: string;
  account_number_masked: string;
  agency?: string;
  notes?: string;
  owner: number;
  owner_name: string;
  finance_account?: number | null;
  finance_account_name?: string;
  created_at: string;
  updated_at: string;
}

export interface StoredBankAccountFormData {
  name: string;
  institution_name: string;
  account_type: string;
  account_number: string;
  agency?: string;
  password?: string;
  digital_password?: string;
  notes?: string;
  owner: number;
  finance_account?: number | null;
}

export interface StoredBankAccountReveal {
  id: number;
  name: string;
  institution_name: string;
  account_number: string;
  agency?: string;
  password?: string;
  password2?: string;
  digital_password?: string;
}

// Archive Types
export interface Archive {
  id: number;
  uuid: string;
  title: string;
  category: string;
  category_display: string;
  archive_type: string;
  archive_type_display: string;
  text_content?: string;
  file_name?: string;
  file_size?: number;
  notes?: string;
  tags?: string;
  has_text: boolean;
  has_file: boolean;
  encrypted_file?: string | null;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface ArchiveFormData {
  title: string;
  category: string;
  archive_type: string;
  text_content?: string;
  encrypted_file?: File | null;
  notes?: string;
  tags?: string;
  owner: number;
}

export interface ArchiveReveal {
  id: number;
  title: string;
  text_content?: string;
}

// Activity Log Types
export interface ActivityLog {
  id: number;
  action: string;
  action_display: string;
  model_name?: string;
  object_id?: number;
  description: string;
  ip_address?: string;
  user_agent?: string;
  user?: number;
  username?: string;
  created_at: string;
}

// Security Module Constants
export const PASSWORD_CATEGORIES = [
  { value: 'social', label: 'Redes Sociais' },
  { value: 'email', label: 'E-mail' },
  { value: 'banking', label: 'Bancário' },
  { value: 'work', label: 'Trabalho' },
  { value: 'entertainment', label: 'Entretenimento' },
  { value: 'shopping', label: 'Compras' },
  { value: 'streaming', label: 'Streaming' },
  { value: 'gaming', label: 'Games' },
  { value: 'other', label: 'Outro' },
];

export const CARD_FLAGS = [
  { value: 'MSC', label: 'Mastercard' },
  { value: 'VSA', label: 'Visa' },
  { value: 'ELO', label: 'Elo' },
  { value: 'EXP', label: 'American Express' },
  { value: 'HCD', label: 'Hipercard' },
  { value: 'DIN', label: 'Diners Club' },
  { value: 'OTHER', label: 'Outro' },
];

export const ACCOUNT_TYPES = [
  { value: 'CC', label: 'Conta Corrente' },
  { value: 'CS', label: 'Conta Salário' },
  { value: 'CP', label: 'Conta Poupança' },
  { value: 'CI', label: 'Conta Investimento' },
  { value: 'OTHER', label: 'Outro' },
];

export const ARCHIVE_CATEGORIES = [
  { value: 'personal', label: 'Pessoal' },
  { value: 'financial', label: 'Financeiro' },
  { value: 'legal', label: 'Jurídico' },
  { value: 'medical', label: 'Médico' },
  { value: 'tax', label: 'Impostos' },
  { value: 'work', label: 'Trabalho' },
  { value: 'other', label: 'Outro' },
];

export const ARCHIVE_TYPES = [
  { value: 'text', label: 'Texto' },
  { value: 'pdf', label: 'PDF' },
  { value: 'image', label: 'Imagem' },
  { value: 'document', label: 'Documento' },
  { value: 'other', label: 'Outro' },
];

// ============================================================================
// LIBRARY MODULE TYPES
// ============================================================================

// Author Types
export interface Author {
  id: number;
  uuid: string;
  name: string;
  birthday?: string;
  death_date?: string;
  nationality?: string;
  nationality_display?: string;
  biography?: string;
  books_count: number;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface AuthorFormData {
  name: string;
  birthday?: string;
  death_date?: string;
  nationality?: string;
  biography?: string;
  owner: number;
}

// Publisher Types
export interface Publisher {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  website?: string;
  country?: string;
  country_display?: string;
  founded_year?: number;
  books_count: number;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface PublisherFormData {
  name: string;
  description?: string;
  website?: string;
  country?: string;
  founded_year?: number;
  owner: number;
}

// Book Types
export interface Book {
  id: number;
  uuid: string;
  title: string;
  authors?: number[];
  authors_names: string[];
  pages: number;
  publisher: number;
  publisher_name: string;
  language: string;
  language_display: string;
  genre: string;
  genre_display: string;
  literarytype: string;
  literarytype_display: string;
  publish_date?: string;
  synopsis: string;
  edition: string;
  media_type?: string;
  media_type_display?: string;
  rating: number;
  read_status: string;
  read_status_display: string;
  has_summary: boolean;
  total_pages_read: number;
  reading_progress: number;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface BookFormData {
  title: string;
  authors: number[];
  pages: number;
  publisher: number;
  language: string;
  genre: string;
  literarytype: string;
  publish_date?: string;
  synopsis: string;
  edition: string;
  media_type?: string;
  rating: number;
  read_status: string;
  owner: number;
}

// Summary Types
export interface Summary {
  id: number;
  uuid: string;
  title: string;
  book: number;
  book_title: string;
  text: string;
  is_vectorized: boolean;
  vectorization_date?: string;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface SummaryFormData {
  title: string;
  book: number;
  text: string;
  owner: number;
}

// Reading Types
export interface Reading {
  id: number;
  uuid: string;
  book: number;
  book_title: string;
  reading_date: string;
  reading_time: number;
  pages_read: number;
  notes?: string;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface ReadingFormData {
  book: number;
  reading_date: string;
  reading_time: number;
  pages_read: number;
  notes?: string;
  owner: number;
}

// Library Module Constants
export const NATIONALITIES = [
  { value: 'USA', label: 'Americana' },
  { value: 'BRA', label: 'Brasileira' },
  { value: 'SUI', label: 'Suíça' },
  { value: 'ALE', label: 'Alemã' },
  { value: 'CZE', label: 'Checa' },
  { value: 'ISR', label: 'Israelense' },
  { value: 'AUS', label: 'Austríaca' },
  { value: 'ROM', label: 'Romana' },
  { value: 'GRE', label: 'Grega' },
  { value: 'FRA', label: 'Francesa' },
  { value: 'ING', label: 'Inglesa' },
  { value: 'CUB', label: 'Cubana' },
  { value: 'MEX', label: 'Mexicana' },
];

export const COUNTRIES = [
  { value: 'BRA', label: 'Brasil' },
  { value: 'USA', label: 'Estados Unidos da América' },
  { value: 'UK', label: 'Reino Unido' },
  { value: 'POR', label: 'Portugal' },
];

export const BOOK_LANGUAGES = [
  { value: 'Por', label: 'Português' },
  { value: 'Ing', label: 'Inglês' },
  { value: 'Esp', label: 'Espanhol' },
];

export const BOOK_GENRES = [
  { value: 'Philosophy', label: 'Filosofia' },
  { value: 'History', label: 'História' },
  { value: 'Psychology', label: 'Psicologia' },
  { value: 'Fiction', label: 'Ficção' },
  { value: 'Policy', label: 'Política' },
  { value: 'Technology', label: 'Tecnologia' },
  { value: 'Theology', label: 'Teologia' },
];

export const LITERARY_TYPES = [
  { value: 'book', label: 'Livro' },
  { value: 'collection', label: 'Coletânea' },
  { value: 'magazine', label: 'Revista' },
  { value: 'article', label: 'Artigo' },
  { value: 'essay', label: 'Ensaio' },
];

export const MEDIA_TYPES = [
  { value: 'Dig', label: 'Digital' },
  { value: 'Phi', label: 'Física' },
];

export const READ_STATUS = [
  { value: 'to_read', label: 'Para ler' },
  { value: 'reading', label: 'Lendo' },
  { value: 'read', label: 'Lido' },
];

// AI Assistant Types
export interface AIQueryRequest {
  question: string;
  top_k?: number;
}

export interface AISource {
  module: string;
  type: string;
  score: number;
  metadata: Record<string, any>;
}

export interface AIQueryResponse {
  answer: string;
  sources: AISource[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: AISource[];
}

// ============================================================================
// PERSONAL PLANNING MODULE TYPES
// ============================================================================

// Task Category Choices
export const TASK_CATEGORIES = [
  { value: 'health', label: 'Saude' },
  { value: 'studies', label: 'Estudos' },
  { value: 'spiritual', label: 'Espiritual' },
  { value: 'exercise', label: 'Exercicio Fisico' },
  { value: 'nutrition', label: 'Nutricao' },
  { value: 'meditation', label: 'Meditacao' },
  { value: 'reading', label: 'Leitura' },
  { value: 'writing', label: 'Escrita' },
  { value: 'work', label: 'Trabalho' },
  { value: 'leisure', label: 'Lazer' },
  { value: 'family', label: 'Familia' },
  { value: 'social', label: 'Social' },
  { value: 'finance', label: 'Financas' },
  { value: 'household', label: 'Casa' },
  { value: 'personal_care', label: 'Cuidado Pessoal' },
  { value: 'other', label: 'Outros' }
] as const;

export const PERIODICITY_CHOICES = [
  { value: 'daily', label: 'Diaria' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'monthly', label: 'Mensal' }
] as const;

export const WEEKDAY_CHOICES = [
  { value: 0, label: 'Segunda-feira' },
  { value: 1, label: 'Terca-feira' },
  { value: 2, label: 'Quarta-feira' },
  { value: 3, label: 'Quinta-feira' },
  { value: 4, label: 'Sexta-feira' },
  { value: 5, label: 'Sabado' },
  { value: 6, label: 'Domingo' }
] as const;

export const GOAL_TYPE_CHOICES = [
  { value: 'consecutive_days', label: 'Dias Consecutivos' },
  { value: 'total_days', label: 'Total de Dias' },
  { value: 'avoid_habit', label: 'Evitar Habito' },
  { value: 'custom', label: 'Personalizado' }
] as const;

export const GOAL_STATUS_CHOICES = [
  { value: 'active', label: 'Ativo' },
  { value: 'completed', label: 'Concluido' },
  { value: 'failed', label: 'Falhou' },
  { value: 'cancelled', label: 'Cancelado' }
] as const;

export const MOOD_CHOICES = [
  { value: 'excellent', label: 'Excelente' },
  { value: 'good', label: 'Bom' },
  { value: 'neutral', label: 'Neutro' },
  { value: 'bad', label: 'Ruim' },
  { value: 'terrible', label: 'Pessimo' }
] as const;

// Routine Task Types
export interface RoutineTask {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  category: string;
  category_display: string;
  periodicity: string;
  periodicity_display: string;
  weekday?: number;
  weekday_display?: string;
  day_of_month?: number;
  is_active: boolean;
  target_quantity: number;
  unit: string;
  completion_rate: number;
  total_completions: number;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface RoutineTaskFormData {
  name: string;
  description?: string;
  category: string;
  periodicity: string;
  weekday?: number;
  day_of_month?: number;
  is_active: boolean;
  target_quantity: number;
  unit: string;
  owner: number;
}

// Daily Task Record Types
export interface DailyTaskRecord {
  id: number;
  uuid: string;
  task: number;
  task_name: string;
  task_category: string;
  task_target: number;
  task_unit: string;
  date: string;
  completed: boolean;
  quantity_completed: number;
  notes?: string;
  completed_at?: string;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface DailyTaskRecordFormData {
  task: number;
  date: string;
  completed: boolean;
  quantity_completed: number;
  notes?: string;
  owner: number;
}

// Task for Today (special endpoint response)
export interface TaskForToday {
  task_id: number;
  task_name: string;
  category: string;
  category_display: string;
  target_quantity: number;
  unit: string;
  record_id?: number;
  completed: boolean;
  quantity_completed: number;
  notes?: string;
}

export interface TasksForTodayResponse {
  date: string;
  tasks: TaskForToday[];
  total_tasks: number;
  completed_tasks: number;
}

// Goal Types
export interface Goal {
  id: number;
  uuid: string;
  title: string;
  description?: string;
  goal_type: string;
  goal_type_display: string;
  related_task?: number;
  related_task_name?: string;
  target_value: number;
  current_value: number;
  start_date: string;
  end_date?: string;
  status: string;
  status_display: string;
  progress_percentage: number;
  days_active: number;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface GoalFormData {
  title: string;
  description?: string;
  goal_type: string;
  related_task?: number;
  target_value: number;
  current_value: number;
  start_date: string;
  end_date?: string;
  status: string;
  owner: number;
}

// Daily Reflection Types
export interface DailyReflection {
  id: number;
  uuid: string;
  date: string;
  reflection: string;
  mood?: string;
  mood_display?: string;
  owner: number;
  owner_name: string;
  created_at: string;
  updated_at: string;
}

export interface DailyReflectionFormData {
  date: string;
  reflection: string;
  mood?: string;
  owner: number;
}

// Dashboard Stats
export interface PersonalPlanningDashboardStats {
  total_tasks: number;
  active_tasks: number;
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  completion_rate_7d: number;
  completion_rate_30d: number;
  current_streak: number;
  best_streak: number;
  tasks_by_category: Array<{
    category: string;
    category_display: string;
    count: number;
  }>;
  weekly_progress: Array<{
    date: string;
    total: number;
    completed: number;
    rate: number;
  }>;
  active_goals_progress: Array<{
    title: string;
    progress_percentage: number;
    current_value: number;
    target_value: number;
    days_active: number;
  }>;
}
