import { PalaceExerciseSession, ExerciseSession } from '../types/palace';

const STORAGE_KEY = 'memory_palace_sessions';

/**
 * ExerciseSessionManager
 * Manages exercise sessions for memory palace training
 */
export class ExerciseSessionManager {
  private sessions: ExerciseSession[] = [];
  private currentSessionId: string | null = null;

  constructor() {
    this.loadSessions();
  }

  /**
   * Load sessions from localStorage
   */
  private loadSessions(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.sessions = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
      this.sessions = [];
    }
  }

  /**
   * Save sessions to localStorage
   */
  private saveSessions(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.sessions));
    } catch (error) {
      console.error('Error saving sessions:', error);
    }
  }

  /**
   * Create a new exercise session
   */
  createSession(palaceId: string, palaceName: string): ExerciseSession {
    const session: ExerciseSession = {
      id: this.generateId(),
      palaceId,
      palaceName,
      startTime: new Date().toISOString(),
      endTime: null,
      status: 'active',
      exercises: [],
      stats: {
        totalExercises: 0,
        completedExercises: 0,
        accuracy: 0,
        totalTime: 0,
      },
    };

    this.sessions.push(session);
    this.currentSessionId = session.id;
    this.saveSessions();

    return session;
  }

  /**
   * Get current session
   */
  getCurrentSession(): ExerciseSession | null {
    if (!this.currentSessionId) {
      return null;
    }

    const session = this.sessions.find(s => s.id === this.currentSessionId);
    return session || null;
  }

  /**
   * Get session by ID
   */
  getSession(sessionId: string): ExerciseSession | null {
    return this.sessions.find(s => s.id === sessionId) || null;
  }

  /**
   * Get all sessions
   */
  getAllSessions(): ExerciseSession[] {
    return this.sessions;
  }

  /**
   * Start a new exercise in the current session
   */
  startExercise(exerciseType: 'recall' | 'review' | 'quiz', palaceId: string): ExerciseSession {
    const session = this.getCurrentSession();
    if (!session) {
      throw new Error('No active session');
    }

    const exercise: PalaceExerciseSession = {
      id: this.generateId(),
      type: exerciseType,
      palaceId,
      startTime: new Date().toISOString(),
      endTime: null,
      status: 'active',
      results: null,
    };

    session.exercises.push(exercise);
    session.stats.totalExercises++;
    this.saveSessions();

    return session;
  }

  /**
   * Complete an exercise
   */
  completeExercise(
    exerciseId: string,
    results: {
      correct: number;
      total: number;
      timeSpent: number;
      accuracy: number;
    }
  ): ExerciseSession | null {
    const session = this.getCurrentSession();
    if (!session) {
      return null;
    }

    const exerciseIndex = session.exercises.findIndex(e => e.id === exerciseId);
    if (exerciseIndex === -1) {
      return null;
    }

    const exercise = session.exercises[exerciseIndex] as PalaceExerciseSession;
    exercise.endTime = new Date().toISOString();
    exercise.status = 'completed';
    exercise.results = results;

    // Update session stats
    session.stats.completedExercises++;
    session.stats.totalTime += results.timeSpent;
    session.stats.accuracy = Math.round(
      (session.stats.completedExercises / session.stats.totalExercises) * 100
    );

    this.saveSessions();
    return session;
  }

  /**
   * End the current session
   */
  endSession(): ExerciseSession | null {
    const session = this.getCurrentSession();
    if (!session) {
      return null;
    }

    session.endTime = new Date().toISOString();
    session.status = 'completed';
    this.saveSessions();

    this.currentSessionId = null;
    return session;
  }

  /**
   * Start a new session
   */
  startNewSession(palaceId: string, palaceName: string): ExerciseSession {
    // End current session if exists
    if (this.currentSessionId) {
      this.endSession();
    }

    return this.createSession(palaceId, palaceName);
  }

  /**
   * Delete a session
   */
  deleteSession(sessionId: string): boolean {
    const index = this.sessions.findIndex(s => s.id === sessionId);
    if (index === -1) {
      return false;
    }

    this.sessions.splice(index, 1);

    // If deleted session was current, clear current session
    if (this.currentSessionId === sessionId) {
      this.currentSessionId = null;
    }

    this.saveSessions();
    return true;
  }

  /**
   * Get session statistics
   */
  getSessionStats(sessionId: string): {
    totalExercises: number;
    completedExercises: number;
    accuracy: number;
    totalTime: number;
    averageTimePerExercise: number;
  } | null {
    const session = this.getSession(sessionId);
    if (!session) {
      return null;
    }

    const completedExercises = session.exercises.filter(e => e.status === 'completed');
    const totalTime = completedExercises.reduce((sum, e) => sum + (e.results?.timeSpent || 0), 0);

    return {
      totalExercises: session.stats.totalExercises,
      completedExercises: session.stats.completedExercises,
      accuracy: session.stats.accuracy,
      totalTime,
      averageTimePerExercise: session.stats.totalExercises > 0
        ? Math.round(totalTime / session.stats.totalExercises)
        : 0,
    };
  }

  /**
   * Get all completed sessions
   */
  getCompletedSessions(): ExerciseSession[] {
    return this.sessions.filter(s => s.status === 'completed');
  }

  /**
   * Get active session
   */
  getActiveSession(): ExerciseSession | null {
    return this.sessions.find(s => s.status === 'active') || null;
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const exerciseSessionManager = new ExerciseSessionManager();