/**
 * Página do Assistente de IA.
 *
 * Interface de chat para interação com o assistente de IA local.
 */
import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Bot, Trash2, History, AlertCircle, Sparkles } from 'lucide-react';
import { PageContainer } from '@/components/common/PageContainer';
import { PageHeader } from '@/components/common/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage } from '@/components/ai-assistant/ChatMessage';
import { ChatInput } from '@/components/ai-assistant/ChatInput';
import { aiAssistantService } from '@/services/ai-assistant-service';
import { useToast } from '@/hooks/use-toast';
import type { AiMessage } from '@/types';

// Sugestões de perguntas para o usuário
const SUGESTOES = [
  'Qual foi meu faturamento do último mês?',
  'Quanto gastei em alimentação este mês?',
  'Qual o saldo total das minhas contas?',
  'Quais livros estou lendo?',
  'Quais são minhas tarefas de hoje?',
  'Qual a senha do Netflix?',
  'Quanto tenho guardado nos cofres?',
  'Quais despesas por categoria este mês?',
];

export default function AiAssistant() {
  const [messages, setMessages] = useState<AiMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isServiceHealthy, setIsServiceHealthy] = useState<boolean | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Verifica saúde do serviço ao montar
  useEffect(() => {
    checkServiceHealth();
  }, []);

  // Scroll automático para a última mensagem
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const checkServiceHealth = async () => {
    try {
      const health = await aiAssistantService.checkHealth();
      setIsServiceHealthy(health.ollama === 'healthy' && health.database === 'healthy');
    } catch {
      setIsServiceHealthy(false);
    }
  };

  const handleSend = async (pergunta: string) => {
    // Adiciona mensagem do usuário
    const userMessage: AiMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: pergunta,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await aiAssistantService.pergunta(pergunta);

      // Adiciona resposta do assistente
      const assistantMessage: AiMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.resposta,
        displayType: response.display_type,
        data: response.data,
        module: response.module,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao processar sua pergunta';
      toast({
        title: 'Erro',
        description: errorMessage,
        variant: 'destructive',
      });

      // Adiciona mensagem de erro como resposta
      const errorResponse: AiMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSugestao = (sugestao: string) => {
    handleSend(sugestao);
  };

  const handleLimparHistorico = () => {
    setMessages([]);
  };

  return (
    <PageContainer>
      <PageHeader
        title="Assistente de IA"
        icon={<Bot className="w-6 h-6" />}
      />

      {/* Status do serviço */}
      {isServiceHealthy === false && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-4 rounded-lg bg-warning/10 border border-warning/20 flex items-center gap-3"
        >
          <AlertCircle className="w-5 h-5 text-warning" />
          <div>
            <div className="font-medium text-warning">Serviço de IA indisponível</div>
            <div className="text-sm text-muted-foreground">
              O Ollama pode não estar rodando. As respostas serão simplificadas.
            </div>
          </div>
        </motion.div>
      )}

      <Card className="flex flex-col h-[calc(100vh-220px)] min-h-[500px]">
        {/* Área de mensagens */}
        <CardContent className="flex-1 p-0 overflow-hidden">
          <ScrollArea
            ref={scrollRef}
            className="h-full p-4"
          >
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-8">
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="mb-6"
                >
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4 mx-auto">
                    <Sparkles className="w-10 h-10 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">
                    Olá! Como posso ajudar?
                  </h3>
                  <p className="text-muted-foreground max-w-md">
                    Faça perguntas sobre suas finanças, livros, tarefas ou senhas.
                    Eu vou consultar seus dados e responder de forma natural.
                  </p>
                </motion.div>

                {/* Sugestões */}
                <div className="w-full max-w-2xl">
                  <div className="text-sm font-medium text-muted-foreground mb-3">
                    Experimente perguntar:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {SUGESTOES.map((sugestao, i) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        onClick={() => handleSugestao(sugestao)}
                        className="text-left p-3 rounded-lg border bg-card hover:bg-accent hover:text-accent-foreground transition-colors text-sm"
                      >
                        {sugestao}
                      </motion.button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}

                {/* Indicador de carregamento */}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex gap-3 p-4 rounded-lg bg-primary/5 border border-primary/10 mr-8"
                  >
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-sm text-muted-foreground">Pensando...</span>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </ScrollArea>
        </CardContent>

        {/* Ações e Input */}
        <div className="border-t">
          {/* Botões de ação quando há mensagens */}
          {messages.length > 0 && (
            <div className="flex justify-end gap-2 px-4 pt-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLimparHistorico}
                className="text-muted-foreground"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Limpar conversa
              </Button>
            </div>
          )}

          {/* Input */}
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
          />
        </div>
      </Card>
    </PageContainer>
  );
}
