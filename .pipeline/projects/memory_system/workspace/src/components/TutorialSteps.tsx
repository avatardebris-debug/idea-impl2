import React, { useState } from 'react';
import { TutorialStep } from '../data/tutorials';
import './TutorialSteps.css';

interface TutorialStepsProps {
  steps: TutorialStep[];
  currentStep: number;
  onStepComplete: (stepId: string) => void;
  onStepChange: (stepIndex: number) => void;
}

const TutorialSteps: React.FC<TutorialStepsProps> = ({
  steps,
  currentStep,
  onStepComplete,
  onStepChange,
}) => {
  const [isComplete, setIsComplete] = useState(false);

  const currentTutorialStep = steps[currentStep];

  const handleComplete = () => {
    setIsComplete(true);
    onStepComplete(currentTutorialStep.id);
  };

  const handleReview = () => {
    setIsComplete(false);
  };

  if (!currentTutorialStep) {
    return (
      <div className="tutorial-steps">
        <div className="tutorial-steps-empty">
          <p>No steps available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tutorial-steps">
      {/* Step Navigation */}
      <div className="tutorial-steps-nav">
        <button
          className={`tutorial-steps-nav-btn ${currentStep === 0 ? 'disabled' : ''}`}
          onClick={() => onStepChange(currentStep - 1)}
          disabled={currentStep === 0}
        >
          <svg className="tutorial-steps-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M15 19l-7-7 7-7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Previous
        </button>
        <div className="tutorial-steps-nav-progress">
          <span>Step {currentStep + 1} of {steps.length}</span>
        </div>
        <button
          className={`tutorial-steps-nav-btn ${currentStep === steps.length - 1 ? 'disabled' : ''}`}
          onClick={() => onStepChange(currentStep + 1)}
          disabled={currentStep === steps.length - 1}
        >
          Next
          <svg className="tutorial-steps-nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M9 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* Step Content */}
      <div className="tutorial-steps-content">
        <div className="tutorial-steps-header">
          <h2 className="tutorial-steps-title">{currentTutorialStep.title}</h2>
          <div className="tutorial-steps-badge">
            {currentTutorialStep.exercise?.type || 'information'}
          </div>
        </div>
        <p className="tutorial-steps-description">{currentTutorialStep.description}</p>

        {/* Exercise Section */}
        {currentTutorialStep.exercise && (
          <div className="tutorial-steps-exercise">
            <div className="tutorial-steps-exercise-header">
              <svg className="tutorial-steps-exercise-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <h3 className="tutorial-steps-exercise-title">Exercise</h3>
            </div>
            <p className="tutorial-steps-exercise-instructions">{currentTutorialStep.exercise.instructions}</p>
            <div className="tutorial-steps-exercise-success">
              <svg className="tutorial-steps-exercise-check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="tutorial-steps-exercise-success-text">{currentTutorialStep.exercise.successCriteria}</span>
            </div>
          </div>
        )}

        {/* Tips Section */}
        {currentTutorialStep.tips && currentTutorialStep.tips.length > 0 && (
          <div className="tutorial-steps-tips">
            <div className="tutorial-steps-tips-header">
              <svg className="tutorial-steps-tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386a3.374 3.374 0 00-1.654-1.653z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <h3 className="tutorial-steps-tips-title">Tips</h3>
            </div>
            <ul className="tutorial-steps-tips-list">
              {currentTutorialStep.tips.map((tip, index) => (
                <li key={index} className="tutorial-steps-tip-item">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="tutorial-steps-actions">
          <button
            className="tutorial-steps-action-btn review"
            onClick={handleReview}
          >
            Review
          </button>
          <button
            className="tutorial-steps-action-btn complete"
            onClick={handleComplete}
          >
            {isComplete ? '✓ Complete' : 'Mark Complete'}
          </button>
        </div>
      </div>
    </div>
  );
};

export { TutorialSteps };
