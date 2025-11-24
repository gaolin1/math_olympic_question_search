import { useState, useEffect, useRef } from 'react';
import { LatexRenderer } from './LatexRenderer';

interface LatexInputProps {
  onAnalyze: (latex: string) => void;
  isLoading: boolean;
}

export function LatexInput({ onAnalyze, isLoading }: LatexInputProps) {
  const [latex, setLatex] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      const el = textareaRef.current;
      el.style.height = 'auto';
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [latex]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (latex.trim()) {
      onAnalyze(latex);
    }
  };

  const handleInsertMath = () => {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart ?? latex.length;
    const end = el.selectionEnd ?? start;
    const insert = '\\(  \\)';
    const nextVal = latex.slice(0, start) + insert + latex.slice(end);
    setLatex(nextVal);
    requestAnimationFrame(() => {
      const pos = start + 3;
      el.focus();
      el.setSelectionRange(pos, pos);
    });
  };

  return (
    <section className="latex-input-section">
      <h2>Enter a Math Expression</h2>
      <form onSubmit={handleSubmit}>
        <div className="latex-input-container">
          <textarea
            value={latex}
            onChange={(e) => setLatex(e.target.value)}
            placeholder="e.g., x^2 + 5x + 6 = 0"
            disabled={isLoading}
            rows={3}
            ref={textareaRef}
          />
          <div className="math-actions">
            <button type="button" className="secondary-btn" onClick={handleInsertMath}>
              Add Math
            </button>
            <button type="submit" disabled={isLoading || !latex.trim()}>
              {isLoading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>
      </form>
      <div className="latex-preview">
        {latex ? (
          <LatexRenderer latex={latex} className="problem-statement" />
        ) : (
          <span className="placeholder">Preview will appear here...</span>
        )}
      </div>
    </section>
  );
}
