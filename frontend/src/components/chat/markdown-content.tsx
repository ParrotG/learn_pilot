"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
  compact?: boolean;
};

export function MarkdownContent({ content, compact = false }: MarkdownContentProps) {
  return (
    <div className={compact ? "text-sm leading-6" : "text-sm leading-7"}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="mb-3 list-disc pl-5 last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="mb-3 list-decimal pl-5 last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="mb-1">{children}</li>,
          code: ({ children }) => (
            <code className="rounded bg-black/5 px-1.5 py-0.5 font-mono text-[0.92em]">{children}</code>
          ),
          pre: ({ children }) => (
            <pre className="mb-3 overflow-x-auto rounded-2xl bg-[var(--surface-muted)] p-4 text-sm">
              {children}
            </pre>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="text-[var(--primary)] underline underline-offset-2"
            >
              {children}
            </a>
          ),
          h1: ({ children }) => <h1 className="mb-3 text-xl font-semibold">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-3 text-lg font-semibold">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-2 text-base font-semibold">{children}</h3>,
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-4 border-[var(--accent)] pl-4 italic text-[var(--muted-foreground)]">
              {children}
            </blockquote>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
