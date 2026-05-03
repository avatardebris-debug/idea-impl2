import React from 'react';
import { DropZoneState } from '../../types/memoryPalace';

interface DroppableLocationProps {
  location: string;
  room: string;
  children: React.ReactNode;
  dropZoneState: DropZoneState;
  onDragEnter: (location: string, room: string) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent, location: string, room: string) => void;
  onDragOver?: (e: React.DragEvent) => void;
  onDragEnd?: () => void;
}

export const DroppableLocation: React.FC<DroppableLocationProps> = ({
  location,
  room,
  children,
  dropZoneState,
  onDragEnter,
  onDragLeave,
  onDrop,
  onDragOver,
  onDragEnd,
}) => {
  const isTarget = dropZoneState.targetLocation === location && dropZoneState.targetRoom === room;
  const isOver = dropZoneState.isOver && isTarget;

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    onDragEnter(location, room);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    onDragLeave();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    onDrop(e, location, room);
  };

  const handleDragOver = (e: React.DragEvent) => {
    if (onDragOver) {
      onDragOver(e);
    }
  };

  const handleDragEnd = () => {
    if (onDragEnd) {
      onDragEnd();
    }
  };

  return (
    <div
      className={`droppable-location ${isOver ? 'drop-target' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      role="region"
      aria-label={`Drop zone for ${location}, room ${room}`}
      aria-dropzone={isOver ? 'true' : 'false'}
    >
      {children}
    </div>
  );
};

export default DroppableLocation;
