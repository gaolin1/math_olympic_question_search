import { useEffect, useRef } from 'react';
import katex from 'katex';

interface LatexRendererProps {
  latex: string;
  className?: string;
}

export function LatexRenderer({ latex, className }: LatexRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !latex) return;

    // Process the text to render LaTeX delimited by \( \) or $ $
    const processedText = latex
      // Replace \( and \) with temporary markers
      .replace(/\\\(/g, '%%LATEX_START%%')
      .replace(/\\\)/g, '%%LATEX_END%%');

    const parts = processedText.split(/(%%LATEX_START%%.*?%%LATEX_END%%)/g);

    containerRef.current.innerHTML = '';

    parts.forEach((part) => {
      if (part.startsWith('%%LATEX_START%%') && part.endsWith('%%LATEX_END%%')) {
        // Extract LaTeX content
        const latexContent = part
          .replace('%%LATEX_START%%', '')
          .replace('%%LATEX_END%%', '');

        const span = document.createElement('span');
        try {
          katex.render(latexContent, span, {
            throwOnError: false,
            displayMode: false,
          });
        } catch {
          span.textContent = latexContent;
        }
        containerRef.current?.appendChild(span);
      } else if (part) {
        // Regular text
        const textNode = document.createTextNode(part);
        containerRef.current?.appendChild(textNode);
      }
    });
  }, [latex]);

  if (!latex) {
    return null;
  }

  return <div ref={containerRef} className={className} />;
}
