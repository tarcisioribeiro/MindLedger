import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/auth-store';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { Toaster } from './components/ui/toaster';
import { AlertDialogProvider } from './components/providers/AlertDialogProvider';
import { Loader2 } from 'lucide-react';

// Eager load (páginas públicas carregadas imediatamente)
import Login from './pages/Login';
import Register from './pages/Register';
import Unauthorized from './pages/Unauthorized';

// Lazy load (páginas protegidas carregadas sob demanda)
const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Accounts = lazy(() => import('./pages/Accounts'));
const Expenses = lazy(() => import('./pages/Expenses'));
const FixedExpenses = lazy(() => import('./pages/FixedExpenses'));
const Revenues = lazy(() => import('./pages/Revenues'));
const CreditCards = lazy(() => import('./pages/CreditCards'));
const CreditCardBills = lazy(() => import('./pages/CreditCardBills'));
const CreditCardExpenses = lazy(() => import('./pages/CreditCardExpenses'));
const Transfers = lazy(() => import('./pages/Transfers'));
const Loans = lazy(() => import('./pages/Loans'));
const Members = lazy(() => import('./pages/Members'));

// Security Module
const SecurityDashboard = lazy(() => import('./pages/SecurityDashboard'));
const Passwords = lazy(() => import('./pages/Passwords'));
const StoredCards = lazy(() => import('./pages/StoredCards'));
const StoredAccounts = lazy(() => import('./pages/StoredAccounts'));
const Archives = lazy(() => import('./pages/Archives'));
const ActivityLogs = lazy(() => import('./pages/ActivityLogs'));

// Library Module
const LibraryDashboard = lazy(() => import('./pages/LibraryDashboard'));
const Books = lazy(() => import('./pages/Books'));
const Authors = lazy(() => import('./pages/Authors'));
const Publishers = lazy(() => import('./pages/Publishers'));
const Summaries = lazy(() => import('./pages/Summaries'));
const Readings = lazy(() => import('./pages/Readings'));

// AI Assistant
const AIAssistant = lazy(() => import('./pages/AIAssistant'));

// Personal Planning Module
const PersonalPlanningDashboard = lazy(() => import('./pages/PersonalPlanningDashboard'));
const RoutineTasks = lazy(() => import('./pages/RoutineTasks'));
const Goals = lazy(() => import('./pages/Goals'));
const DailyChecklist = lazy(() => import('./pages/DailyChecklist'));

// Loading component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen">
    <Loader2 className="w-12 h-12 animate-spin text-primary" />
  </div>
);

function App() {
  const { loadUserData, isAuthenticated, isInitializing } = useAuthStore();

  useEffect(() => {
    // Load user data from cookies on app start
    loadUserData();
  }, [loadUserData]);

  // Mostra loading durante inicialização
  if (isInitializing) {
    return <LoadingFallback />;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <Login />
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <Register />
          }
        />
        <Route path="/unauthorized" element={<Unauthorized />} />

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Suspense fallback={<LoadingFallback />}><Home /></Suspense>} />
          <Route path="/dashboard" element={<Suspense fallback={<LoadingFallback />}><Dashboard /></Suspense>} />
          <Route path="/accounts" element={<Suspense fallback={<LoadingFallback />}><Accounts /></Suspense>} />
          <Route path="/expenses" element={<Suspense fallback={<LoadingFallback />}><Expenses /></Suspense>} />
          <Route path="/fixed-expenses" element={<Suspense fallback={<LoadingFallback />}><FixedExpenses /></Suspense>} />
          <Route path="/revenues" element={<Suspense fallback={<LoadingFallback />}><Revenues /></Suspense>} />
          <Route path="/credit-cards" element={<Suspense fallback={<LoadingFallback />}><CreditCards /></Suspense>} />
          <Route path="/credit-card-bills" element={<Suspense fallback={<LoadingFallback />}><CreditCardBills /></Suspense>} />
          <Route path="/credit-card-expenses" element={<Suspense fallback={<LoadingFallback />}><CreditCardExpenses /></Suspense>} />
          <Route path="/transfers" element={<Suspense fallback={<LoadingFallback />}><Transfers /></Suspense>} />
          <Route path="/loans" element={<Suspense fallback={<LoadingFallback />}><Loans /></Suspense>} />
          <Route path="/members" element={<Suspense fallback={<LoadingFallback />}><Members /></Suspense>} />

          {/* Security Module routes */}
          <Route path="/security/dashboard" element={<Suspense fallback={<LoadingFallback />}><SecurityDashboard /></Suspense>} />
          <Route path="/security/passwords" element={<Suspense fallback={<LoadingFallback />}><Passwords /></Suspense>} />
          <Route path="/security/stored-cards" element={<Suspense fallback={<LoadingFallback />}><StoredCards /></Suspense>} />
          <Route path="/security/stored-accounts" element={<Suspense fallback={<LoadingFallback />}><StoredAccounts /></Suspense>} />
          <Route path="/security/archives" element={<Suspense fallback={<LoadingFallback />}><Archives /></Suspense>} />
          <Route path="/security/activity-logs" element={<Suspense fallback={<LoadingFallback />}><ActivityLogs /></Suspense>} />

          {/* Library Module routes */}
          <Route path="/library/dashboard" element={<Suspense fallback={<LoadingFallback />}><LibraryDashboard /></Suspense>} />
          <Route path="/library/books" element={<Suspense fallback={<LoadingFallback />}><Books /></Suspense>} />
          <Route path="/library/authors" element={<Suspense fallback={<LoadingFallback />}><Authors /></Suspense>} />
          <Route path="/library/publishers" element={<Suspense fallback={<LoadingFallback />}><Publishers /></Suspense>} />
          <Route path="/library/summaries" element={<Suspense fallback={<LoadingFallback />}><Summaries /></Suspense>} />
          <Route path="/library/readings" element={<Suspense fallback={<LoadingFallback />}><Readings /></Suspense>} />

          {/* AI Assistant route */}
          <Route path="/ai-assistant" element={<Suspense fallback={<LoadingFallback />}><AIAssistant /></Suspense>} />

          {/* Personal Planning Module routes */}
          <Route path="/planning/dashboard" element={<Suspense fallback={<LoadingFallback />}><PersonalPlanningDashboard /></Suspense>} />
          <Route path="/planning/routine-tasks" element={<Suspense fallback={<LoadingFallback />}><RoutineTasks /></Suspense>} />
          <Route path="/planning/goals" element={<Suspense fallback={<LoadingFallback />}><Goals /></Suspense>} />
          <Route path="/planning/daily" element={<Suspense fallback={<LoadingFallback />}><DailyChecklist /></Suspense>} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
      <AlertDialogProvider />
    </BrowserRouter>
  );
}

export default App;
