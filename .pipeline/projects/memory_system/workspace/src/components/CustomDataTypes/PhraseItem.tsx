import React from 'react';
import { PhraseItem } from '../../types/memoryPalace';

interface PhraseItemProps {
  item: PhraseItem;
  onClick?: (item: PhraseItem) => void;
  isSelected?: boolean;
}

export const PhraseItem: React.FC<PhraseItemProps> = ({ item, onClick, isSelected }) => {
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
      className={`phrase-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Phrase: ${item.value}`}
      aria-selected={isSelected}
    >
      <div className="phrase-item-content">
        <span className="phrase-item-text">"{item.value}"</span>
        {(item.metadata.author || item.metadata.source) && (
          <span className="phrase-item-attribution">
            {item.metadata.author && <span>— {item.metadata.author}</span>}
            {item.metadata.source && <span> ({item.metadata.source})</span>}
          </span>
        )}
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="phrase-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="phrase-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default PhraseItem;
