import React, { useMemo } from 'react';
import { DateItem, MemoryPalaceItemUnion } from '../../types/memoryPalace';

interface TimelineVisualizationProps {
  items: MemoryPalaceItemUnion[];
  onItemSelect?: (item: MemoryPalaceItemUnion) => void;
  selectedItemId?: string;
}

const formatDate = (dateValue: string | number): Date => {
  try {
    return new Date(dateValue);
  } catch {
    return new Date(0);
  }
};

const formatDateLabel = (date: Date): string => {
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const TimelineVisualization: React.FC<TimelineVisualizationProps> = ({
  items,
  onItemSelect,
  selectedItemId,
}) => {
  const dateItems = useMemo(() => {
    return items
      .filter((item): item is DateItem => item.type === 'date')
      .map((item) => ({
        ...item,
        dateObj: formatDate(item.value),
      }))
      .sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());
  }, [items]);

  const handleItemClick = (item: DateItem) => {
    if (onItemSelect) {
      onItemSelect(item);
    }
  };

  if (dateItems.length === 0) {
    return (
      <div className="timeline-visualization empty">
        <p className="timeline-empty-message">No date items to display</p>
      </div>
    );
  }

  const minDate = dateItems[0].dateObj;
  const maxDate = dateItems[dateItems.length - 1].dateObj;
  const totalDays = Math.max(
    1,
    Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24))
  );

  return (
    <div className="timeline-visualization" role="region" aria-label="Timeline visualization">
      <div className="timeline-header">
        <span className="timeline-date-range">
          {formatDateLabel(minDate)} — {formatDateLabel(maxDate)}
        </span>
        <span className="timeline-item-count">{dateItems.length} items</span>
      </div>

      <div className="timeline-container">
        <div className="timeline-track">
          {dateItems.map((item, index) => {
            const positionPercent = totalDays > 0
              ? ((item.dateObj.getTime() - minDate.getTime()) / (totalDays * 24 * 60 * 60 * 1000)) * 100
              : 0;

            return (
              <div
                key={item.id}
                className={`timeline-item ${selectedItemId === item.id ? 'selected' : ''}`}
                style={{ left: `${positionPercent}%` }}
                onClick={() => handleItemClick(item)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleItemClick(item);
                  }
                }}
                aria-label={`${formatDateLabel(item.dateObj)}: ${item.metadata.dateLabel || 'Date item'}`}
                aria-selected={selectedItemId === item.id}
              >
                <div className="timeline-item-marker">
                  <span className="timeline-item-icon">📅</span>
                </div>
                <div className="timeline-item-label">
                  <span className="timeline-item-date">{formatDateLabel(item.dateObj)}</span>
                  {item.metadata.dateLabel && (
                    <span className="timeline-item-title">{item.metadata.dateLabel}</span>
                  )}
                </div>
                {item.metadata.isEvent && (
                  <span className="timeline-item-event" title="Event">
                    🎯
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="timeline-scale">
        <span className="timeline-scale-start">{formatDateLabel(minDate)}</span>
        <span className="timeline-scale-end">{formatDateLabel(maxDate)}</span>
      </div>
    </div>
  );
};

export default TimelineVisualization;
