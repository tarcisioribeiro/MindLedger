// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:30001',
  ENDPOINTS: {
    // Authentication
    LOGIN: '/api/v1/authentication/token/',
    REFRESH_TOKEN: '/api/v1/authentication/token/refresh/',
    VERIFY_TOKEN: '/api/v1/authentication/token/verify/',
    REGISTER: '/api/v1/users/register/',
    USER_PERMISSIONS: '/api/v1/user/permissions/',

    // Resources
    ACCOUNTS: '/api/v1/accounts/',
    EXPENSES: '/api/v1/expenses/',
    FIXED_EXPENSES: '/api/v1/fixed-expenses/',
    REVENUES: '/api/v1/revenues/',
    CREDIT_CARDS: '/api/v1/credit-cards/',
    CREDIT_CARD_BILLS: '/api/v1/credit-cards-bills/',
    CREDIT_CARD_EXPENSES: '/api/v1/credit-cards-expenses/',
    TRANSFERS: '/api/v1/transfers/',
    LOANS: '/api/v1/loans/',
    MEMBERS: '/api/v1/members/',
    CURRENT_USER_MEMBER: '/api/v1/members/me/',
    AVAILABLE_PERMISSIONS: '/api/v1/permissions/available/',

    // Security Module
    PASSWORDS: '/api/v1/security/passwords/',
    STORED_CARDS: '/api/v1/security/stored-cards/',
    STORED_ACCOUNTS: '/api/v1/security/stored-accounts/',
    ARCHIVES: '/api/v1/security/archives/',
    ACTIVITY_LOGS: '/api/v1/security/activity-logs/',

    // Library Module
    AUTHORS: '/api/v1/library/authors/',
    PUBLISHERS: '/api/v1/library/publishers/',
    BOOKS: '/api/v1/library/books/',
    SUMMARIES: '/api/v1/library/summaries/',
    READINGS: '/api/v1/library/readings/',

    // AI Assistant
    AI_QUERY: '/api/v1/ai/query/',
    AI_STREAM: '/api/v1/ai/stream/',

    // Health
    HEALTH: '/api/v1/health/',
  },
};

// Token Configuration
export const TOKEN_CONFIG = {
  ACCESS_TOKEN_LIFETIME: 15 * 60 * 1000, // 15 minutes
  REFRESH_TOKEN_LIFETIME: 60 * 60 * 1000, // 1 hour
  COOKIE_EXPIRE_DAYS: 7,
};

// Translations - English (API) to Portuguese (UI)
export const TRANSLATIONS = {
  // Account Types
  accountTypes: {
    CC: 'Conta Corrente',
    CS: 'Conta Salário',
    FG: 'Fundo de Garantia',
    VA: 'Vale Alimentação',
    VR: 'Vale Refeição',
    CP: 'Conta Poupança',
  },

  // Institutions
  institutions: {
    NUB: 'Nubank',
    SIC: 'Sicoob',
    MPG: 'Mercado Pago',
    IFB: 'Ifood Benefícios',
    CEF: 'Caixa Econômica Federal',
    BB: 'Banco do Brasil',
    SAN: 'Santander',
    ITA: 'Itaú',
    BRA: 'Bradesco',
    INT: 'Inter',
    C6B: 'C6 Bank',
    PIC: 'PicPay',
  },

  // Expense Categories
  expenseCategories: {
    'food and drink': 'Comida e Bebida',
    'bills and services': 'Contas e Serviços',
    electronics: 'Eletrônicos',
    'family and friends': 'Amizades e Família',
    pets: 'Animais de Estimação',
    'digital signs': 'Assinaturas Digitais',
    house: 'Casa',
    purchases: 'Compras',
    donate: 'Doações',
    education: 'Educação',
    loans: 'Empréstimos',
    entertainment: 'Entretenimento',
    taxes: 'Impostos',
    investments: 'Investimentos',
    others: 'Outros',
    vestuary: 'Roupas',
    'health and care': 'Saúde e Cuidados Pessoais',
    'professional services': 'Serviços Profissionais',
    supermarket: 'Supermercado',
    rates: 'Taxas',
    transport: 'Transporte',
    travels: 'Viagens',
  },

  // Revenue Categories
  revenueCategories: {
    deposit: 'Depósito',
    award: 'Prêmio',
    salary: 'Salário',
    ticket: 'Vale',
    income: 'Rendimentos',
    refund: 'Reembolso',
    cashback: 'Cashback',
    transfer: 'Transferência Recebida',
    received_loan: 'Empréstimo Recebido',
    loan_devolution: 'Devolução de Empréstimo',
  },

  // Card Brands
  cardBrands: {
    MSC: 'Master Card',
    VSA: 'Visa',
    ELO: 'Elo',
    EXP: 'American Express',
    HCD: 'Hipercard',
    DIN: 'Diners Club',
  },

  // Transfer Types
  transferTypes: {
    doc: 'DOC',
    ted: 'TED',
    pix: 'PIX',
    internal: 'Transferência Interna',
  },

  // Payment Status
  paymentStatus: {
    pending: 'Pendente',
    paid: 'Pago',
    overdue: 'Atrasado',
    cancelled: 'Cancelado',
  },

  // Loan Status
  loanStatus: {
    active: 'Ativo',
    paid: 'Pago',
    overdue: 'Atrasado',
    cancelled: 'Cancelado',
  },

  // Member Types
  memberTypes: {
    user: 'Usuário',
    creditor: 'Credor',
    beneficiary: 'Beneficiário',
    both: 'Ambos',
    other: 'Outro',
  },

  // Bill Status
  billStatus: {
    open: 'Aberta',
    closed: 'Fechada',
    paid: 'Paga',
    overdue: 'Em Atraso',
  },

  // Months
  months: {
    Jan: 'Janeiro',
    Feb: 'Fevereiro',
    Mar: 'Março',
    Apr: 'Abril',
    May: 'Maio',
    Jun: 'Junho',
    Jul: 'Julho',
    Aug: 'Agosto',
    Sep: 'Setembro',
    Oct: 'Outubro',
    Nov: 'Novembro',
    Dec: 'Dezembro',
  },

  // Payment Frequency
  paymentFrequency: {
    daily: 'Diário',
    weekly: 'Semanal',
    biweekly: 'Quinzenal',
    monthly: 'Mensal',
    bimonthly: 'Bimestral',
    quarterly: 'Trimestral',
    semiannual: 'Semestral',
    annual: 'Anual',
  },
};

// Reverse translations - Portuguese to English
export const REVERSE_TRANSLATIONS = {
  accountTypes: Object.fromEntries(
    Object.entries(TRANSLATIONS.accountTypes).map(([k, v]) => [v, k])
  ),
  institutions: Object.fromEntries(
    Object.entries(TRANSLATIONS.institutions).map(([k, v]) => [v, k])
  ),
  expenseCategories: Object.fromEntries(
    Object.entries(TRANSLATIONS.expenseCategories).map(([k, v]) => [v, k])
  ),
  revenueCategories: Object.fromEntries(
    Object.entries(TRANSLATIONS.revenueCategories).map(([k, v]) => [v, k])
  ),
  cardBrands: Object.fromEntries(
    Object.entries(TRANSLATIONS.cardBrands).map(([k, v]) => [v, k])
  ),
  transferTypes: Object.fromEntries(
    Object.entries(TRANSLATIONS.transferTypes).map(([k, v]) => [v, k])
  ),
  paymentStatus: Object.fromEntries(
    Object.entries(TRANSLATIONS.paymentStatus).map(([k, v]) => [v, k])
  ),
  loanStatus: Object.fromEntries(
    Object.entries(TRANSLATIONS.loanStatus).map(([k, v]) => [v, k])
  ),
  memberTypes: Object.fromEntries(
    Object.entries(TRANSLATIONS.memberTypes).map(([k, v]) => [v, k])
  ),
  billStatus: Object.fromEntries(
    Object.entries(TRANSLATIONS.billStatus).map(([k, v]) => [v, k])
  ),
  months: Object.fromEntries(
    Object.entries(TRANSLATIONS.months).map(([k, v]) => [v, k])
  ),
  paymentFrequency: Object.fromEntries(
    Object.entries(TRANSLATIONS.paymentFrequency).map(([k, v]) => [v, k])
  ),
};

// Helper function to translate
export const translate = (
  category: keyof typeof TRANSLATIONS,
  key: string
): string => {
  return TRANSLATIONS[category][key as keyof typeof TRANSLATIONS[typeof category]] || key;
};

// Helper function to reverse translate
export const reverseTranslate = (
  category: keyof typeof REVERSE_TRANSLATIONS,
  value: string
): string => {
  return REVERSE_TRANSLATIONS[category][value as keyof typeof REVERSE_TRANSLATIONS[typeof category]] || value;
};
