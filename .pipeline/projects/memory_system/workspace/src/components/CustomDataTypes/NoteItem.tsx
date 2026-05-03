import React from 'react';
import { NoteItem } from '../../types/memoryPalace';

interface NoteItemProps {
  item: NoteItem;
  onClick?: (item: NoteItem) => void;
  isSelected?: boolean;
}

export const NoteItem: React.FC<NoteItemProps> = ({ item, onClick, isSelected }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  const formatDate = (dateValue: string | number): string => {
    try {
      const date = new Date(dateValue);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return String(dateValue);
    }
  };

  return (
    <div
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
      className={`note-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Note: ${item.value}`}
      aria-selected={isSelected}
    >
      <div className="note-item-content">
        <span className="note-item-title">{item.value}</span>
        <span className="note-item-text">{item.metadata.text || item.value}</span>
        {item.metadata.tags && item.metadata.tags.length > 0 && (
          <div className="note-item-tags">
            {item.metadata.tags.map((tag, index) => (
              <span key={index} className="note-item-tag">
                {tag}
              </span>
            ))}
          </div>
        )}
        {item.metadata.date && (
          <span className="note-item-date">
            📅 {formatDate(item.metadata.date)}
          </span>
        )}
      </div>
    </div>
  );
};

export default NoteItem;
