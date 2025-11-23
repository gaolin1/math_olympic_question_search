import { useState, useEffect, useRef } from 'react';
import katex from 'katex';

interface LatexInputProps {
  onAnalyze: (latex: string) => void;
  isLoading: boolean;
}

export function LatexInput({ onAnalyze, isLoading }: LatexInputProps) {
  const [latex, setLatex] = useState('');
  const previewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (previewRef.current && latex) {
      try {
        katex.render(latex, previewRef.current, {
          throwOnError: false,
          displayMode: true,
        });
      } catch {
        previewRef.current.textContent = latex;
      }
    }
  }, [latex]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (latex.trim()) {
      onAnalyze(latex);
    }
  };

  return (
    <section className="latex-input-section">
      <h2>Enter a Math Expression</h2>
      <form onSubmit={handleSubmit}>
        <div className="latex-input-container">
          <input
            type="text"
            value={latex}
            onChange={(e) => setLatex(e.target.value)}
            placeholder="e.g., x^2 + 5x + 6 = 0"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !latex.trim()}>
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </form>
      <div className="latex-preview">
        {latex ? (
          <div ref={previewRef} />
        ) : (
          <span className="placeholder">Preview will appear here...</span>
        )}
      </div>
    </section>
  );
}
