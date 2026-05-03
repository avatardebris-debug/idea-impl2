import React from 'react';
import { WordItem } from '../../types/memoryPalace';

interface WordItemProps {
  item: WordItem;
  onClick?: (item: WordItem) => void;
  isSelected?: boolean;
}

export const WordItem: React.FC<WordItemProps> = ({ item, onClick, isSelected }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
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
      className={`word-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Word: ${item.value}`}
      aria-selected={isSelected}
    >
      <div className="word-item-content">
        <span className="word-item-text">{item.value}</span>
        {item.metadata.definition && (
          <span className="word-item-definition" title={item.metadata.definition}>
            {item.metadata.definition}
          </span>
        )}
        {item.metadata.partOfSpeech && (
          <span className="word-item-pos">
            ({item.metadata.partOfSpeech})
          </span>
        )}
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="word-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="word-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default WordItem;
