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
    h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>,
    h2: ({ children }) => <h2 className="text-xl font-bold mt-3 mb-2">{children}</h2>,
    h3: ({ children }) => <h3 className="text-lg font-semibold mt-2 mb-1">{children}</h3>,
    h4: ({ children }) => <h4 className="text-base font-semibold mt-2 mb-1">{children}</h4>,

    // Paragraphs
    p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,

    // Lists
    ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
    li: ({ children }) => <li className="ml-2">{children}</li>,

    // Code
    code: ({ inline, className, children, ...props }: any) => {
      if (inline) {
        return (
          <code
            className="px-1.5 py-0.5 rounded bg-background/80 font-mono text-sm border"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <code
          className="block p-3 rounded bg-background/80 font-mono text-sm border overflow-x-auto my-2"
          {...props}
        >
          {children}
        </code>
      );
    },

    // Blockquote
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-primary pl-4 my-2 italic text-muted-foreground">
        {children}
      </blockquote>
    ),

    // Tables
    table: ({ children }) => (
      <div className="overflow-x-auto my-3">
        <table className="min-w-full border-collapse border border-border">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
    th: ({ children }) => (
      <th className="px-3 py-2 text-left font-semibold border border-border">{children}</th>
    ),
    td: ({ children }) => <td className="px-3 py-2 border border-border">{children}</td>,

    // Links
    a: ({ href, children }) => (
      <a href={href} className="text-primary underline hover:text-primary/80" target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ),

    // Horizontal rule
    hr: () => <hr className="my-4 border-border" />,

    // Strong/Bold
    strong: ({ children }) => <strong className="font-bold">{children}</strong>,

    // Emphasis/Italic
    em: ({ children }) => <em className="italic">{children}</em>,
  };

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
