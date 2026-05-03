import React from 'react';
import { MemoryPalaceItemUnion } from '../../types/memoryPalace';
import { WordItem } from '../CustomDataTypes/WordItem';
import { PhraseItem } from '../CustomDataTypes/PhraseItem';
import { ImageItem } from '../CustomDataTypes/ImageItem';
import { DateItem } from '../CustomDataTypes/DateItem';
import { CardItem } from '../CustomDataTypes/CardItem';
import { NumberItem } from '../CustomDataTypes/NumberItem';

interface DraggableItemProps {
  item: MemoryPalaceItemUnion;
  isSelected?: boolean;
  onDragStart?: (e: React.DragEvent, item: MemoryPalaceItemUnion) => void;
  onDragEnd?: () => void;
  onClick?: (item: MemoryPalaceItemUnion) => void;
}

export const DraggableItem: React.FC<DraggableItemProps> = ({
  item,
  isSelected = false,
  onDragStart,
  onDragEnd,
  onClick,
}) => {
  const handleDragStart = (e: React.DragEvent) => {
    if (onDragStart) {
      onDragStart(e, item);
    }
  };

  const handleDragEnd = () => {
    if (onDragEnd) {
      onDragEnd();
    }
  };

  const handleClick = () => {
    if (onClick) {
      onClick(item);
    }
  };

  const renderContent = () => {
    switch (item.type) {
      case 'word':
        return <WordItem item={item as WordItem} />;
      case 'phrase':
        return <PhraseItem item={item as PhraseItem} />;
      case 'image':
        return <ImageItem item={item as ImageItem} />;
      case 'date':
        return <DateItem item={item as DateItem} />;
      case 'card':
        return <CardItem item={item as CardItem} />;
      case 'number':
        return <NumberItem item={item as NumberItem} />;
      default:
        return <div className="draggable-item-content">{item.value}</div>;
    }
  };

  return (
    <div
      className={`draggable-item ${isSelected ? 'selected' : ''}`}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`${item.type} item: ${item.value}`}
    >
      {renderContent()}
    </div>
  );
};

export default DraggableItem;
