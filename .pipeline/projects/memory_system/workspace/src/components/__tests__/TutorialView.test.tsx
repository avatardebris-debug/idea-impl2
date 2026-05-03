import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TutorialView } from './TutorialView';
import { TutorialProgressProvider, useTutorialProgress } from '../contexts/TutorialProgressContext';
import { tutorials } from '../data/tutorials';

// Mock the context
jest.mock('../contexts/TutorialProgressContext', () => ({
  useTutorialProgress: jest.fn(),
}));

// Mock the TutorialCard component
jest.mock('./TutorialCard', () => ({
  TutorialCard: ({ tutorial, onClick, isCompleted, currentStep, canStart }: any) => (
    <div data-testid="tutorial-card">
      <h2>{tutorial.title}</h2>
      <button onClick={() => onClick(tutorial)}>Select Tutorial</button>
      {isCompleted && <span data-testid="completed-badge">Completed</span>}
      <span data-testid="current-step">{currentStep}</span>
      {!canStart && <span data-testid="locked-badge">Locked</span>}
    </div>
  ),
}));

// Mock the TutorialSteps component
jest.mock('./TutorialSteps', () => ({
  TutorialSteps: ({ steps, currentStep, onStepComplete, onStepChange }: any) => (
    <div data-testid="tutorial-steps">
      {steps.map((step: any, index: number) => (
        <div key={step.id} data-testid={`step-${index}`}>
          <h3>{step.title}</h3>
          <p>{step.content}</p>
          {index < steps.length - 1 && (
            <button onClick={() => onStepComplete(step.id)}>Complete Step</button>
          )}
        </div>
      ))}
      <button onClick={() => onStepChange(0)}>Go to Step 0</button>
    </div>
  ),
}));

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <TutorialProgressProvider>
      {component}
    </TutorialProgressProvider>
  );
};

describe('TutorialView', () => {
  const mockTutorial = tutorials[0];
  const mockOnComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('initial rendering', () => {
    it('renders the tutorial title', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText(mockTutorial.title)).toBeInTheDocument();
    });

    it('renders the tutorial description', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText(mockTutorial.description)).toBeInTheDocument();
    });

    it('renders the estimated time', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText(`${mockTutorial.estimatedTime} min`)).toBeInTheDocument();
    });

    it('renders the number of steps', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText(`${mockTutorial.steps.length} steps`)).toBeInTheDocument();
    });

    it('renders learning objectives', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      mockTutorial.learningObjectives.forEach((objective) => {
        expect(screen.getByText(objective)).toBeInTheDocument();
      });
    });

    it('renders prerequisites if they exist', () => {
      const tutorialWithPrereqs = {
        ...mockTutorial,
        prerequisites: ['memory-basics'],
      };

      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => tutorialWithPrereqs,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={tutorialWithPrereqs.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('memory-basics')).toBeInTheDocument();
    });
  });

  describe('progress tracking', () => {
    it('displays current step number', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();
    });

    it('displays progress percentage', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('60%')).toBeInTheDocument();
    });

    it('renders progress bar with correct width', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const progressBar = screen.getByTestId('progress-bar');
      expect(progressBar).toHaveStyle('width: 60%');
    });

    it('marks tutorial as completed when all steps are done', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
  });

  describe('navigation', () => {
    it('allows navigation to next step', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const nextButton = screen.getByText('Next Step');
      fireEvent.click(nextButton);

      expect(updateProgressMock).toHaveBeenCalledWith(mockTutorial.id, 1);
    });

    it('disables next button on last step', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const nextButton = screen.getByText('Next Step');
      expect(nextButton).toBeDisabled();
    });

    it('allows navigation to previous step', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const prevButton = screen.getByText('Previous Step');
      fireEvent.click(prevButton);

      expect(updateProgressMock).toHaveBeenCalledWith(mockTutorial.id, 1);
    });

    it('disables previous button on first step', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const prevButton = screen.getByText('Previous Step');
      expect(prevButton).toBeDisabled();
    });

    it('calls onComplete when tutorial is completed', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const continueButton = screen.getByText('Continue Learning');
      fireEvent.click(continueButton);

      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('restart functionality', () => {
    it('allows restarting the tutorial', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const restartButton = screen.getByText('Restart Tutorial');
      fireEvent.click(restartButton);

      expect(updateProgressMock).toHaveBeenCalledWith(mockTutorial.id, 0);
    });

    it('resets completion status on restart', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: true }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const restartButton = screen.getByText('Restart Tutorial');
      fireEvent.click(restartButton);

      expect(updateProgressMock).toHaveBeenCalledWith(mockTutorial.id, 0);
    });
  });

  describe('completion screen', () => {
    it('shows completion screen when tutorial is finished', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('🎉 Tutorial Completed!')).toBeInTheDocument();
      expect(screen.getByText('Congratulations!')).toBeInTheDocument();
    });

    it('shows completion percentage', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('provides continue button on completion', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('Continue Learning')).toBeInTheDocument();
    });

    it('provides restart button on completion', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 4, completed: true }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('Restart Tutorial')).toBeInTheDocument();
    });
  });

  describe('error handling', () => {
    it('handles missing tutorial gracefully', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => null,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      const { container } = renderWithProvider(
        <TutorialView tutorialId="non-existent" onComplete={mockOnComplete} />
      );

      expect(container.querySelector('p')).toHaveTextContent('Tutorial not found');
    });

    it('handles invalid tutorial ID', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => null,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      const { container } = renderWithProvider(
        <TutorialView tutorialId="" onComplete={mockOnComplete} />
      );

      expect(container.querySelector('p')).toHaveTextContent('Tutorial not found');
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA labels', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const nextButton = screen.getByText('Next Step');
      expect(nextButton).toHaveAttribute('aria-label', 'Go to next step');

      const prevButton = screen.getByText('Previous Step');
      expect(prevButton).toHaveAttribute('aria-label', 'Go to previous step');
    });

    it('has proper heading hierarchy', () => {
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent(mockTutorial.title);
    });
  });

  describe('localStorage integration', () => {
    it('persists progress to localStorage', () => {
      const updateProgressMock = jest.fn();
      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 0, completed: false }),
        updateProgress: updateProgressMock,
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      const nextButton = screen.getByText('Next Step');
      fireEvent.click(nextButton);

      expect(updateProgressMock).toHaveBeenCalled();
    });

    it('loads progress from localStorage on mount', () => {
      const savedProgress = {
        'memory-basics': {
          currentStep: 2,
          completed: false,
        },
      };
      localStorage.setItem('memory-tutorial-progress', JSON.stringify(savedProgress));

      (useTutorialProgress as jest.Mock).mockReturnValue({
        getTutorialById: () => mockTutorial,
        getProgress: () => ({ currentStep: 2, completed: false }),
        updateProgress: jest.fn(),
        completeTutorial: jest.fn(),
        canStartTutorial: () => true,
      });

      renderWithProvider(
        <TutorialView tutorialId={mockTutorial.id} onComplete={mockOnComplete} />
      );

      expect(screen.getByText('Step 3 of 5')).toBeInTheDocument();
    });
  });
});
