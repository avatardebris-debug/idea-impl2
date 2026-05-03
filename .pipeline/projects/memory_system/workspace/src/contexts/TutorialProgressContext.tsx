import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Tutorial, TutorialProgress, ALL_TUTORIALS, getTutorialById, completeTutorial, resetTutorialProgress } from '../data/tutorials';

/**
 * Tutorial progress context type
 */
interface TutorialProgressContextType {
  progress: Record<string, TutorialProgress>;
  getProgress: (tutorialId: string) => TutorialProgress;
  updateProgress: (tutorialId: string, updates: Partial<TutorialProgress>) => void;
  completeTutorial: (tutorialId: string) => void;
  resetTutorial: (tutorialId: string) => void;
  getTutorialById: (id: string) => Tutorial | undefined;
  getCompletedTutorials: () => Tutorial[];
  getInProgressTutorials: () => Tutorial[];
  getBeginnerTutorials: () => Tutorial[];
  getIntermediateTutorials: () => Tutorial[];
  getAdvancedTutorials: () => Tutorial[];
  getTutorialSteps: (tutorialId: string) => number;
  getCurrentStep: (tutorialId: string) => number;
  canStartTutorial: (tutorialId: string) => boolean;
  getPrerequisites: (tutorialId: string) => string[];
}

/**
 * Create tutorial progress context
 */
const TutorialProgressContext = createContext<TutorialProgressContextType | undefined>(undefined);

/**
 * Tutorial progress provider component
 */
interface TutorialProgressProviderProps {
  children: ReactNode;
  initialProgress?: Record<string, TutorialProgress>;
}

export const TutorialProgressProvider: React.FC<TutorialProgressProviderProps> = ({
  children,
  initialProgress = {},
}) => {
  const [progress, setProgress] = useState<Record<string, TutorialProgress>>(initialProgress);

  /**
   * Get progress for a tutorial
   */
  const getProgress = useCallback((tutorialId: string): TutorialProgress => {
    if (!progress[tutorialId]) {
      // Create default progress if not exists
      const defaultProgress: TutorialProgress = {
        tutorialId,
        completed: false,
        currentStep: 0,
        lastAccessed: new Date().toISOString(),
      };
      setProgress(prev => ({ ...prev, [tutorialId]: defaultProgress }));
      return defaultProgress;
    }
    return progress[tutorialId];
  }, [progress]);

  /**
   * Update tutorial progress
   */
  const updateProgress = useCallback((tutorialId: string, updates: Partial<TutorialProgress>) => {
    setProgress(prev => ({
      ...prev,
      [tutorialId]: {
        ...getProgress(tutorialId),
        ...updates,
        lastAccessed: new Date().toISOString(),
      },
    }));
  }, [getProgress]);

  /**
   * Mark tutorial as completed
   */
  const completeTutorial = useCallback((tutorialId: string) => {
    setProgress(prev => ({
      ...prev,
      [tutorialId]: completeTutorial(tutorialId),
    }));
  }, []);

  /**
   * Reset tutorial progress
   */
  const resetTutorial = useCallback((tutorialId: string) => {
    setProgress(prev => ({
      ...prev,
      [tutorialId]: resetTutorialProgress(tutorialId),
    }));
  }, []);

  /**
   * Get tutorial by ID
   */
  const getTutorialById = useCallback((id: string): Tutorial | undefined => {
    return getTutorialById(id);
  }, []);

  /**
   * Get completed tutorials
   */
  const getCompletedTutorials = useCallback((): Tutorial[] => {
    return ALL_TUTORIALS.filter(tutorial => {
      const tutorialProgress = getProgress(tutorial.id);
      return tutorialProgress.completed;
    });
  }, [getProgress]);

  /**
   * Get tutorials in progress
   */
  const getInProgressTutorials = useCallback((): Tutorial[] => {
    return ALL_TUTORIALS.filter(tutorial => {
      const tutorialProgress = getProgress(tutorial.id);
      return !tutorialProgress.completed && tutorialProgress.currentStep < tutorial.steps.length;
    });
  }, [getProgress]);

  /**
   * Get beginner tutorials
   */
  const getBeginnerTutorials = useCallback((): Tutorial[] => {
    return ALL_TUTORIALS.filter(tutorial => tutorial.difficulty === 'beginner');
  }, []);

  /**
   * Get intermediate tutorials
   */
  const getIntermediateTutorials = useCallback((): Tutorial[] => {
    return ALL_TUTORIALS.filter(tutorial => tutorial.difficulty === 'intermediate');
  }, []);

  /**
   * Get advanced tutorials
   */
  const getAdvancedTutorials = useCallback((): Tutorial[] => {
    return ALL_TUTORIALS.filter(tutorial => tutorial.difficulty === 'advanced');
  }, []);

  /**
   * Get number of steps in a tutorial
   */
  const getTutorialSteps = useCallback((tutorialId: string): number => {
    const tutorial = getTutorialById(tutorialId);
    return tutorial?.steps.length || 0;
  }, [getTutorialById]);

  /**
   * Get current step for a tutorial
   */
  const getCurrentStep = useCallback((tutorialId: string): number => {
    const tutorialProgress = getProgress(tutorialId);
    return tutorialProgress.currentStep;
  }, [getProgress]);

  /**
   * Check if tutorial can be started (prerequisites met)
   */
  const canStartTutorial = useCallback((tutorialId: string): boolean => {
    const tutorial = getTutorialById(tutorialId);
    if (!tutorial || !tutorial.prerequisites) {
      return true;
    }

    // Check if all prerequisites are completed
    return tutorial.prerequisites.every(prereqId => {
      const prereqProgress = getProgress(prereqId);
      return prereqProgress.completed;
    });
  }, [getTutorialById, getProgress]);

  /**
   * Get prerequisites for a tutorial
   */
  const getPrerequisites = useCallback((tutorialId: string): string[] => {
    const tutorial = getTutorialById(tutorialId);
    return tutorial?.prerequisites || [];
  }, [getTutorialById]);

  const contextValue: TutorialProgressContextType = {
    progress,
    getProgress,
    updateProgress,
    completeTutorial,
    resetTutorial,
    getTutorialById,
    getCompletedTutorials,
    getInProgressTutorials,
    getBeginnerTutorials,
    getIntermediateTutorials,
    getAdvancedTutorials,
    getTutorialSteps,
    getCurrentStep,
    canStartTutorial,
    getPrerequisites,
  };

  return (
    <TutorialProgressContext.Provider value={contextValue}>
      {children}
    </TutorialProgressContext.Provider>
  );
};

/**
 * Hook to access tutorial progress context
 */
export const useTutorialProgress = (): TutorialProgressContextType => {
  const context = useContext(TutorialProgressContext);
  if (!context) {
    throw new Error('useTutorialProgress must be used within a TutorialProgressProvider');
  }
  return context;
};

export default TutorialProgressContext;
