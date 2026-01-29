import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary para capturar erros em componentes React.
 * Previne que erros em um componente quebrem toda a aplicacao.
 *
 * Uso:
 * ```tsx
 * <ErrorBoundary>
 *   <ComponenteQuePodeFalhar />
 * </ErrorBoundary>
 * ```
 *
 * Com fallback customizado:
 * ```tsx
 * <ErrorBoundary fallback={<MeuComponenteDeErro />}>
 *   <ComponenteQuePodeFalhar />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log do erro para debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Callback opcional para logging externo (ex: Sentry)
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Fallback customizado se fornecido
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Fallback padrao
      return (
        <div className="flex items-center justify-center min-h-[400px] p-4">
          <Card className="max-w-md w-full">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 p-3 bg-destructive/10 rounded-full w-fit">
                <AlertTriangle className="h-8 w-8 text-destructive" />
              </div>
              <CardTitle className="text-xl">Algo deu errado</CardTitle>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-muted-foreground">
                Ocorreu um erro inesperado ao carregar este componente.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-left text-sm bg-muted p-3 rounded-lg">
                  <summary className="cursor-pointer font-medium mb-2">
                    Detalhes do erro (desenvolvimento)
                  </summary>
                  <pre className="overflow-auto text-xs text-destructive whitespace-pre-wrap">
                    {this.state.error.message}
                    {'\n\n'}
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
              <div className="flex gap-2 justify-center">
                <Button onClick={this.handleRetry} variant="default">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Tentar novamente
                </Button>
                <Button
                  onClick={() => window.location.reload()}
                  variant="outline"
                >
                  Recarregar pagina
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
