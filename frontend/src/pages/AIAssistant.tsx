/**
 * AI Assistant Page
 *
 * Conversational AI chatbot with streaming responses and rich visualizations.
 * Features:
 * - Real-time streaming responses (word-by-word)
 * - Conversation context (maintains history)
 * - Rich visualizations (charts, cards, tables)
 * - Session persistence
 */

import { useState, useRef, useEffect } from 'react';
import { BotMessageSquare, Send, Loader2, Bot, User, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { PageHeader } from '@/components/common/PageHeader';
import { VisualizationRenderer } from '@/components/ai/VisualizationRenderer';
import { useAIChatStore } from '@/stores/ai-chat-store';
import { aiStreamingService } from '@/services/ai-streaming-service';
import { formatDate } from '@/lib/formatters';
import { getModuleBadgeColor, getModuleLabel, getEntityLabel } from '@/lib/helpers';

export default function AIAssistant() {
  const [input, setInput] = useState('');
  const { toast } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);

  const {
    sessionId,
    messages,
    isStreaming,
    setSessionId,
    addMessage,
    updateMessage,
    appendToMessage,
    setStreaming,
    clearMessages,
  } = useAIChatStore();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput('');
    setStreaming(true);

    // Create placeholder for assistant message
    const assistantId = (Date.now() + 1).toString();
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      streaming: true,
    });

    try {
      await aiStreamingService.streamQuery(
        userMessage.content,
        sessionId,
        (event) => {
          switch (event.event) {
            case 'intent':
              // Could show intent classification to user (optional)
              console.log('Intent detected:', event.data);
              break;

            case 'message_start':
              if (event.data.session_id) {
                setSessionId(event.data.session_id);
              }
              break;

            case 'content_chunk':
              appendToMessage(assistantId, event.data.text);
              break;

            case 'visualization':
              updateMessage(assistantId, {
                visualization: event.data,
              });
              break;

            case 'sources':
              updateMessage(assistantId, {
                sources: event.data.sources,
              });
              break;

            case 'message_end':
              updateMessage(assistantId, { streaming: false });
              if (event.data.session_id) {
                setSessionId(event.data.session_id);
              }
              break;

            case 'error':
              toast({
                title: 'Erro',
                description: event.data.message,
                variant: 'destructive',
              });
              updateMessage(assistantId, {
                content: `Erro: ${event.data.message}`,
                streaming: false,
              });
              break;
          }
        }
      );
    } catch (error: any) {
      console.error('Streaming error:', error);

      let errorTitle = 'Erro ao processar';
      let errorDescription = error.message || 'Não foi possível processar sua pergunta.';

      // Check for configuration errors
      if (error.message?.includes('503') || error.message?.includes('configurada')) {
        errorTitle = 'Configuração Necessária';
        errorDescription =
          'O AI Assistant requer chaves de API (OPENAI_API_KEY e GROQ_API_KEY) configuradas no servidor.';
      }

      toast({
        title: errorTitle,
        description: errorDescription,
        variant: 'destructive',
        duration: 7000,
      });

      updateMessage(assistantId, {
        content: `Desculpe, ocorreu um erro: ${errorDescription}`,
        streaming: false,
      });
    } finally {
      setStreaming(false);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Limpar todo o histórico da conversa?')) {
      clearMessages();
      toast({
        title: 'Histórico limpo',
        description: 'O histórico da conversa foi apagado.',
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <PageHeader
        title="AI Assistant"
        description="Converse naturalmente sobre seus dados pessoais"
        icon={<BotMessageSquare />}
      >
        {messages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearHistory}
            disabled={isStreaming}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Limpar Histórico
          </Button>
        )}
      </PageHeader>

      <Card className="flex-1 flex flex-col mt-6">
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Bot className="w-16 h-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Como posso ajudar?</h3>
              <p className="text-sm text-muted-foreground max-w-md mb-4">
                Faça perguntas sobre suas finanças, senhas, livros ou hábitos.
                Posso mostrar gráficos, tabelas e estatísticas!
              </p>
              <div className="mt-6 grid gap-2 w-full max-w-md">
                <p className="text-xs text-muted-foreground text-left">Exemplos de perguntas:</p>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Quanto gastei este mês?')}
                >
                  "Quanto gastei este mês?"
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Mostre a evolução das minhas despesas')}
                >
                  "Mostre a evolução das minhas despesas"
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Quais livros estou lendo?')}
                >
                  "Quais livros estou lendo?"
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-primary-foreground" />
                    </div>
                  )}

                  <div className={`flex-1 max-w-3xl ${message.role === 'user' ? 'flex justify-end' : ''}`}>
                    <div
                      className={`rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">
                        {message.content}
                        {message.streaming && (
                          <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
                        )}
                      </p>

                      {/* Visualization */}
                      {message.visualization && (
                        <VisualizationRenderer visualization={message.visualization} />
                      )}

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-border">
                          <p className="text-xs font-semibold mb-2">Fontes consultadas:</p>
                          <div className="space-y-2">
                            {message.sources.map((source, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 text-xs bg-background/50 p-2 rounded"
                              >
                                <Badge className={getModuleBadgeColor(source.module)}>
                                  {getModuleLabel(source.module)}
                                </Badge>
                                <div className="flex-1">
                                  <p className="font-medium">{getEntityLabel(source.type)}</p>
                                  {source.metadata.title && (
                                    <p className="text-muted-foreground">{source.metadata.title}</p>
                                  )}
                                  {source.metadata.name && !source.metadata.title && (
                                    <p className="text-muted-foreground">{source.metadata.name}</p>
                                  )}
                                  {source.metadata.description && (
                                    <p className="text-muted-foreground line-clamp-1">
                                      {source.metadata.description}
                                    </p>
                                  )}
                                </div>
                                <span className="text-muted-foreground">
                                  {Math.round(source.score * 100)}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDate(message.timestamp, 'HH:mm')}
                      </p>
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-secondary-foreground" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={scrollRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua pergunta..."
              disabled={isStreaming}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={isStreaming || !input.trim()}>
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Enter para enviar • Shift+Enter para nova linha
          </p>
        </div>
      </Card>
    </div>
  );
}
