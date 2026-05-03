import React from 'react';
import { Tutorial } from '../data/tutorials';
import './TutorialCard.css';

interface TutorialCardProps {
  tutorial: Tutorial;
  onClick?: (tutorial: Tutorial) => void;
  isCompleted?: boolean;
  currentStep?: number;
  canStart?: boolean;
}

const TutorialCard: React.FC<TutorialCardProps> = ({
  tutorial,
  onClick,
  isCompleted = false,
  currentStep = 0,
  canStart = false,
}) => {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'beginner';
      case 'intermediate':
        return 'intermediate';
      case 'advanced':
        return 'advanced';
      default:
        return 'beginner';
    }
  };

  return (
    <div className={`tutorial-card ${isCompleted ? 'completed' : ''} ${!canStart ? 'disabled' : ''}`}>
      <div className="tutorial-card-header">
        <div className="tutorial-card-step-badge">
          {isCompleted ? (
            <span className="completed-badge">✓ Completed</span>
          ) : (
            <span>Step {currentStep + 1} of {tutorial.steps.length}</span>
          )}
        </div>
        <span className={`tutorial-card-difficulty ${getDifficultyColor(tutorial.difficulty)}`}>
          {tutorial.difficulty}
        </span>
      </div>
      <h2 className="tutorial-card-title">{tutorial.title}</h2>
      <p className="tutorial-card-description">{tutorial.description}</p>
      <div className="tutorial-card-meta">
        <div className="tutorial-card-meta-item">
          <svg className="tutorial-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" strokeWidth="2" />
            <path d="M12 6v6l4 2" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span>{tutorial.estimatedTime} min</span>
        </div>
        <div className="tutorial-card-meta-item">
          <svg className="tutorial-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>{tutorial.steps.length} steps</span>
        </div>
      </div>
      {onClick && (
        <button className="tutorial-card-action-btn" onClick={() => onClick(tutorial)}>
          {isCompleted ? 'Review Again' : 'Start Tutorial'}
        </button>
      )}
    </div>
  );
};

export { TutorialCard };
