# TODO - Módulo de Planejamento Pessoal

## ✅ Concluído

- [x] Backend completo (models, serializers, views, urls, admin, signals)
- [x] Integração no projeto (settings.py e urls.py)
- [x] Types TypeScript (interfaces e constants)
- [x] Validações Zod (schemas)
- [x] Services (5 arquivos de API client)

---

## 🚀 Tarefas Pendentes

### 1. Setup Inicial (Prioritário)

- [ ] **Executar migrations**
  ```bash
  docker-compose exec api python manage.py makemigrations personal_planning
  docker-compose exec api python manage.py migrate
  ```

- [ ] **Testar backend via Django Admin**
  - Criar algumas tarefas de teste
  - Criar um objetivo de teste
  - Verificar se endpoints estão funcionando

### 2. Componentes de Formulário

#### 2.1. RoutineTaskForm.tsx (Complexidade: Média)
**Arquivo**: `frontend/src/components/personal-planning/RoutineTaskForm.tsx`

**Requisitos**:
- [ ] Usar React Hook Form + zodResolver
- [ ] Schema: `routineTaskSchema`
- [ ] Campos básicos: name, description, category, periodicity, target_quantity, unit, is_active
- [ ] **Campos condicionais**:
  - weekday (Select) - só aparece se periodicity === 'weekly'
  - day_of_month (Input number) - só aparece se periodicity === 'monthly'
- [ ] useEffect para resetar weekday/day_of_month quando periodicity muda
- [ ] Usar componentes Radix: Input, Textarea, Select, Checkbox
- [ ] Props: `{ task?, onSubmit, onCancel, isLoading, defaultOwnerId }`

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/components/library/BookForm.tsx`

---

#### 2.2. GoalForm.tsx (Complexidade: Média)
**Arquivo**: `frontend/src/components/personal-planning/GoalForm.tsx`

**Requisitos**:
- [ ] Usar React Hook Form + zodResolver
- [ ] Schema: `goalSchema`
- [ ] Campos: title, description, goal_type, related_task, target_value, current_value, start_date, end_date, status
- [ ] Select de related_task (opcional) - carregar lista de RoutineTasks
- [ ] DatePicker para start_date e end_date
- [ ] Props: `{ goal?, routineTasks, onSubmit, onCancel, isLoading, defaultOwnerId }`

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/components/security/PasswordForm.tsx`

---

#### 2.3. DailyChecklistItem.tsx (Complexidade: Baixa)
**Arquivo**: `frontend/src/components/personal-planning/DailyChecklistItem.tsx`

**Requisitos**:
- [ ] Componente auxiliar para item do checklist
- [ ] Checkbox para marcar como cumprida
- [ ] Input numérico para quantity_completed
- [ ] Badge com categoria (com cores diferentes)
- [ ] Mostrar target_quantity e unit
- [ ] Props: `{ task: TaskForToday, onToggle, onQuantityChange }`

---

### 3. Páginas Principais

#### 3.1. PersonalPlanningDashboard.tsx (Complexidade: Alta)
**Arquivo**: `frontend/src/pages/PersonalPlanningDashboard.tsx`

**Requisitos**:
- [ ] useState: stats, isLoading
- [ ] useEffect: carregar `personalPlanningDashboardService.getStats()`
- [ ] PageHeader com título e ícone Target
- [ ] **Grid 4 colunas** - StatCards:
  - Tarefas Ativas (ícone CheckCircle2)
  - Objetivos Ativos (ícone Trophy)
  - Taxa de Cumprimento 7d (ícone TrendingUp)
  - Sequência Atual / Melhor (ícone Flame)
- [ ] **LineChart** (Recharts) - Progresso Semanal (stats.weekly_progress)
- [ ] **BarChart** (Recharts) - Tarefas por Categoria (stats.tasks_by_category)
- [ ] **Card com Lista** - Objetivos em Andamento com Progress bars
- [ ] **Card com Resumo** - Taxa de cumprimento 30 dias

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/pages/LibraryDashboard.tsx`

**Ícones necessários**: `import { Target, CheckCircle2, Trophy, TrendingUp, Flame } from 'lucide-react'`

---

#### 3.2. RoutineTasks.tsx (Complexidade: Média)
**Arquivo**: `frontend/src/pages/RoutineTasks.tsx`

**Requisitos**:
- [ ] useState: tasks, members, isLoading, selectedTask, isDialogOpen
- [ ] useEffect: carregar tasks e members em paralelo
- [ ] PageHeader com botão "Nova Tarefa"
- [ ] **DataTable** com colunas:
  - name
  - category_display
  - periodicity_display (+ weekday_display ou day_of_month se aplicável)
  - target_quantity + unit
  - completion_rate (com Badge colorido)
  - is_active (Badge verde/cinza)
  - Ações (editar, deletar)
- [ ] Dialog com RoutineTaskForm para criar/editar
- [ ] Confirmação antes de deletar (useAlertDialog)
- [ ] Toast para feedback
- [ ] Recarregar lista após operações

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/pages/Books.tsx`

---

#### 3.3. DailyChecklist.tsx (Complexidade: Alta)
**Arquivo**: `frontend/src/pages/DailyChecklist.tsx`

**Requisitos**:
- [ ] useState: selectedDate (default: hoje), tasksData, reflection, mood, isLoading, isSaving
- [ ] useEffect: carregar `dailyTaskRecordsService.getTasksForToday(selectedDate)` quando data muda
- [ ] **DatePicker** para selecionar data
- [ ] Mostrar: `{completed_tasks} de {total_tasks} tarefas cumpridas`
- [ ] **Lista de DailyChecklistItem** (mapear tasksData.tasks)
- [ ] **Card com Reflexão do Dia**:
  - Textarea para reflexão
  - Select para mood
- [ ] **Botão "Salvar"**:
  - Criar/atualizar DailyTaskRecord para cada tarefa modificada
  - Criar/atualizar DailyReflection se preenchida
  - Operações em batch (Promise.all)
- [ ] Recarregar dados após salvar

**Desafios**:
- [ ] Gerenciar estado local de cada tarefa (completed, quantity_completed)
- [ ] Enviar apenas tarefas modificadas
- [ ] Buscar DailyReflection existente para a data selecionada

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/pages/Expenses.tsx` (para padrão de formulário)

---

#### 3.4. Goals.tsx (Complexidade: Média)
**Arquivo**: `frontend/src/pages/Goals.tsx`

**Requisitos**:
- [ ] useState: goals, tasks, members, isLoading, selectedGoal, isDialogOpen
- [ ] useEffect: carregar goals, tasks e members em paralelo
- [ ] PageHeader com botão "Novo Objetivo"
- [ ] **DataTable** com colunas:
  - title
  - goal_type_display
  - related_task_name (se houver)
  - current_value / target_value
  - progress_percentage (Progress bar inline)
  - status_display (Badge colorido)
  - days_active
  - Ações (editar, deletar)
- [ ] Dialog com GoalForm para criar/editar
- [ ] Confirmação antes de deletar
- [ ] Filtro por status (ativo, concluído, etc.)

**Referência**: `/home/tarcisio/Development/PersonalHub/frontend/src/pages/Loans.tsx`

---

### 4. Integração de Rotas

#### 4.1. App.tsx
**Arquivo**: `frontend/src/App.tsx`

**Requisitos**:
- [ ] **Adicionar lazy imports** (após linha 43):
  ```typescript
  const PersonalPlanningDashboard = lazy(() => import('./pages/PersonalPlanningDashboard'));
  const RoutineTasks = lazy(() => import('./pages/RoutineTasks'));
  const DailyChecklist = lazy(() => import('./pages/DailyChecklist'));
  const Goals = lazy(() => import('./pages/Goals'));
  ```

- [ ] **Adicionar rotas protegidas** (dentro do elemento Layout):
  ```typescript
  <Route path="/personal-planning/dashboard" element={<Suspense fallback={<LoadingFallback />}><PersonalPlanningDashboard /></Suspense>} />
  <Route path="/personal-planning/tasks" element={<Suspense fallback={<LoadingFallback />}><RoutineTasks /></Suspense>} />
  <Route path="/personal-planning/daily" element={<Suspense fallback={<LoadingFallback />}><DailyChecklist /></Suspense>} />
  <Route path="/personal-planning/goals" element={<Suspense fallback={<LoadingFallback />}><Goals /></Suspense>} />
  ```

**Linha aproximada**: Após linha 99 (no bloco de rotas protegidas)

---

#### 4.2. Sidebar/Navigation (Opcional)
**Arquivo**: `frontend/src/components/layout/Sidebar.tsx` (se existir)

**Requisitos**:
- [ ] Adicionar seção "Planejamento Pessoal" no menu
- [ ] Links para:
  - Dashboard (/personal-planning/dashboard)
  - Tarefas (/personal-planning/tasks)
  - Checklist Diário (/personal-planning/daily)
  - Objetivos (/personal-planning/goals)
- [ ] Ícones sugeridos: Target, CheckSquare, Calendar, Trophy

---

### 5. Testes e Validações

#### 5.1. Testes Backend
- [ ] Criar tarefas via Django Admin
- [ ] Testar endpoint `tasks-today` com diferentes datas
- [ ] Verificar validações (ex: task semanal sem weekday deve dar erro)
- [ ] Testar cálculo de métricas no dashboard
- [ ] Verificar se signals atualizam Goals corretamente

#### 5.2. Testes Frontend
- [ ] Criar tarefa rotineira (diária, semanal, mensal)
- [ ] Preencher checklist diário e salvar
- [ ] Criar objetivo vinculado a tarefa
- [ ] Verificar se dashboard mostra métricas corretas
- [ ] Testar validações dos formulários
- [ ] Verificar responsividade mobile

---

### 6. Melhorias Futuras (Opcional)

#### 6.1. Funcionalidades Extras
- [ ] Filtros avançados nas páginas (por categoria, status, data)
- [ ] Gráficos adicionais no dashboard (heatmap de cumprimento, etc.)
- [ ] Exportar dados (CSV, PDF)
- [ ] Notificações/lembretes de tarefas
- [ ] Gamificação (badges, conquistas)

#### 6.2. UX/UI
- [ ] Animações nas transições
- [ ] Skeleton loaders
- [ ] Empty states personalizados
- [ ] Modo drag-and-drop para reordenar tarefas
- [ ] Dark mode otimizado

#### 6.3. Performance
- [ ] Cache de dados do dashboard
- [ ] Infinite scroll nas listagens
- [ ] Debounce em filtros
- [ ] Lazy load de componentes pesados

---

## 📊 Progresso Estimado

- **Backend**: 100% ✅
- **Frontend Base**: 60% ✅ (types, validations, services)
- **Frontend UI**: 0% ⏳ (components, pages, routes)

---

## 🎯 Prioridades

### Alta Prioridade (MVP)
1. Executar migrations
2. DailyChecklist.tsx (principal funcionalidade)
3. RoutineTasks.tsx (gerenciar tarefas)
4. Integrar rotas no App.tsx

### Média Prioridade
5. PersonalPlanningDashboard.tsx (métricas)
6. Goals.tsx (objetivos)

### Baixa Prioridade
7. Melhorias de UX/UI
8. Funcionalidades extras

---

## 📝 Notas de Implementação

### Padrões a Seguir
- **Formulários**: React Hook Form + Zod
- **Listagens**: DataTable genérico (reutilizável)
- **Feedback**: useToast para sucesso/erro
- **Confirmações**: useAlertDialog para deletar
- **Loading**: useState(isLoading) + LoadingState component
- **Cores de Badge**:
  - Verde: ativo, concluído
  - Amarelo: pendente
  - Vermelho: inativo, falhou
  - Cinza: cancelado

### Componentes Radix Necessários
Todos já disponíveis no projeto:
- Button, Input, Label, Textarea
- Select, Checkbox, DatePicker
- Dialog, Badge, Progress
- Card, ScrollArea

### Ícones Lucide React
Já instalado, importar conforme necessário:
```typescript
import {
  Target, CheckCircle2, Trophy, TrendingUp, Flame,
  CheckSquare, Calendar, Plus, Edit, Trash2
} from 'lucide-react';
```

---

## 🚀 Começar Por

**Ordem sugerida de implementação**:

1. ✅ Executar migrations
2. ✅ Testar backend via Admin
3. 📝 RoutineTaskForm.tsx
4. 📝 RoutineTasks.tsx
5. 📝 DailyChecklistItem.tsx
6. 📝 DailyChecklist.tsx
7. 📝 Adicionar rotas no App.tsx
8. 📝 GoalForm.tsx
9. 📝 Goals.tsx
10. 📝 PersonalPlanningDashboard.tsx

---

## 📚 Referências Úteis

**Páginas de exemplo no projeto**:
- Dashboard: `/pages/LibraryDashboard.tsx`, `/pages/SecurityDashboard.tsx`
- CRUD: `/pages/Books.tsx`, `/pages/Expenses.tsx`
- Formulários: `/components/library/BookForm.tsx`, `/components/accounts/AccountForm.tsx`

**Documentação**:
- React Hook Form: https://react-hook-form.com/
- Zod: https://zod.dev/
- Recharts: https://recharts.org/
- Radix UI: https://www.radix-ui.com/
- Lucide Icons: https://lucide.dev/

---

**Data de criação**: 2026-01-01
**Última atualização**: 2026-01-01
