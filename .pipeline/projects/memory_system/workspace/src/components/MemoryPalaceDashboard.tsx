import React, { useState, useCallback, useEffect } from 'react';
import { Palace, Room, PalaceStats, ExerciseSession, ExerciseType } from '../types/palace';
import { memoryPalaceManager } from '../managers/MemoryPalaceManager';
import { exerciseSessionManager } from '../managers/ExerciseSessionManager';
import { useMemoryPalace } from '../hooks/useMemoryPalace';
import { useVisualization } from '../hooks/useVisualization';
import { useNetworkGraph } from '../hooks/useNetworkGraph';
import MemoryPalaceVisualization from './MemoryPalaceVisualization';
import MemoryPalaceEditor from './MemoryPalaceEditor';
import MemoryPalaceAnalytics from './MemoryPalaceAnalytics';
import ExerciseSessionManager from './ExerciseSessionManager';
import './MemoryPalaceDashboard.css';

export interface DashboardConfig {
  showVisualization: boolean;
  showEditor: boolean;
  showAnalytics: boolean;
  showExerciseManager: boolean;
  defaultView: 'visualization' | 'editor' | 'analytics' | 'exercise';
}

const DEFAULT_CONFIG: DashboardConfig = {
  showVisualization: true,
  showEditor: true,
  showAnalytics: true,
  showExerciseManager: true,
  defaultView: 'visualization',
};

/**
 * MemoryPalaceDashboard Component
 * Main dashboard for memory palace management
 */
const MemoryPalaceDashboard: React.FC<{ config?: DashboardConfig }> = ({
  config = DEFAULT_CONFIG,
}) => {
  const [activePalace, setActivePalace] = useState<Palace | null>(null);
  const [palaces, setPalaces] = useState<Palace[]>([]);
  const [activeView, setActiveView] = useState<'visualization' | 'editor' | 'analytics' | 'exercise'>(
    config.defaultView
  );
  const [exerciseHistory, setExerciseHistory] = useState<
    Array<{
      palaceId: string;
      date: string;
      accuracy: number;
      timeSpent: number;
      itemsRecalled: number;
    }>
  >([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPalaceName, setNewPalaceName] = useState('');
  const [newPalaceDescription, setNewPalaceDescription] = useState('');

  // Use hooks for memory palace management
  const { 
    rooms, 
    items, 
    relationships, 
    addRoom, 
    removeRoom, 
    addItem, 
    removeItem, 
    addRelationship, 
    removeRelationship 
  } = useMemoryPalace();

  // Use hooks for visualization settings
  const { 
    viewMode, 
    showLabels, 
    showConnections, 
    highlightActive, 
    zoomLevel, 
    setViewMode, 
    setShowLabels, 
    setShowConnections, 
    setHighlightActive, 
    setZoomLevel 
  } = useVisualization();

  // Use hooks for network graph
  const { 
    nodes, 
    edges, 
    selectedNode, 
    setSelectedNode, 
    handleRemoveRelationship, 
    handleAddRelationship 
  } = useNetworkGraph();

  // Load palaces on mount
  useEffect(() => {
    loadPalaces();
  }, []);

  // Load palaces from manager
  const loadPalaces = useCallback(() => {
    const allPalaces = memoryPalaceManager.getAllPalaces();
    setPalaces(allPalaces);

    // Set first palace as active if none selected
    if (allPalaces.length > 0 && !activePalace) {
      setActivePalace(allPalaces[0]);
    }
  }, [activePalace]);

  // Create a new palace
  const handleCreatePalace = useCallback(() => {
    if (!newPalaceName.trim()) {
      return;
    }

    const palace = memoryPalaceManager.createPalace(
      newPalaceName.trim(),
      newPalaceDescription.trim()
    );
    setPalaces(memoryPalaceManager.getAllPalaces());
    setActivePalace(palace);
    setShowCreateModal(false);
    setNewPalaceName('');
    setNewPalaceDescription('');
  }, [newPalaceName, newPalaceDescription]);

  // Delete a palace
  const handleDeletePalace = useCallback((palaceId: string) => {
    memoryPalaceManager.deletePalace(palaceId);
    setPalaces(memoryPalaceManager.getAllPalaces());
    if (activePalace?.id === palaceId) {
      setActivePalace(null);
    }
  }, [activePalace]);

  // Select a palace
  const handleSelectPalace = useCallback((palace: Palace) => {
    setActivePalace(palace);
  }, []);

  // Update palace
  const handleUpdatePalace = useCallback((updatedPalace: Palace) => {
    memoryPalaceManager.updatePalace(updatedPalace);
    setPalaces(memoryPalaceManager.getAllPalaces());
    setActivePalace(updatedPalace);
  }, []);

  // Handle exercise completion
  const handleExerciseComplete = useCallback((session: ExerciseSession) => {
    // Update exercise history
    setExerciseHistory(prev => [
      ...prev,
      {
        palaceId: session.palaceId,
        date: new Date().toISOString(),
        accuracy: session.stats.accuracy,
        timeSpent: session.stats.totalTime,
        itemsRecalled: session.stats.completedExercises,
      },
    ]);
  }, []);

  // Calculate palace stats
  const palaceStats = activePalace
    ? memoryPalaceManager.getPalaceStats(activePalace.id)
    : null;

  // Get exercise history for current palace
  const currentPalaceExerciseHistory = exerciseHistory.filter(
    entry => entry.palaceId === activePalace?.id
  );

  // Render palace list
  const renderPalaceList = () => (
    <div className="dashboard-palace-list">
      <h3>🏰 Your Memory Palaces</h3>
      <div className="palace-list">
        {palaces.length === 0 ? (
          <p className="no-palaces">No memory palaces yet. Create one to get started!</p>
        ) : (
          palaces.map(palace => (
            <div
              key={palace.id}
              className={`palace-item ${activePalace?.id === palace.id ? 'active' : ''}`}
              onClick={() => handleSelectPalace(palace)}
            >
              <div className="palace-info">
                <span className="palace-name">{palace.name}</span>
                <span className="palace-stats">
                  {palace.rooms.length} rooms, {palace.rooms.reduce((sum, room) => sum + room.items.length, 0)} items
                </span>
              </div>
              <button
                className="delete-palace-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeletePalace(palace.id);
                }}
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
      <button
        className="create-palace-btn"
        onClick={() => setShowCreateModal(true)}
      >
        ➕ Create New Palace
      </button>
    </div>
  );

  // Render visualization view
  const renderVisualizationView = () => (
    <div className="dashboard-view">
      <h3>🖼️ Memory Palace Visualization</h3>
      <MemoryPalaceVisualization
        palace={activePalace!}
        onRoomSelect={(room) => console.log('Room selected:', room)}
        onItemSelect={(item) => console.log('Item selected:', item)}
      />
    </div>
  );

  // Render editor view
  const renderEditorView = () => (
    <div className="dashboard-view">
      <h3>✏️ Memory Palace Editor</h3>
      <MemoryPalaceEditor
        palace={activePalace!}
        onUpdate={handleUpdatePalace}
      />
    </div>
  );

  // Render analytics view
  const renderAnalyticsView = () => (
    <div className="dashboard-view">
      <h3>📊 Memory Palace Analytics</h3>
      <MemoryPalaceAnalytics
        palace={activePalace!}
        exerciseHistory={currentPalaceExerciseHistory}
        onInsightClick={(insight) => console.log('Insight clicked:', insight)}
      />
    </div>
  );

  // Render exercise view
  const renderExerciseView = () => (
    <div className="dashboard-view">
      <h3>🧠 Exercise Session Manager</h3>
      <ExerciseSessionManager
        palace={activePalace!}
        onExerciseComplete={handleExerciseComplete}
      />
    </div>
  );

  // Render create palace modal
  const renderCreateModal = () => (
    <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>🏰 Create New Memory Palace</h3>
        <div className="modal-form">
          <div className="form-group">
            <label htmlFor="palaceName">Palace Name *</label>
            <input
              type="text"
              id="palaceName"
              value={newPalaceName}
              onChange={(e) => setNewPalaceName(e.target.value)}
              placeholder="e.g., My Childhood Home"
            />
          </div>
          <div className="form-group">
            <label htmlFor="palaceDescription">Description</label>
            <textarea
              id="palaceDescription"
              value={newPalaceDescription}
              onChange={(e) => setNewPalaceDescription(e.target.value)}
              placeholder="Describe the layout and purpose of this palace"
              rows={4}
            />
          </div>
        </div>
        <div className="modal-actions">
          <button
            className="btn-cancel"
            onClick={() => setShowCreateModal(false)}
          >
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleCreatePalace}
            disabled={!newPalaceName.trim()}
          >
            Create Palace
          </button>
        </div>
      </div>
    </div>
  );

  // Render main content
  const renderMainContent = () => {
    if (!activePalace) {
      return (
        <div className="no-palace-selected">
          <h3>🏰 No Palace Selected</h3>
          <p>Select a memory palace from the list or create a new one to get started.</p>
          <button
            className="btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            Create New Palace
          </button>
        </div>
      );
    }

    return (
      <div className="dashboard-main-content">
        {/* View Tabs */}
        <div className="view-tabs">
          {config.showVisualization && (
            <button
              className={`tab ${activeView === 'visualization' ? 'active' : ''}`}
              onClick={() => setActiveView('visualization')}
            >
              🖼️ Visualization
            </button>
          )}
          {config.showEditor && (
            <button
              className={`tab ${activeView === 'editor' ? 'active' : ''}`}
              onClick={() => setActiveView('editor')}
            >
              ✏️ Editor
            </button>
          )}
          {config.showAnalytics && (
            <button
              className={`tab ${activeView === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveView('analytics')}
            >
              📊 Analytics
            </button>
          )}
          {config.showExerciseManager && (
            <button
              className={`tab ${activeView === 'exercise' ? 'active' : ''}`}
              onClick={() => setActiveView('exercise')}
            >
              🧠 Exercises
            </button>
          )}
        </div>

        {/* View Content */}
        <div className="view-content">
          {activeView === 'visualization' && renderVisualizationView()}
          {activeView === 'editor' && renderEditorView()}
          {activeView === 'analytics' && renderAnalyticsView()}
          {activeView === 'exercise' && renderExerciseView()}
        </div>
      </div>
    );
  };

  return (
    <div className="memory-palace-dashboard">
      <div className="dashboard-container">
        {/* Sidebar */}
        <aside className="dashboard-sidebar">
          {renderPalaceList()}
        </aside>

        {/* Main Content */}
        <main className="dashboard-main">
          {activePalace && (
            <header className="dashboard-header">
              <h1>{activePalace.name}</h1>
              {activePalace.description && (
                <p className="palace-description">{activePalace.description}</p>
              )}
            </header>
          )}
          {renderMainContent()}
        </main>
      </div>

      {/* Create Modal */}
      {showCreateModal && renderCreateModal()}
    </div>
  );
};

export default MemoryPalaceDashboard;
