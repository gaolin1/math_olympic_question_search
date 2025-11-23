import { useState } from 'react';
import { LatexInput, TagSelector, ProblemList } from './components';
import { analyzeLaTeX } from './api';
import type { TagWithConfidence } from './types';

function App() {
  const [suggestedTags, setSuggestedTags] = useState<TagWithConfidence[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (latex: string) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await analyzeLaTeX(latex);
      setSuggestedTags(response.tags);
      // Don't auto-select tags - let user choose
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze expression');
      setSuggestedTags([]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleTagToggle = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleTagRemove = (tag: string) => {
    setSelectedTags((prev) => prev.filter((t) => t !== tag));
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Math Olympic Question Search</h1>
        <p>
          Enter a math expression to find related practice problems from Gauss competitions.
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      <LatexInput onAnalyze={handleAnalyze} isLoading={isAnalyzing} />

      <TagSelector
        suggestedTags={suggestedTags}
        selectedTags={selectedTags}
        onTagToggle={handleTagToggle}
        onTagRemove={handleTagRemove}
      />

      <ProblemList selectedTags={selectedTags} />
    </div>
  );
}

export default App;
