import React from 'react';
import { NumberItem } from '../../types/memoryPalace';

interface NumberItemProps {
  item: NumberItem;
  onClick?: (item: NumberItem) => void;
  isSelected?: boolean;
}

export const NumberItem: React.FC<NumberItemProps> = ({ item, onClick, isSelected }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  const formatNumber = (num: number): string => {
    if (item.format === 'binary') {
      return num.toString(2);
    } else if (item.format === 'hex') {
      return '0x' + num.toString(16).toUpperCase();
    } else if (item.format === 'octal') {
      return '0' + num.toString(8);
    } else if (item.format === 'roman') {
      return num.toString().replace(/\d/g, (d) => {
        const roman = ['I', 'V', 'X', 'L', 'C', 'D', 'M'];
        const map = [0, 10, 100, 1000];
        let result = '';
        let n = parseInt(d);
        for (let i = map.length - 1; i >= 0; i--) {
          const repeat = Math.floor(n / map[i]);
          result += roman[i + 1] || roman[i];
          n -= repeat * map[i];
        }
        return result;
      });
    }
    return num.toString();
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
      className={`number-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Number: ${item.value} (${formatNumber(item.value)})`}
      aria-selected={isSelected}
    >
      <div className="number-item-content">
        <span className="number-item-value">{formatNumber(item.value)}</span>
        {item.format && item.format !== 'decimal' && (
          <span className="number-item-format">
            ({item.format})
          </span>
        )}
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="number-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="number-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default NumberItem;
