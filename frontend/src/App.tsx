import { useEffect, useState } from 'react';
import { LatexInput, TagSelector, ProblemList } from './components';
import { analyzeLaTeX, getTags } from './api';
import type { TagWithConfidence } from './types';

function App() {
  const [suggestedTags, setSuggestedTags] = useState<TagWithConfidence[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [tagCounts, setTagCounts] = useState<Record<string, number>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTags()
      .then((resp) => {
        setAvailableTags(resp.all_tags);
        setTagCounts(resp.tag_counts || {});
      })
      .catch(() => setAvailableTags([]));
  }, []);

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
        <p>Enter a math expression to find related practice problems from Gauss competitions.</p>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="layout-grid">
        <div className="left-panel">
          <LatexInput onAnalyze={handleAnalyze} isLoading={isAnalyzing} />

          <TagSelector
            suggestedTags={suggestedTags}
            selectedTags={selectedTags}
            availableTags={availableTags}
            tagCounts={tagCounts}
            onTagToggle={handleTagToggle}
            onTagRemove={handleTagRemove}
          />
        </div>

        <div className="right-panel">
          <ProblemList selectedTags={selectedTags} />
        </div>
      </div>
    </div>
  );
}

export default App;
