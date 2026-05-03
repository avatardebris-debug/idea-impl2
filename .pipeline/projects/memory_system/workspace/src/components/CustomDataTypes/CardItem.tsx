import React from 'react';
import { CardItem } from '../../types/memoryPalace';

interface CardItemProps {
  item: CardItem;
  onClick?: (item: CardItem) => void;
  isSelected?: boolean;
}

export const CardItem: React.FC<CardItemProps> = ({ item, onClick, isSelected }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  const getSuitIcon = (suit: string): string => {
    switch (suit) {
      case 'hearts':
        return '♥';
      case 'diamonds':
        return '♦';
      case 'clubs':
        return '♣';
      case 'spades':
        return '♠';
      default:
        return '?';
    }
  };

  const getSuitColor = (suit: string): string => {
    return suit === 'hearts' || suit === 'diamonds' ? '#e91e63' : '#212121';
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
      className={`card-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Card: ${item.displayText}`}
      aria-selected={isSelected}
    >
      <div className="card-item-content">
        <div className="card-item-suit" style={{ color: getSuitColor(item.suit) }}>
          {getSuitIcon(item.suit)}
        </div>
        <div className="card-item-value">{item.value}</div>
        <div className="card-item-suit">
          {getSuitIcon(item.suit)}
        </div>
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="card-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="card-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default CardItem;
