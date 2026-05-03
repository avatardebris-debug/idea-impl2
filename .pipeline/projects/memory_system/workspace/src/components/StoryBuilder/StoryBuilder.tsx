import React, { useState, useCallback } from 'react';
import { Palace, Room } from '../types/palace';
import {
  StoryBuilderState,
  StoryBuilderConfig,
  buildStory,
  addStoryItem,
  removeStoryItem,
  exportStoryToPalace,
  importStoryFromPalace,
} from '../utils/storyBuilder';
import './StoryBuilder.css';

export interface StoryBuilderProps {
  palace: Palace;
  onStoryComplete?: (storyItems: StoryBuilderState['selectedItems']) => void;
  config?: StoryBuilderConfig;
}

const DEFAULT_CONFIG: StoryBuilderConfig = {
  maxItems: 10,
  maxStoryLength: 500,
  autoGenerate: false,
};

/**
 * StoryBuilder Component
 * Allows users to create and manage memory palace stories
 */
const StoryBuilder: React.FC<StoryBuilderProps> = ({
  palace,
  onStoryComplete,
  config = DEFAULT_CONFIG,
}) => {
  const [storyState, setStoryState] = useState<StoryBuilderState>({
    selectedItems: [],
    storyText: '',
    isGenerating: false,
    storyPreview: '',
  });

  const [newItemText, setNewItemText] = useState('');
  const [selectedRoomId, setSelectedRoomId] = useState<string>(palace.rooms[0]?.id || '');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const selectedRoom = palace.rooms.find(r => r.id === selectedRoomId);

  // Handle adding a new item to the story
  const handleAddItem = useCallback(() => {
    if (!newItemText.trim()) {
      setToastMessage('Please enter an item text');
      setTimeout(() => setToastMessage(null), 2000);
      return;
    }

    if (storyState.selectedItems.length >= config.maxItems) {
      setToastMessage(`Maximum ${config.maxItems} items allowed`);
      setTimeout(() => setToastMessage(null), 2000);
      return;
    }

    const newItems = addStoryItem(
      storyState.selectedItems,
      newItemText.trim(),
      selectedRoom?.name || 'Unknown Location',
      config
    );

    setStoryState(prev => ({
      ...prev,
      selectedItems: newItems,
      storyText: newItems.map(item => item.storyText).join(' '),
    }));

    setNewItemText('');
    setToastMessage('Item added to story');
    setTimeout(() => setToastMessage(null), 2000);
  }, [newItemText, storyState.selectedItems, selectedRoom, config]);

  // Handle removing an item from the story
  const handleRemoveItem = useCallback((itemId: string) => {
    const newItems = removeStoryItem(storyState.selectedItems, itemId);
    setStoryState(prev => ({
      ...prev,
      selectedItems: newItems,
      storyText: newItems.map(item => item.storyText).join(' '),
    }));
    setToastMessage('Item removed from story');
    setTimeout(() => setToastMessage(null), 2000);
  }, [storyState.selectedItems]);

  // Handle exporting story to palace
  const handleExportToPalace = useCallback(() => {
    if (storyState.selectedItems.length === 0) {
      setToastMessage('No items to export');
      setTimeout(() => setToastMessage(null), 2000);
      return;
    }

    const updatedPalace = exportStoryToPalace(storyState.selectedItems, palace);
    
    // In a real app, this would update the palace state
    // For now, we'll just call the callback
    onStoryComplete?.(storyState.selectedItems);
    
    setToastMessage(`Exported ${storyState.selectedItems.length} items to palace`);
    setTimeout(() => setToastMessage(null), 2000);
  }, [storyState.selectedItems, palace, onStoryComplete]);

  // Handle importing story from palace room
  const handleImportFromPalace = useCallback(() => {
    if (!selectedRoomId) {
      setToastMessage('Please select a room first');
      setTimeout(() => setToastMessage(null), 2000);
      return;
    }

    const importedState = importStoryFromPalace(palace, selectedRoomId);
    setStoryState(importedState);
    setToastMessage(`Imported ${importedState.selectedItems.length} items from room`);
    setTimeout(() => setToastMessage(null), 2000);
  }, [selectedRoomId, palace]);

  // Handle clearing the story
  const handleClearStory = useCallback(() => {
    setStoryState({
      selectedItems: [],
      storyText: '',
      isGenerating: false,
      storyPreview: '',
    });
    setToastMessage('Story cleared');
    setTimeout(() => setToastMessage(null), 2000);
  }, []);

  // Handle selecting a room
  const handleRoomChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedRoomId(e.target.value);
  }, []);

  // Handle story text update
  const handleStoryTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    if (newText.length <= config.maxStoryLength) {
      setStoryState(prev => ({
        ...prev,
        storyText: newText,
      }));
    }
  }, [config.maxStoryLength]);

  return (
    <div className="story-builder">
      {/* Header */}
      <div className="story-builder-header">
        <h2>📖 Story Builder</h2>
        <div className="story-builder-actions">
          <button
            className="btn btn-export"
            onClick={handleExportToPalace}
            disabled={storyState.selectedItems.length === 0}
          >
            Export to Palace
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="story-builder-main">
        {/* Input Section */}
        <div className="story-builder-input-section">
          <div className="story-builder-input-group">
            <label htmlFor="room-select">Select Room:</label>
            <select
              id="room-select"
              value={selectedRoomId}
              onChange={handleRoomChange}
            >
              {palace.rooms.map(room => (
                <option key={room.id} value={room.id}>
                  {room.name} ({room.items.length} items)
                </option>
              ))}
            </select>
          </div>

          <div className="story-builder-input-group">
            <label htmlFor="new-item">Add New Item:</label>
            <input
              type="text"
              id="new-item"
              value={newItemText}
              onChange={(e) => setNewItemText(e.target.value)}
              placeholder="Enter item text..."
              onKeyPress={(e) => e.key === 'Enter' && handleAddItem()}
            />
          </div>

          <div className="story-builder-input-actions">
            <button
              className="btn btn-add"
              onClick={handleAddItem}
              disabled={!newItemText.trim()}
            >
              Add Item
            </button>
            <button
              className="btn btn-generate"
              onClick={handleImportFromPalace}
            >
              Import from Room
            </button>
            <button
              className="btn btn-clear"
              onClick={handleClearStory}
            >
              Clear
            </button>
          </div>
        </div>

        {/* Output Section */}
        <div className="story-builder-output-section">
          <h3>Story Items ({storyState.selectedItems.length}/{config.maxItems})</h3>
          
          <div className="story-builder-story-list">
            {storyState.selectedItems.length === 0 ? (
              <div className="story-builder-empty-state">
                <div className="story-builder-empty-state-icon">📝</div>
                <p>No items in story yet. Add items or import from a room.</p>
              </div>
            ) : (
              storyState.selectedItems.map((item, index) => (
                <div key={item.id} className="story-builder-story-item">
                  <div className="story-builder-story-item-header">
                    <span className="story-builder-story-item-title">
                      {index + 1}. {item.text}
                    </span>
                    <span className="story-builder-story-item-location">
                      📍 {item.location}
                    </span>
                  </div>
                  <div className="story-builder-story-item-text">
                    {item.storyText}
                  </div>
                  <div className="story-builder-story-item-actions">
                    <button
                      className="btn btn-view"
                      onClick={() => {
                        setToastMessage(`Viewing: ${item.text}`);
                        setTimeout(() => setToastMessage(null), 2000);
                      }}
                    >
                      View
                    </button>
                    <button
                      className="btn btn-delete"
                      onClick={() => handleRemoveItem(item.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="story-builder-story-preview">
            <h4>Story Preview</h4>
            <div className="story-builder-story-preview-text">
              {storyState.storyText || 'Story preview will appear here...'}
            </div>
          </div>

          <div className="story-builder-stats">
            <div className="story-builder-stat">
              <span className="story-builder-stat-value">
                {storyState.selectedItems.length}
              </span>
              <span className="story-builder-stat-label">Items</span>
            </div>
            <div className="story-builder-stat">
              <span className="story-builder-stat-value">
                {storyState.storyText.length}
              </span>
              <span className="story-builder-stat-label">Characters</span>
            </div>
            <div className="story-builder-stat">
              <span className="story-builder-stat-value">
                {storyState.selectedItems.length > 0 
                  ? Math.round(storyState.storyText.length / storyState.selectedItems.length)
                  : 0}
              </span>
              <span className="story-builder-stat-label">Avg Length</span>
            </div>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="story-builder-toast">
          {toastMessage}
        </div>
      )}
    </div>
  );
};

export default StoryBuilder;