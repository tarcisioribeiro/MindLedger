import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebar } from '@/hooks/use-sidebar';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Users,
  Lock,
  X,
  Wallet,
  Shield,
  Library,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface NavSubItem {
  title: string;
  href: string;
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
    icon: <LayoutDashboard className="w-5 h-5" />,
  },
  {
    title: 'Membros',
    href: '/members',
    icon: <Users className="w-5 h-5" />,
    permission: { appName: 'member', action: 'view' },
  },
  {
    title: 'Gerenciar Permissões',
    href: '/permissions',
    icon: <Lock className="w-5 h-5" />,
  },
];

const navModules: NavModule[] = [
  {
    title: 'ExpenseLit',
    icon: <Wallet className="w-5 h-5" />,
    items: [
      { title: 'Dashboard', href: '/dashboard' },
      { title: 'Contas', href: '/accounts' },
      { title: 'Despesas', href: '/expenses' },
      { title: 'Receitas', href: '/revenues' },
      { title: 'Cartões de Crédito', href: '/credit-cards' },
      { title: 'Faturas', href: '/credit-card-bills' },
      { title: 'Gastos do Cartão', href: '/credit-card-expenses' },
      { title: 'Transferências', href: '/transfers' },
      { title: 'Empréstimos', href: '/loans' },
    ],
  },
  {
    title: 'Streamfort',
    icon: <Shield className="w-5 h-5" />,
    items: [
      { title: 'Senhas', href: '/security/passwords' },
      { title: 'Cartões Armazenados', href: '/security/stored-cards' },
      { title: 'Contas Armazenadas', href: '/security/stored-accounts' },
      { title: 'Arquivos', href: '/security/archives' },
      { title: 'Logs de Atividade', href: '/security/activity-logs' },
    ],
  },
  {
    title: 'CodexDB',
    icon: <Library className="w-5 h-5" />,
    items: [
      { title: 'Livros', href: '/library/books' },
      { title: 'Autores', href: '/library/authors' },
      { title: 'Editoras', href: '/library/publishers' },
      { title: 'Resumos', href: '/library/summaries' },
      { title: 'Leituras', href: '/library/readings' },
    ],
  },
];

export const Sidebar = () => {
  const location = useLocation();
  const { hasPermission } = useAuthStore();
  const { isOpen, close } = useSidebar();
  // Inicializar com todos os módulos expandidos por padrão
  const [expandedModules, setExpandedModules] = useState<string[]>(
    navModules.map(module => module.title)
  );

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

      <nav className="space-y-2 flex-1 overflow-y-auto">
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
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
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
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
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
                            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                        )}
                      >
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
