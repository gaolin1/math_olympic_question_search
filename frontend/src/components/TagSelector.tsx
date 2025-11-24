import { useMemo, useState } from 'react';
import type { TagWithConfidence } from '../types';

interface TagSelectorProps {
  suggestedTags: TagWithConfidence[];
  selectedTags: string[];
  availableTags: string[];
  tagCounts: Record<string, number>;
  onTagToggle: (tag: string) => void;
  onTagRemove: (tag: string) => void;
}

export function TagSelector({
  suggestedTags,
  selectedTags,
  availableTags,
  tagCounts,
  onTagToggle,
  onTagRemove,
}: TagSelectorProps) {
  const [search, setSearch] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const filteredAvailable = useMemo(() => {
    const term = search.trim().toLowerCase();
    const source = term
      ? availableTags.filter((t) => t.toLowerCase().includes(term))
      : availableTags;
    return source
      .filter((t) => !selectedTags.includes(t) && (tagCounts[t] || 0) > 0);
  }, [availableTags, selectedTags, search, tagCounts]);

  return (
    <section className="tag-selector-section">
      <h2>Concept Tags</h2>

      {suggestedTags.length > 0 && (
        <details className="suggested-tags" open>
          <summary>Suggested Tags (click to select)</summary>
          <div className="tag-suggestions">
            {suggestedTags.map((tag) => (
              <label key={tag.name} className="tag-suggestion">
                <input
                  type="checkbox"
                  checked={selectedTags.includes(tag.name)}
                  onChange={() => onTagToggle(tag.name)}
                />
                <span className="tag-name">{tag.name}</span>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{ width: `${tag.confidence * 100}%` }}
                  />
                </div>
                <span className="confidence-value">
                  {Math.round(tag.confidence * 100)}%
                </span>
              </label>
            ))}
          </div>
        </details>
      )}

      {availableTags.length > 0 && (
        <div className="available-tags">
          <h3>Browse Tags</h3>
          <div className="tag-search">
            <input
              type="text"
              placeholder="Type to find tags..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
            {(isFocused || search.length > 0) && filteredAvailable.length > 0 && (
              <div className="tag-dropdown">
                {filteredAvailable.map((tag) => (
                  <button
                    type="button"
                    key={tag}
                    className="tag-pill"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      onTagToggle(tag);
                      setSearch('');
                      setIsFocused(false);
                    }}
                  >
                    {tag} <span className="tag-count">({tagCounts[tag] || 0})</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div>
        <h3 style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.75rem' }}>
          Selected Tags
        </h3>
        {selectedTags.length > 0 ? (
          <div className="selected-tags">
            {selectedTags.map((tag) => (
              <span key={tag} className="selected-tag">
                {tag}
                <button onClick={() => onTagRemove(tag)}>&times;</button>
              </span>
            ))}
          </div>
        ) : (
          <p className="no-tags">No tags selected. Analyze an expression or select from suggestions.</p>
        )}
      </div>
    </section>
  );
}
