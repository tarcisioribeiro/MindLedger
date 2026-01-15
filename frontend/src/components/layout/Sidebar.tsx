import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebar } from '@/hooks/use-sidebar';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  X,
  Wallet,
  Shield,
  Library,
  ChevronDown,
  ChevronRight,
  CreditCard,
  Receipt,
  ShoppingCart,
  TrendingDown,
  TrendingUp,
  ArrowLeftRight,
  HandCoins,
  Archive,
  Key,
  BookOpen,
  UserPen,
  Building2,
  BookMarked,
  FileText,
  Home,
  Bot,
  MessageSquare,
  Calendar,
  Target,
  CheckCircle2,
  Users,
} from 'lucide-react';

interface NavSubItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  permission?: {
    appName: string;
    action: string;
  };
}

interface NavModule {
  title: string;
  icon: React.ReactNode;
  items: NavSubItem[];
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  permission?: {
    appName: string;
    action: string;
  };
}

const navItems: NavItem[] = [
  {
    title: 'Início',
    href: '/',
    icon: <Home className="w-5 h-5" />,
  },
];

const navModules: NavModule[] = [
  {
    title: 'Planejamento Pessoal',
    icon: <Calendar className="w-5 h-5" />,
    items: [
      { title: 'Dashboard', href: '/planning/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { title: 'Checklist Diário', href: '/planning/daily', icon: <CheckCircle2 className="w-4 h-4" /> },
      { title: 'Tarefas Rotineiras', href: '/planning/routine-tasks', icon: <Calendar className="w-4 h-4" /> },
      { title: 'Objetivos', href: '/planning/goals', icon: <Target className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Controle Financeiro',
    icon: <Wallet className="w-5 h-5" />,
    items: [
      { title: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { title: 'Contas', href: '/accounts', icon: <Wallet className="w-4 h-4" /> },
      { title: 'Despesas', href: '/expenses', icon: <TrendingDown className="w-4 h-4" /> },
      { title: 'Gastos Fixos', href: '/fixed-expenses', icon: <Calendar className="w-4 h-4" /> },
      { title: 'Receitas', href: '/revenues', icon: <TrendingUp className="w-4 h-4" /> },
      { title: 'Cartões de Crédito', href: '/credit-cards', icon: <CreditCard className="w-4 h-4" /> },
      { title: 'Faturas', href: '/credit-card-bills', icon: <Receipt className="w-4 h-4" /> },
      { title: 'Gastos do Cartão', href: '/credit-card-expenses', icon: <ShoppingCart className="w-4 h-4" /> },
      { title: 'Transferências', href: '/transfers', icon: <ArrowLeftRight className="w-4 h-4" /> },
      { title: 'Empréstimos', href: '/loans', icon: <HandCoins className="w-4 h-4" /> },
      { title: 'Beneficiários/Credores', href: '/members', icon: <Users className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Segurança',
    icon: <Shield className="w-5 h-5" />,
    items: [
      { title: 'Dashboard', href: '/security/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { title: 'Senhas', href: '/security/passwords', icon: <Key className="w-4 h-4" /> },
      { title: 'Cartões Armazenados', href: '/security/stored-cards', icon: <CreditCard className="w-4 h-4" /> },
      { title: 'Contas Armazenadas', href: '/security/stored-accounts', icon: <Wallet className="w-4 h-4" /> },
      { title: 'Arquivos', href: '/security/archives', icon: <Archive className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Leitura',
    icon: <Library className="w-5 h-5" />,
    items: [
      { title: 'Dashboard', href: '/library/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { title: 'Livros', href: '/library/books', icon: <BookOpen className="w-4 h-4" /> },
      { title: 'Autores', href: '/library/authors', icon: <UserPen className="w-4 h-4" /> },
      { title: 'Editoras', href: '/library/publishers', icon: <Building2 className="w-4 h-4" /> },
      { title: 'Resumos', href: '/library/summaries', icon: <FileText className="w-4 h-4" /> },
      { title: 'Leituras', href: '/library/readings', icon: <BookMarked className="w-4 h-4" /> },
    ],
  },
  {
    title: 'Assistente de IA',
    icon: <Bot className="w-5 h-5" />,
    items: [
      { title: 'Chat', href: '/ai-assistant', icon: <MessageSquare className="w-4 h-4" /> },
    ],
  },
];

export const Sidebar = () => {
  const location = useLocation();
  const { hasPermission } = useAuthStore();
  const { isOpen, close } = useSidebar();
  // Inicializar com todos os módulos fechados por padrão
  const [expandedModules, setExpandedModules] = useState<string[]>([]);

  const filteredNavItems = navItems.filter((item) => {
    if (!item.permission) return true;
    return hasPermission(item.permission.appName, item.permission.action);
  });

  const toggleModule = (moduleTitle: string) => {
    setExpandedModules((prev) =>
      prev.includes(moduleTitle)
        ? prev.filter((title) => title !== moduleTitle)
        : [...prev, moduleTitle]
    );
  };

  const isModuleExpanded = (moduleTitle: string) => {
    return expandedModules.includes(moduleTitle);
  };

  // Auto-expand module if current route is within it
  useEffect(() => {
    navModules.forEach((module) => {
      const isActive = module.items.some((item) => location.pathname === item.href);
      if (isActive) {
        setExpandedModules((prev) =>
          prev.includes(module.title) ? prev : [...prev, module.title]
        );
      }
    });
  }, [location.pathname]);

  // Fechar sidebar ao mudar de rota em mobile
  useEffect(() => {
    close();
  }, [location.pathname, close]);

  // Prevenir scroll do body quando sidebar mobile está aberta
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  return (
    <>
      {/* Overlay para mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={close}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50',
          'w-64 bg-card border-r min-h-screen p-4',
          'flex flex-col',
          'transform transition-transform duration-300 ease-in-out lg:transform-none',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              PersonalHub
            </span>
          </Link>

          {/* Botão fechar (apenas mobile) */}
          <button
            onClick={close}
            className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
            aria-label="Fechar menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      <nav className="space-y-2 flex-1 overflow-y-auto custom-scrollbar">
        {/* Items principais */}
        {filteredNavItems.map((item) => {
          const isActive = location.pathname === item.href;

          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground font-medium'
                  : 'sidebar-text hover:bg-accent hover:text-accent-foreground'
              )}
            >
              {item.icon}
              <span>{item.title}</span>
            </Link>
          );
        })}

        {/* Divisória */}
        <div className="border-t my-2" />

        {/* Módulos com submenus */}
        {navModules.map((module) => {
          const isExpanded = isModuleExpanded(module.title);
          const hasActiveItem = module.items.some((item) => location.pathname === item.href);

          return (
            <div key={module.title} className="space-y-1">
              {/* Cabeçalho do módulo */}
              <button
                onClick={() => toggleModule(module.title)}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors w-full',
                  hasActiveItem
                    ? 'bg-accent text-accent-foreground font-medium'
                    : 'sidebar-text hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {module.icon}
                <span className="flex-1 text-left">{module.title}</span>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>

              {/* Subitens */}
              {isExpanded && (
                <div className="ml-4 space-y-1">
                  {module.items.map((item) => {
                    const isActive = location.pathname === item.href;

                    return (
                      <Link
                        key={item.href}
                        to={item.href}
                        className={cn(
                          'flex items-center gap-3 px-4 py-2 rounded-lg transition-colors text-sm',
                          isActive
                            ? 'bg-primary text-primary-foreground font-medium'
                            : 'sidebar-text hover:bg-accent hover:text-accent-foreground'
                        )}
                      >
                        {item.icon}
                        <span>{item.title}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
    </>
  );
};
