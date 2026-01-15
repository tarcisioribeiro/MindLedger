/**
 * Markdown Renderer Component
 *
 * Renders markdown content with proper styling for chat messages.
 * Supports GFM (GitHub Flavored Markdown) including tables, task lists, etc.
 */

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { type Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  // Custom components for markdown elements
  const components: Components = {
    // Headings
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold mt-6 mb-3 first:mt-0 text-foreground">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-bold mt-5 mb-2 first:mt-0 text-foreground">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold mt-4 mb-2 first:mt-0 text-foreground">{children}</h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold mt-3 mb-1 first:mt-0 text-foreground">{children}</h4>
    ),

    // Paragraphs
    p: ({ children }) => (
      <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
    ),

    // Lists - melhorada a indentação e espaçamento
    ul: ({ children }) => (
      <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>
    ),
    li: ({ children }) => (
      <li className="leading-relaxed pl-1">{children}</li>
    ),

    // Pre block for code blocks
    pre: ({ children }) => (
      <pre className="block p-4 rounded-lg bg-muted/50 font-mono text-sm border overflow-x-auto custom-scrollbar my-3">
        {children}
      </pre>
    ),

    // Code - detecta inline vs block pelo contexto do node
    code: ({ node, className, children, ...props }: any) => {
      // Verifica se está dentro de um <pre> (code block) ou é inline
      const isInline = !node?.properties?.className &&
                       node?.position?.start?.line === node?.position?.end?.line;

      if (isInline) {
        return (
          <code
            className="px-1.5 py-0.5 rounded bg-muted/70 font-mono text-sm border text-primary"
            {...props}
          >
            {children}
          </code>
        );
      }

      // Para code blocks, retorna apenas o código (o pre já aplica o estilo)
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },

    // Blockquote
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-primary/60 pl-4 my-4 py-1 italic bg-muted/30 rounded-r">
        {children}
      </blockquote>
    ),

    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto custom-scrollbar my-4 rounded-lg border border-border">
        <table className="min-w-full border-collapse">{children}</table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="bg-muted/50">{children}</thead>
    ),
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => (
      <tr className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors">
        {children}
      </tr>
    ),
    th: ({ children }) => (
      <th className="px-4 py-3 text-left font-semibold text-sm">{children}</th>
    ),
    td: ({ children }) => (
      <td className="px-4 py-3 text-sm">{children}</td>
    ),

    // Links
    a: ({ href, children }) => (
      <a
        href={href}
        className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors"
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),

    // Horizontal rule
    hr: () => <hr className="my-6 border-border" />,

    // Strong/Bold
    strong: ({ children }) => (
      <strong className="font-semibold text-foreground">{children}</strong>
    ),

    // Emphasis/Italic
    em: ({ children }) => <em className="italic">{children}</em>,

    // Line breaks
    br: () => <br className="my-1" />,
  };

  // Pré-processa o conteúdo para garantir formatação correta
  const processedContent = content
    // Garante quebra de linha após títulos
    .replace(/^(#{1,6}\s.+)$/gm, '$1\n')
    // Garante espaçamento antes de listas
    .replace(/([^\n])\n([-*]\s)/g, '$1\n\n$2')
    .replace(/([^\n])\n(\d+\.\s)/g, '$1\n\n$2');

  return (
    <div className={`markdown-content max-w-none ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}
