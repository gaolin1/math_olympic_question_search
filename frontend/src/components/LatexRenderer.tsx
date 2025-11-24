import { useEffect, useRef } from 'react';
import katex from 'katex';

console.log('=== LatexRenderer.tsx LOADED ===');


interface LatexRendererProps {
  latex: string;
  className?: string;
}

// Helper function to append text with line breaks preserved
function appendTextWithLineBreaks(container: HTMLElement, text: string) {
  text.split(/\r?\n/).forEach((line, idx, arr) => {
    container.appendChild(document.createTextNode(line));
    if (idx < arr.length - 1) {
      container.appendChild(document.createElement('br'));
    }
  });
}

export function LatexRenderer({ latex, className }: LatexRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Early return for empty/null content - must be before useEffect to prevent
  // the effect from running on unmounted component
  const hasContent = latex && latex.trim();

  useEffect(() => {
    // Guard against null ref or empty content
    if (!containerRef.current || !hasContent) {
      return;
    }

    const container = containerRef.current;
    const normalized = latex.replace(/\\\$/g, '$');

    console.log('useEffect running, latex:', JSON.stringify(latex));
    console.log('normalized:', JSON.stringify(normalized));

    // If the entire string is a single math block \( ... \), render it.
    // Match \( content \) with flexible whitespace
    const mathOnlyMatch = normalized.match(/^\s*\\\(\s*([\s\S]*?)\s*\\\)\s*$/);
    console.log('mathOnlyMatch:', mathOnlyMatch);
    if (mathOnlyMatch && mathOnlyMatch[1]) {
      console.log('MATCHED! Rendering KaTeX...');
      const mathContent = mathOnlyMatch[1].trim();
      if (mathContent) {
        container.innerHTML = '';
        const span = document.createElement('span');
        try {
          katex.render(mathContent, span, { throwOnError: false, displayMode: false });
          container.appendChild(span);
          console.log('KaTeX rendered successfully, container HTML:', container.innerHTML.substring(0, 100));
        } catch (e) {
          console.error('KaTeX render error:', e);
          span.textContent = mathContent;
          container.appendChild(span);
        }
        return;
      }
    }

    console.log('Did NOT match math-only pattern, falling through to mixed content...');

    // Handle mixed content with inline math \( ... \) blocks
    container.innerHTML = '';
    const mathPattern = /\\\(\s*([\s\S]*?)\s*\\\)/g;
    let lastIndex = 0;
    let match;

    while ((match = mathPattern.exec(normalized)) !== null) {
      // Add text before the math
      if (match.index > lastIndex) {
        const textBefore = normalized.slice(lastIndex, match.index);
        appendTextWithLineBreaks(container, textBefore);
      }

      // Render the math
      const mathContent = match[1].trim();
      if (mathContent) {
        const span = document.createElement('span');
        try {
          katex.render(mathContent, span, { throwOnError: false, displayMode: false });
        } catch {
          span.textContent = mathContent;
        }
        container.appendChild(span);
      }

      lastIndex = mathPattern.lastIndex;
    }

    // Add remaining text after last math block
    if (lastIndex < normalized.length) {
      appendTextWithLineBreaks(container, normalized.slice(lastIndex));
    }
  }, [latex, hasContent]);

  // Don't render empty container - prevents layout issues with empty divs
  if (!hasContent) {
    return null;
  }

  return <div ref={containerRef} className={className} />;
}
