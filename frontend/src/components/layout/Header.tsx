import { useAuthStore } from '@/stores/auth-store';
import { useSidebar } from '@/hooks/use-sidebar';
import { Button } from '@/components/ui/button';
import { LogOut, Moon, Sun, Menu } from 'lucide-react';
import { useState, useEffect } from 'react';
import { membersService } from '@/services/members-service';
import type { Member } from '@/types';

export const Header = () => {
  const { user, logout } = useAuthStore();
  const { toggle } = useSidebar();
  const [darkMode, setDarkMode] = useState(true);
  const [currentMember, setCurrentMember] = useState<Member | null>(null);

  useEffect(() => {
    // Check system preference first, then localStorage
    const savedTheme = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme !== null ? savedTheme !== 'false' : prefersDark;

    setDarkMode(isDark);
    updateTheme(isDark);
  }, []);

  useEffect(() => {
    // Carregar o membro do usuário logado
    const loadCurrentMember = async () => {
      if (user) {
        try {
          const member = await membersService.getCurrentUserMember();
          setCurrentMember(member);
        } catch (error) {
          console.error('Erro ao carregar membro do usuário:', error);
        }
      }
    };

    loadCurrentMember();
  }, [user]);

  const updateTheme = (isDark: boolean) => {
    const root = document.documentElement;

    // Add transition class for smooth theme change
    root.classList.add('transition-colors', 'duration-300');

    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Remove transition class after animation
    setTimeout(() => {
      root.classList.remove('transition-colors', 'duration-300');
    }, 300);
  };

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', String(newDarkMode));
    updateTheme(newDarkMode);
  };

  return (
    <header className="bg-card border-b px-4 lg:px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Botão Hamburger (apenas mobile) */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          className="lg:hidden mr-2"
          aria-label="Abrir menu"
        >
          <Menu className="w-5 h-5" />
        </Button>

        <div className="flex-1 lg:flex-none">
          <h2 className="text-lg font-semibold">
            Bem-vindo, {currentMember ? currentMember.name.split(' ')[0] : user?.username || 'Usuário'}!
          </h2>
          <p className="text-sm text-muted-foreground hidden sm:block">
            Gerencie suas finanças de forma inteligente
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
            title={darkMode ? 'Mudar para Modo Claro' : 'Mudar para Modo Escuro'}
            className="relative overflow-hidden hover:bg-secondary transition-all hover-lift"
          >
            <div className="relative">
              {darkMode ? (
                <Sun className="w-5 h-5 text-amber-500 transition-transform rotate-0 hover:rotate-180 duration-500" />
              ) : (
                <Moon className="w-5 h-5 text-primary transition-transform rotate-0 hover:rotate-[-15deg] duration-300" />
              )}
            </div>
          </Button>

          <Button
            variant="outline"
            onClick={logout}
            className="flex items-center gap-2 hover-lift"
          >
            <LogOut className="w-4 h-4" />
            Sair
          </Button>
        </div>
      </div>
    </header>
  );
};
