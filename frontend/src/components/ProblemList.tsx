import { useState, useEffect, useCallback } from 'react';
import { getProblems } from '../api';
import type { Problem } from '../types';
import { ProblemCard } from './ProblemCard';

interface ProblemListProps {
  selectedTags: string[];
}

export function ProblemList({ selectedTags }: ProblemListProps) {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [filteredProblems, setFilteredProblems] = useState<Problem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gradeFilter, setGradeFilter] = useState<number | undefined>();
  const [yearFilter, setYearFilter] = useState<number | undefined>();

  // Fetch all problems on mount
  useEffect(() => {
    const fetchProblems = async () => {
      try {
        const data = await getProblems();
        setProblems(data);
        setFilteredProblems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load problems');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProblems();
  }, []);

  // Filter problems when tags or filters change
  const filterProblems = useCallback(() => {
    let result = problems;

    // Filter by tags (union - must have ANY selected tag)
    if (selectedTags.length > 0) {
      result = result.filter((p) =>
        selectedTags.some((tag) => p.tags.includes(tag))
      );
    }

    // Filter by grade
    if (gradeFilter !== undefined) {
      result = result.filter((p) => p.grade === gradeFilter);
    }

    // Filter by year
    if (yearFilter !== undefined) {
      result = result.filter((p) => p.year === yearFilter);
    }

    setFilteredProblems(result);
  }, [problems, selectedTags, gradeFilter, yearFilter]);

  useEffect(() => {
    filterProblems();
  }, [filterProblems]);

  // Get unique years from problems
  const years = [...new Set(problems.map((p) => p.year))].sort((a, b) => b - a);

  if (isLoading) {
    return (
      <section className="problem-list-section">
        <div className="loading">Loading problems...</div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="problem-list-section">
        <div className="error">{error}</div>
      </section>
    );
  }

  return (
    <section className="problem-list-section">
      <h2>Practice Problems</h2>

      <div className="problem-filters">
        <select
          value={gradeFilter ?? ''}
          onChange={(e) =>
            setGradeFilter(e.target.value ? parseInt(e.target.value) : undefined)
          }
        >
          <option value="">All Grades</option>
          <option value="7">Grade 7</option>
          <option value="8">Grade 8</option>
        </select>

        <select
          value={yearFilter ?? ''}
          onChange={(e) =>
            setYearFilter(e.target.value ? parseInt(e.target.value) : undefined)
          }
        >
          <option value="">All Years</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      <p className="problem-count">
        Showing {filteredProblems.length} of {problems.length} problems
        {selectedTags.length > 0 && ` matching tags: ${selectedTags.join(', ')}`}
      </p>

      {filteredProblems.length === 0 ? (
        <div className="empty-state">
          <p>No problems match your current filters.</p>
          <p>Try selecting different tags or removing filters.</p>
        </div>
      ) : (
        <div className="problem-list">
          {filteredProblems.map((problem) => (
            <ProblemCard key={problem.id} problem={problem} />
          ))}
        </div>
      )}
    </section>
  );
}
