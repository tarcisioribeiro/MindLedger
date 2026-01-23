/**
 * Componente de mensagem do chat.
 *
 * Exibe mensagens do usuário e do assistente com estilos diferentes.
 */
import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ResponseRenderer } from './ResponseRenderer';
import type { AiMessage } from '@/types';

interface ChatMessageProps {
  message: AiMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex gap-3 p-4 rounded-lg',
        isUser
          ? 'bg-muted ml-8'
          : 'bg-primary/5 border border-primary/10 mr-8'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-muted-foreground/20'
            : 'bg-primary/20'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-muted-foreground" />
        ) : (
          <Bot className="w-4 h-4 text-primary" />
        )}
      </div>

      {/* Conteúdo */}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm mb-1">
          {isUser ? 'Você' : 'Assistente'}
        </div>

        {isUser ? (
          <p className="text-foreground whitespace-pre-wrap">{message.content}</p>
        ) : (
          <ResponseRenderer
            content={message.content}
            displayType={message.displayType || 'text'}
            data={message.data}
          />
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div className="text-xs text-muted-foreground mt-2">
            {new Date(message.timestamp).toLocaleTimeString('pt-BR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
}
