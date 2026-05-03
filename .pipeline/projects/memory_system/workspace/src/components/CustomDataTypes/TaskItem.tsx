import React from 'react';
import { TaskItem } from '../../types/memoryPalace';

interface TaskItemProps {
  item: TaskItem;
  onClick?: (item: TaskItem) => void;
  isSelected?: boolean;
}

export const TaskItem: React.FC<TaskItemProps> = ({ item, onClick, isSelected }) => {
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

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'high';
      case 'medium':
        return 'medium';
      case 'low':
        return 'low';
      default:
        return 'medium';
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
      className={`task-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Task: ${item.value}, ${item.metadata.status || 'pending'}`}
      aria-selected={isSelected}
    >
      <div className="task-item-content">
        <span className="task-item-title">{item.value}</span>
        {item.metadata.description && (
          <span className="task-item-description">{item.metadata.description}</span>
        )}
        <span className={`task-item-status ${item.metadata.status || 'pending'}`}>
          {item.metadata.status || 'Pending'}
        </span>
        {item.metadata.dueDate && (
          <span className="task-item-due-date">
            📅 {formatDate(item.metadata.dueDate)}
          </span>
        )}
        {item.metadata.priority && (
          <span className={`task-item-priority ${getPriorityColor(item.metadata.priority)}`}>
            {item.metadata.priority}
          </span>
        )}
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="task-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="task-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskItem;
