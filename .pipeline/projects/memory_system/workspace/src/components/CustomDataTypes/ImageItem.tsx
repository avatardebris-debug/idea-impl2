import React from 'react';
import { ImageItem } from '../../types/memoryPalace';

interface ImageItemProps {
  item: ImageItem;
  onClick?: (item: ImageItem) => void;
  isSelected?: boolean;
}

export const ImageItem: React.FC<ImageItemProps> = ({ item, onClick, isSelected }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  const isUrl = item.value.startsWith('http://') || item.value.startsWith('https://');

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
      className={`image-item ${isSelected ? 'selected' : ''}`}
      aria-label={`Image: ${item.metadata.altText || 'Image item'}`}
      aria-selected={isSelected}
    >
      <div className="image-item-content">
        {isUrl ? (
          <img
            src={item.value}
            alt={item.metadata.altText || 'Memory item image'}
            className="image-item-display"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="image-item-placeholder">
            <span className="image-item-icon">🖼️</span>
            <span className="image-item-label">Image</span>
          </div>
        )}
        {item.metadata.altText && (
          <span className="image-item-alt" title={item.metadata.altText}>
            {item.metadata.altText}
          </span>
        )}
      </div>
      {item.metadata.tags && item.metadata.tags.length > 0 && (
        <div className="image-item-tags">
          {item.metadata.tags.map((tag, index) => (
            <span key={index} className="image-item-tag">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default ImageItem;
