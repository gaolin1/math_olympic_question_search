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
            <LatexRenderer latex={problem.statement} />
          </div>
          {problem.images && problem.images.length > 0 && (
            <div className="problem-images" style={{ marginTop: '0.75rem' }}>
              {problem.images.map((imgSrc, idx) => (
                <img
                  key={idx}
                  src={imgSrc}
                  alt={`Problem ${problem.problem_number} diagram ${idx + 1}`}
                  className="problem-image"
                  style={{
                    maxWidth: '100%',
                    maxHeight: '300px',
                    display: 'block',
                    margin: '0.5rem 0',
                    borderRadius: '4px',
                    border: '1px solid #e0e0e0'
                  }}
                />
              ))}
            </div>
          )}
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
