import React, { useState, useCallback, useEffect } from 'react';
import { ExerciseSession, ExerciseType } from '../types/palace';
import { exerciseSessionManager } from '../managers/ExerciseSessionManager';
import './ExerciseSessionManager.css';

export interface ExerciseSessionManagerProps {
  palaceId: string;
  palaceName: string;
  onExerciseComplete?: (session: ExerciseSession) => void;
}

/**
 * ExerciseSessionManager Component
 * Manages exercise sessions for memory palace training
 */
const ExerciseSessionManager: React.FC<ExerciseSessionManagerProps> = ({
  palaceId,
  palaceName,
  onExerciseComplete,
}) => {
  const [currentSession, setCurrentSession] = useState<ExerciseSession | null>(null);
  const [sessions, setSessions] = useState<ExerciseSession[]>([]);
  const [activeExercise, setActiveExercise] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load sessions from manager
  const loadSessions = useCallback(() => {
    const allSessions = exerciseSessionManager.getAllSessions();
    setSessions(allSessions);
    
    const activeSession = exerciseSessionManager.getActiveSession();
    if (activeSession) {
      setCurrentSession(activeSession);
    }
  }, []);

  // Start a new session
  const handleStartSession = useCallback(() => {
    const session = exerciseSessionManager.startNewSession(palaceId, palaceName);
    setCurrentSession(session);
    setSessions(exerciseSessionManager.getAllSessions());
  }, [palaceId, palaceName]);

  // Start an exercise
  const handleStartExercise = useCallback((exerciseType: ExerciseType) => {
    if (!currentSession) {
      return;
    }

    const session = exerciseSessionManager.startExercise(exerciseType, palaceId);
    setCurrentSession(session);
    setSessions(exerciseSessionManager.getAllSessions());
    setActiveExercise(session.exercises[session.exercises.length - 1].id);
  }, [currentSession, palaceId]);

  // Complete an exercise
  const handleCompleteExercise = useCallback((
    exerciseId: string,
    results: {
      correct: number;
      total: number;
      timeSpent: number;
      accuracy: number;
    }
  ) => {
    const session = exerciseSessionManager.completeExercise(exerciseId, results);
    if (session) {
      setCurrentSession(session);
      setSessions(exerciseSessionManager.getAllSessions());
      setActiveExercise(null);
      onExerciseComplete?.(session);
    }
  }, [onExerciseComplete]);

  // End current session
  const handleEndSession = useCallback(() => {
    const session = exerciseSessionManager.endSession();
    if (session) {
      setCurrentSession(null);
      setSessions(exerciseSessionManager.getAllSessions());
      onExerciseComplete?.(session);
    }
  }, [onExerciseComplete]);

  // Delete a session
  const handleDeleteSession = useCallback((sessionId: string) => {
    exerciseSessionManager.deleteSession(sessionId);
    setSessions(exerciseSessionManager.getAllSessions());
    if (currentSession?.id === sessionId) {
      setCurrentSession(null);
    }
  }, [currentSession]);

  // Get session statistics
  const getSessionStats = useCallback((sessionId: string) => {
    return exerciseSessionManager.getSessionStats(sessionId);
  }, []);

  // Render current session stats
  const renderCurrentSessionStats = () => {
    if (!currentSession) {
      return null;
    }

    const stats = getSessionStats(currentSession.id);
    if (!stats) {
      return null;
    }

    return (
      <div className="exercise-session-stats">
        <div className="stat-item">
          <span className="stat-value">{stats.completedExercises}</span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.totalExercises}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{stats.accuracy}%</span>
          <span className="stat-label">Accuracy</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{Math.round(stats.totalTime / 60)}m</span>
          <span className="stat-label">Time</span>
        </div>
      </div>
    );
  };

  // Render session history
  const renderSessionHistory = () => {
    if (!showHistory) {
      return null;
    }

    const completedSessions = sessions.filter(s => s.status === 'completed');

    return (
      <div className="exercise-session-history">
        <h3>Session History</h3>
        <div className="session-list">
          {completedSessions.length === 0 ? (
            <p className="no-sessions">No completed sessions yet.</p>
          ) : (
            completedSessions.map(session => {
              const stats = getSessionStats(session.id);
              return (
                <div key={session.id} className="session-item">
                  <div className="session-info">
                    <span className="session-name">{session.palaceName}</span>
                    <span className="session-date">
                      {new Date(session.startTime).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="session-stats">
                    <span>{stats?.completedExercises || 0} exercises</span>
                    <span>{stats?.accuracy || 0}% accuracy</span>
                  </div>
                  <button
                    className="delete-session-btn"
                    onClick={() => handleDeleteSession(session.id)}
                  >
                    Delete
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  // Render active exercise indicator
  const renderActiveExercise = () => {
    if (!activeExercise) {
      return null;
    }

    return (
      <div className="active-exercise-indicator">
        <span className="indicator-dot"></span>
        <span>Exercise in progress...</span>
      </div>
    );
  };

  return (
    <div className="exercise-session-manager">
      {/* Header */}
      <div className="exercise-session-header">
        <h2>📚 Exercise Sessions</h2>
        <button
          className="toggle-history-btn"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? 'Hide History' : 'Show History'}
        </button>
      </div>

      {/* Current Session */}
      <div className="exercise-session-current">
        {currentSession ? (
          <>
            <div className="session-active">
              <span className="session-status active">Active Session</span>
              <span className="session-name">{currentSession.palaceName}</span>
            </div>
            
            {renderCurrentSessionStats()}
            
            <div className="exercise-actions">
              <button
                className="exercise-btn recall"
                onClick={() => handleStartExercise('recall')}
                disabled={!!activeExercise}
              >
                🧠 Recall Exercise
              </button>
              <button
                className="exercise-btn review"
                onClick={() => handleStartExercise('review')}
                disabled={!!activeExercise}
              >
                📖 Review Exercise
              </button>
              <button
                className="exercise-btn quiz"
                onClick={() => handleStartExercise('quiz')}
                disabled={!!activeExercise}
              >
                📝 Quiz Exercise
              </button>
            </div>

            {renderActiveExercise()}

            <button
              className="end-session-btn"
              onClick={handleEndSession}
              disabled={!activeExercise}
            >
              End Session
            </button>
          </>
        ) : (
          <div className="no-session">
            <p>No active session</p>
            <button className="start-session-btn" onClick={handleStartSession}>
              Start New Session
            </button>
          </div>
        )}
      </div>

      {/* Session History */}
      {renderSessionHistory()}
    </div>
  );
};

export default ExerciseSessionManager;