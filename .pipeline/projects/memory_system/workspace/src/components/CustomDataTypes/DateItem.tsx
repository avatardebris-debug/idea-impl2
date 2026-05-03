import React from 'react';
import { DateItem } from '../../types/memoryPalace';

interface DateItemProps {
  item: DateItem;
  onClick?: (item: DateItem) => void;
  isSelected?: boolean;
}

export const DateItem: React.FC<DateItemProps> = ({ item, onClick, isSelected }) => {
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
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return String(dateValue);
    }
  };

  const dateLabel = item.metadata.dateLabel || formatDate(item.value);

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
      className={`date-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Date: ${dateLabel}`}
      aria-selected={isSelected}
    >
      <div className="date-item-content">
        <span className="date-item-icon">📅</span>
        <span className="date-item-label">{dateLabel}</span>
        {item.metadata.isEvent && (
          <span className="date-item-event" title="Event">
            🎯
          </span>
        )}
        {item.metadata.recurring && (
          <span className="date-item-recurring" title="Recurring">
            🔄
          </span>
        )}
      </div>
      {item.metadata.category && (
        <span className="date-item-category">{item.metadata.category}</span>
      )}
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="date-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="date-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default DateItem;
