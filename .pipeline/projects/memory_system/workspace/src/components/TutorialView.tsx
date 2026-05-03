import React, { useState, useEffect } from 'react';
import { Tutorial, TutorialStep, TutorialProgress, getTutorialById, getProgress, updateProgress, completeTutorial, canStartTutorial } from '../data/tutorials';
import { TutorialCard } from './TutorialCard';
import { TutorialSteps } from './TutorialSteps';
import './TutorialView.css';

interface TutorialViewProps {
  tutorialId: string;
  onComplete?: () => void;
}

const TutorialView: React.FC<TutorialViewProps> = ({ tutorialId, onComplete }) => {
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    const loadedTutorial = getTutorialById(tutorialId);
    if (loadedTutorial) {
      setTutorial(loadedTutorial);
      const progress = getProgress(tutorialId);
      setCurrentStep(progress.currentStep);
      setIsCompleted(progress.completed);
    }
  }, [tutorialId, getTutorialById, getProgress]);

  const tutorialProgress = tutorial ? getProgress(tutorial.id) : null;
  const canStart = tutorial ? canStartTutorial(tutorial.id) : false;

  /**
   * Handle tutorial selection
   */
  const handleTutorialClick = (selectedTutorial: Tutorial) => {
    if (selectedTutorial.id === tutorialId) {
      setCurrentStep(0);
      updateProgress(selectedTutorial.id, { currentStep: 0, completed: false });
    }
  };

  /**
   * Handle step completion
   */
  const handleStepComplete = (stepId: string) => {
    if (!tutorial) return;

    const newStep = currentStep + 1;
    updateProgress(tutorial.id, { currentStep: newStep });

    if (newStep >= tutorial.steps.length) {
      completeTutorial(tutorial.id);
      setIsCompleted(true);
      onComplete?.();
    }
  };

  /**
   * Handle step change
   */
  const handleStepChange = (stepIndex: number) => {
    setCurrentStep(stepIndex);
    updateProgress(tutorial?.id || tutorialId, { currentStep: stepIndex });
  };

  /**
   * Handle tutorial restart
   */
  const handleRestart = () => {
    if (!tutorial) return;
    setCurrentStep(0);
    updateProgress(tutorial.id, { currentStep: 0, completed: false });
    setIsCompleted(false);
  };

  if (!tutorial) {
    return (
      <div className="tutorial-view">
        <div className="tutorial-view-loading">
          <div className="tutorial-view-spinner" />
          <p>Loading tutorial...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tutorial-view">
      {/* Tutorial Header */}
      <div className="tutorial-view-header">
        <div className="tutorial-view-title">
          <h1 className="tutorial-view-title-text">{tutorial.title}</h1>
          <div className="tutorial-view-badges">
            <span className={`tutorial-view-badge ${tutorial.difficulty}`}>
              {tutorial.difficulty}
            </span>
            {isCompleted && (
              <span className="tutorial-view-badge completed">
                ✓ Completed
              </span>
            )}
          </div>
        </div>
        <div className="tutorial-view-meta">
          <div className="tutorial-view-meta-item">
            <svg className="tutorial-view-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <path d="M12 6v6l4 2" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span>{tutorial.estimatedTime} min</span>
          </div>
          <div className="tutorial-view-meta-item">
            <svg className="tutorial-view-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>{tutorial.steps.length} steps</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="tutorial-view-progress">
        <div className="tutorial-view-progress-bar">
          <div
            className="tutorial-view-progress-fill"
            style={{ width: `${isCompleted ? 100 : ((currentStep + 1) / tutorial.steps.length) * 100}%` }}
          />
        </div>
        <div className="tutorial-view-progress-text">
          {isCompleted ? (
            <span className="tutorial-view-progress-completed">Tutorial Completed!</span>
          ) : (
            <>
              <span>Step {currentStep + 1} of {tutorial.steps.length}</span>
              <span className="tutorial-view-progress-percent">
                {Math.round(((currentStep + 1) / tutorial.steps.length) * 100)}%
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="tutorial-view-content">
        {/* Left Column - Tutorial Card */}
        <div className="tutorial-view-left">
          <TutorialCard
            tutorial={tutorial}
            onClick={handleTutorialClick}
            isCompleted={isCompleted}
            currentStep={currentStep}
            canStart={canStart}
          />

          {/* Learning Objectives */}
          <div className="tutorial-view-objectives">
            <h2 className="tutorial-view-objectives-title">Learning Objectives</h2>
            <ul className="tutorial-view-objectives-list">
              {tutorial.learningObjectives.map((objective, index) => (
                <li key={index} className="tutorial-view-objective-item">
                  <svg className="tutorial-view-check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  {objective}
                </li>
              ))}
            </ul>
          </div>

          {/* Prerequisites */}
          {tutorial.prerequisites && tutorial.prerequisites.length > 0 && (
            <div className="tutorial-view-prerequisites">
              <h2 className="tutorial-view-prerequisites-title">Prerequisites</h2>
              <div className="tutorial-view-prerequisites-list">
                {tutorial.prerequisites.map((prereqId, index) => (
                  <span key={index} className="tutorial-view-prerequisite-item">
                    {prereqId}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Tutorial Steps */}
        <div className="tutorial-view-right">
          <TutorialSteps
            steps={tutorial.steps}
            currentStep={currentStep}
            onStepComplete={handleStepComplete}
            onStepChange={handleStepChange}
          />
        </div>
      </div>

      {/* Completion Message */}
      {isCompleted && (
        <div className="tutorial-view-completion">
          <div className="tutorial-view-completion-content">
            <div className="tutorial-view-completion-icon">
              <svg className="tutorial-view-check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2 className="tutorial-view-completion-title">Congratulations!</h2>
            <p className="tutorial-view-completion-text">
              You've completed the {tutorial.title} tutorial.
            </p>
            <div className="tutorial-view-completion-actions">
              <button className="tutorial-view-completion-btn primary" onClick={handleRestart}>
                Restart Tutorial
              </button>
              <button className="tutorial-view-completion-btn secondary" onClick={onComplete}>
                Continue Learning
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TutorialView;
