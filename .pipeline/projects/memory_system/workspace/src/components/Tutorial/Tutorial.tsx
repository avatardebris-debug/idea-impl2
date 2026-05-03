import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getTutorialById,
  getTutorialSteps,
  getPrerequisites,
  getLearningObjectives,
  getBeginnerTutorials,
  getIntermediateTutorials,
  getAdvancedTutorials,
} from './TutorialData';
import TutorialCard from '../TutorialCard';
import TutorialSteps from '../TutorialSteps';
import './Tutorial.css';

const Tutorial: React.FC = () => {
  const { tutorialId } = useParams<{ tutorialId: string }>();
  const navigate = useNavigate();
  const [tutorial, setTutorial] = useState<any>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'beginner' | 'intermediate' | 'advanced'>('all');

  useEffect(() => {
    if (tutorialId) {
      const loadedTutorial = getTutorialById(tutorialId);
      setTutorial(loadedTutorial);
      setLoading(false);
    }
  }, [tutorialId]);

  const handleStepComplete = (stepId: string) => {
    if (!completedSteps.includes(stepId)) {
      setCompletedSteps([...completedSteps, stepId]);
    }
  };

  const handleNext = () => {
    if (currentStepIndex < (tutorial?.steps.length || 0) - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleBackToList = () => {
    navigate('/tutorials');
  };

  const handleStartTutorial = () => {
    setCurrentStepIndex(0);
    setCompletedSteps([]);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return '#10b981';
      case 'intermediate':
        return '#f59e0b';
      case 'advanced':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const filteredTutorials = () => {
    switch (filter) {
      case 'beginner':
        return getBeginnerTutorials();
      case 'intermediate':
        return getIntermediateTutorials();
      case 'advanced':
        return getAdvancedTutorials();
      default:
        return getTutorialById('loci-method-basics') ? [
          getTutorialById('loci-method-basics'),
          getTutorialById('story-technique'),
          getTutorialById('association-mastery'),
          getTutorialById('moonwalking-einstein'),
        ].filter(Boolean) : [];
    }
  };

  if (loading) {
    return (
      <div className="tutorial-container">
        <div className="tutorial-loading">
          <div className="tutorial-loading-spinner"></div>
          <p>Loading tutorial...</p>
        </div>
      </div>
    );
  }

  // Tutorial list view
  if (!tutorialId) {
    const tutorials = filteredTutorials();
    return (
      <div className="tutorial-page">
        <div className="tutorial-page-header">
          <h1 className="tutorial-page-title">Memory Training Tutorials</h1>
          <p className="tutorial-page-subtitle">Master the art of memory with guided practice</p>
        </div>

        <div className="tutorial-filter">
          <button
            className={`tutorial-filter-button ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`tutorial-filter-button ${filter === 'beginner' ? 'active' : ''}`}
            onClick={() => setFilter('beginner')}
          >
            Beginner
          </button>
          <button
            className={`tutorial-filter-button ${filter === 'intermediate' ? 'active' : ''}`}
            onClick={() => setFilter('intermediate')}
          >
            Intermediate
          </button>
          <button
            className={`tutorial-filter-button ${filter === 'advanced' ? 'active' : ''}`}
            onClick={() => setFilter('advanced')}
          >
            Advanced
          </button>
        </div>

        <div className="tutorial-grid">
          {tutorials.map((tut: any) => (
            <div
              key={tut.id}
              className="tutorial-card-item"
              onClick={() => navigate(`/tutorials/${tut.id}`)}
            >
              <div className="tutorial-card-item-header">
                <span
                  className="tutorial-difficulty-badge"
                  style={{ backgroundColor: getDifficultyColor(tut.difficulty) }}
                >
                  {tut.difficulty}
                </span>
              </div>
              <h3 className="tutorial-card-item-title">{tut.title}</h3>
              <p className="tutorial-card-item-description">{tut.description}</p>
              <div className="tutorial-card-item-meta">
                <span className="tutorial-card-item-duration">⏱ {tut.duration}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Tutorial detail view
  if (!tutorial) {
    return (
      <div className="tutorial-container">
        <div className="tutorial-error">
          <h2>Tutorial Not Found</h2>
          <button className="tutorial-button-primary" onClick={handleBackToList}>
            Back to Tutorials
          </button>
        </div>
      </div>
    );
  }

  const currentStep = tutorial.steps[currentStepIndex];
  const progress = ((completedSteps.length) / tutorial.steps.length) * 100;

  return (
    <div className="tutorial-container">
      <div className="tutorial-header">
        <div className="tutorial-title-section">
          <h1 className="tutorial-title">{tutorial.title}</h1>
          <div className="tutorial-meta">
            <span className="tutorial-duration">⏱ {tutorial.duration}</span>
            <span
              className={`tutorial-difficulty ${tutorial.difficulty}`}
              style={{ backgroundColor: getDifficultyColor(tutorial.difficulty) }}
            >
              {tutorial.difficulty}
            </span>
          </div>
        </div>
        <div className="tutorial-actions">
          <button className="tutorial-button-secondary" onClick={handleBackToList}>
            ← Back to Tutorials
          </button>
          <button className="tutorial-button-primary" onClick={handleStartTutorial}>
            Start Tutorial
          </button>
        </div>
      </div>

      {currentStepIndex === 0 && (
        <div className="tutorial-intro">
          <div className="tutorial-prerequisites">
            <h3>Prerequisites</h3>
            <ul>
              {tutorial.prerequisites?.length ? (
                tutorial.prerequisites.map((prereq: string) => (
                  <li key={prereq}>{prereq}</li>
                ))
              ) : (
                <li>No prerequisites - suitable for beginners!</li>
              )}
            </ul>
          </div>

          <div className="tutorial-objectives">
            <h3>Learning Objectives</h3>
            <ul>
              {tutorial.learningObjectives.map((objective: string, index: number) => (
                <li key={index}>{objective}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {currentStepIndex > 0 && (
        <div className="tutorial-progress">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-text">
            {completedSteps.length} of {tutorial.steps.length} steps completed
          </div>
        </div>
      )}

      {currentStep && (
        <div className="tutorial-content">
          <TutorialCard
            stepNumber={currentStepIndex + 1}
            totalSteps={tutorial.steps.length}
            title={currentStep.title}
            description={currentStep.description}
          />

          {currentStep.exercise && (
            <TutorialSteps
              exercise={currentStep.exercise.instructions}
              onComplete={handleStepComplete}
              tips={currentStep.tips || []}
            />
          )}

          <div className="tutorial-navigation">
            <button
              className="tutorial-button-secondary"
              onClick={handlePrevious}
              disabled={currentStepIndex === 0}
            >
              ← Previous
            </button>

            {currentStepIndex === tutorial.steps.length - 1 ? (
              <button
                className="tutorial-button-success"
                onClick={handleBackToList}
              >
                Complete & Return to List
              </button>
            ) : (
              <button
                className="tutorial-button-primary"
                onClick={handleNext}
              >
                Next →
              </button>
            )}
          </div>
        </div>
      )}

      {currentStepIndex === tutorial.steps.length && (
        <div className="tutorial-complete">
          <div className="complete-icon">🎉</div>
          <h2>Tutorial Complete!</h2>
          <p>You've successfully completed the {tutorial.title} tutorial.</p>
          <button className="tutorial-button-primary" onClick={handleBackToList}>
            Explore More Tutorials
          </button>
        </div>
      )}
    </div>
  );
};

export default Tutorial;
