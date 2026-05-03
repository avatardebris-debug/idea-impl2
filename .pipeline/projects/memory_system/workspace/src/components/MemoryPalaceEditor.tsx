import React, { useState, useCallback } from 'react';
import { Palace, Room, Item } from '../types/palace';
import { useMemoryPalace } from '../hooks/useMemoryPalace';
import './MemoryPalaceEditor.css';

export interface MemoryPalaceEditorProps {
  palace: Palace;
  onUpdate: (palace: Palace) => void;
}

/**
 * MemoryPalaceEditor Component
 * Provides an interface for editing memory palace rooms and items
 */
const MemoryPalaceEditor: React.FC<MemoryPalaceEditorProps> = ({
  palace,
  onUpdate,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Use hooks for memory palace management
  const {
    state,
    actions,
    filteredRooms,
    totalItems,
  } = useMemoryPalace(palace);

  // Handle room selection for editing
  const handleRoomSelect = useCallback((roomId: string) => {
    actions.setEditingRoomId(roomId);
  }, [actions]);

  // Handle room deselection
  const handleRoomDeselect = useCallback(() => {
    actions.setEditingRoomId(null);
  }, [actions]);

  // Add a new item to the currently selected room
  const handleAddItem = useCallback(() => {
    if (!state.editingRoomId) {
      return;
    }

    const newItemText = prompt('Enter new item:');
    if (!newItemText || !newItemText.trim()) {
      return;
    }

    const newItem: Item = {
      id: `item-${Date.now()}`,
      text: newItemText.trim(),
      createdAt: new Date().toISOString(),
    };

    actions.addItemToRoom(state.editingRoomId, newItem);
  }, [state.editingRoomId, actions]);

  // Remove an item from the currently selected room
  const handleRemoveItem = useCallback((roomId: string, itemId: string) => {
    actions.deleteItemFromRoom(roomId, itemId);
  }, [actions]);

  // Add a new room
  const handleAddRoom = useCallback(() => {
    const roomName = prompt('Enter room name:');
    if (!roomName || !roomName.trim()) {
      return;
    }

    const newRoom: Room = {
      id: `room-${Date.now()}`,
      name: roomName.trim(),
      description: '',
      items: [],
    };

    actions.addRoom(newRoom);
  }, [actions]);

  // Remove a room
  const handleRemoveRoom = useCallback((roomId: string) => {
    if (window.confirm('Are you sure you want to delete this room? This will also delete all items in it.')) {
      actions.deleteRoom(roomId);
      if (state.editingRoomId === roomId) {
        actions.setEditingRoomId(null);
      }
    }
  }, [actions, state.editingRoomId]);

  // Handle room name update
  const handleRoomNameChange = useCallback((roomId: string, newName: string) => {
    actions.updateRoom(roomId, { name: newName });
  }, [actions]);

  // Handle room description update
  const handleRoomDescriptionChange = useCallback((roomId: string, newDescription: string) => {
    actions.updateRoom(roomId, { description: newDescription });
  }, [actions]);

  // Get the currently selected room
  const selectedRoom = state.editingRoomId 
    ? state.palace.rooms.find(room => room.id === state.editingRoomId) 
    : null;

  // Render room card
  const renderRoomCard = (room: Room) => {
    const isSelected = state.editingRoomId === room.id;
    const itemCount = room.items.length;

    return (
      <div
        key={room.id}
        className={`memory-palace-editor-room ${isSelected ? 'selected' : ''}`}
        onClick={() => handleRoomSelect(room.id)}
      >
        <div className="room-header">
          <input
            type="text"
            className="room-name-input"
            value={room.name}
            onChange={(e) => handleRoomNameChange(room.id, e.target.value)}
            onClick={(e) => e.stopPropagation()}
          />
          <button
            className="remove-room-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleRemoveRoom(room.id);
            }}
            title="Remove room"
          >
            🗑️
          </button>
        </div>
        <div className="room-stats">
          <span className="item-count">{itemCount} items</span>
        </div>
      </div>
    );
  };

  // Render item card
  const renderItemCard = (item: Item) => {
    return (
      <div key={item.id} className="memory-palace-editor-item">
        <span className="item-text">{item.text}</span>
        <button
          className="remove-item-btn"
          onClick={() => handleRemoveItem(state.editingRoomId!, item.id)}
          title="Remove item"
        >
          ✕
        </button>
      </div>
    );
  };

  // Render room editor panel
  const renderRoomEditor = () => {
    if (!selectedRoom) {
      return (
        <div className="room-editor-empty">
          <p>Select a room to start editing items</p>
        </div>
      );
    }

    return (
      <div className="room-editor-panel">
        <div className="room-editor-header">
          <h3>Editing: {selectedRoom.name}</h3>
          <button className="close-editor-btn" onClick={handleRoomDeselect}>
            ✕ Close
          </button>
        </div>

        <div className="room-editor-description">
          <input
            type="text"
            className="room-description-input"
            value={selectedRoom.description}
            onChange={(e) => handleRoomDescriptionChange(selectedRoom.id, e.target.value)}
            placeholder="Room description (optional)"
          />
        </div>

        <div className="room-editor-items">
          {selectedRoom.items.length === 0 ? (
            <p className="no-items">No items in this room yet.</p>
          ) : (
            selectedRoom.items.map(item => renderItemCard(item))
          )}
        </div>

        <div className="room-editor-add-item">
          <input
            type="text"
            className="add-item-input"
            placeholder="Enter new item..."
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddItem();
              }
            }}
          />
          <button className="add-item-btn" onClick={handleAddItem}>
            ➕ Add Item
          </button>
        </div>
      </div>
    );
  };

  // Render rooms list
  const renderRoomsList = () => (
    <div className="rooms-list">
      <div className="rooms-list-header">
        <h3>🏰 Rooms</h3>
        <button className="add-room-btn" onClick={handleAddRoom}>
          ➕ Add Room
        </button>
      </div>

      <div className="rooms-search">
        <input
          type="text"
          className="search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search rooms and items..."
        />
      </div>

      <div className="rooms-list-content">
        {filteredRooms.length === 0 ? (
          <p className="no-rooms">No rooms found.</p>
        ) : (
          filteredRooms.map(room => renderRoomCard(room))
        )}
      </div>
    </div>
  );

  // Render palace summary
  const renderPalaceSummary = () => (
    <div className="palace-summary">
      <h3>📊 Palace Summary</h3>
      <div className="summary-stats">
        <div className="stat-item">
          <span className="stat-value">{state.palace.rooms.length}</span>
          <span className="stat-label">Total Rooms</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{totalItems}</span>
          <span className="stat-label">Total Items</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{state.palace.relationships?.length || 0}</span>
          <span className="stat-label">Connections</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="memory-palace-editor">
      <div className="editor-header">
        <h2>✏️ Memory Palace Editor</h2>
        <div className="editor-actions">
          <button className="save-btn" onClick={() => onUpdate(state.palace)}>
            💾 Save Changes
          </button>
        </div>
      </div>

      <div className="editor-content">
        {/* Left Panel: Rooms List */}
        <div className="editor-left-panel">
          {renderRoomsList()}
          {renderPalaceSummary()}
        </div>

        {/* Right Panel: Room Editor */}
        <div className="editor-right-panel">
          {renderRoomEditor()}
        </div>
      </div>
    </div>
  );
};

export default MemoryPalaceEditor;
