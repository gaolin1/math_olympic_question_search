import { useState } from 'react';
import { getProblem } from '../api';
import type { Problem, ProblemDetail } from '../types';
import { LatexRenderer } from './LatexRenderer';
import { HintChat } from './HintChat';

interface ProblemCardProps {
  problem: Problem;
}

export function ProblemCard({ problem }: ProblemCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [detail, setDetail] = useState<ProblemDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const handleExpand = async () => {
    if (!isExpanded && !detail) {
      setIsLoadingDetail(true);
      try {
        const data = await getProblem(problem.id);
        setDetail(data);
      } catch (error) {
        console.error('Failed to load problem details:', error);
      } finally {
        setIsLoadingDetail(false);
      }
    }
    setIsExpanded(!isExpanded);
  };

  const handleRevealAnswer = () => {
    setShowAnswer(true);
  };

  return (
    <div className="problem-card">
      <div className="problem-header" onClick={handleExpand}>
        <div>
          <div className="problem-meta">
            <span className="problem-badge grade">Grade {problem.grade}</span>
            <span className="problem-badge year">{problem.year}</span>
            <span className="problem-badge">#{problem.problem_number}</span>
          </div>
          <div className="problem-statement" style={{ marginTop: '0.5rem' }}>
            <LatexRenderer latex={problem.statement} images={problem.images} />
          </div>
        </div>
        <span className="problem-expand-icon">{isExpanded ? '−' : '+'}</span>
      </div>

      {isExpanded && (
        <div className="problem-body">
          {isLoadingDetail ? (
            <div className="loading">Loading details...</div>
          ) : (
            <>
              <div className="problem-choices">
                {problem.choices.map((choice, index) => (
                  <div key={index} className="choice">
                    <span className="choice-letter">{String.fromCharCode(65 + index)})</span>
                    <LatexRenderer latex={choice} />
                  </div>
                ))}
              </div>

              {problem.tags.length > 0 && (
                <div className="problem-tags">
                  {problem.tags.map((tag) => (
                    <span key={tag} className="problem-tag">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {!showAnswer ? (
                <button className="reveal-answer-btn" onClick={handleRevealAnswer}>
                  Reveal Answer
                </button>
              ) : detail?.answer ? (
                <div className="answer-reveal">
                  <strong>Answer:</strong> {detail.answer}
                  {detail.solution && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <strong>Solution:</strong>
                      <LatexRenderer latex={detail.solution} />
                    </div>
                  )}
                </div>
              ) : (
                <div className="answer-reveal">
                  <em>Answer not available</em>
                </div>
              )}

              <HintChat problemId={problem.id} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
