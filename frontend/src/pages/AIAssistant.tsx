import { useState } from 'react';
import { BotMessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { aiService } from '@/services/ai-service';
import { formatDate } from '@/lib/formatters';
import { getModuleBadgeColor, getModuleLabel, getEntityLabel } from '@/lib/helpers';
import { PageHeader } from '@/components/common/PageHeader';
import type { ChatMessage } from '@/types';
import { Loader2, Send, Bot, User } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

export default function AIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await aiService.query({ question: input });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      let errorTitle = 'Erro ao consultar AI';
      let errorDescription = error.message || 'Não foi possível processar sua pergunta.';
      let errorContent = 'Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente.';

      // Check if it's a configuration error
      if (error.response?.status === 503 || error.message?.includes('configurada')) {
        errorTitle = 'Configuração Necessária';
        errorDescription = error.response?.data?.message || error.message || 'As chaves de API não estão configuradas.';
        errorContent = `⚠️ Configuração Necessária\n\nO AI Assistant requer configuração das chaves de API:\n\n1. OPENAI_API_KEY (para embeddings)\n   Obtenha em: https://platform.openai.com/api-keys\n\n2. GROQ_API_KEY (para geração de texto)\n   Obtenha em: https://console.groq.com/keys\n\nAdicione essas chaves no arquivo .env do projeto.`;
      } else if (error.response?.data?.message) {
        errorDescription = error.response.data.message;
        errorContent = error.response.data.message;
      }

      toast({
        title: errorTitle,
        description: errorDescription,
        variant: 'destructive',
        duration: 7000,
      });

      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
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
        description="Faça perguntas sobre seus dados pessoais em linguagem natural"
        icon={<BotMessageSquare />}
      />

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col mt-6">
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Bot className="w-16 h-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Como posso ajudar?</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Pergunte sobre suas finanças, senhas, livros ou qualquer outro dado pessoal.
                Eu vou buscar informações relevantes e fornecer respostas contextualizadas.
              </p>
              <div className="mt-6 grid gap-2 w-full max-w-md">
                <p className="text-xs text-muted-foreground text-left">Exemplos de perguntas:</p>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Quais foram minhas maiores despesas este mês?')}
                >
                  "Quais foram minhas maiores despesas este mês?"
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Quais livros estou lendo atualmente?')}
                >
                  "Quais livros estou lendo atualmente?"
                </Button>
                <Button
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => setInput('Quantas senhas tenho cadastradas?')}
                >
                  "Quantas senhas tenho cadastradas?"
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
                      <p className="whitespace-pre-wrap">{message.content}</p>

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
                                  {source.metadata.name && (
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

              {loading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-primary-foreground" />
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <Loader2 className="w-5 h-5 animate-spin" />
                  </div>
                </div>
              )}
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
              disabled={loading}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Pressione Enter para enviar, Shift+Enter para nova linha
          </p>
        </div>
      </Card>
    </div>
  );
}
