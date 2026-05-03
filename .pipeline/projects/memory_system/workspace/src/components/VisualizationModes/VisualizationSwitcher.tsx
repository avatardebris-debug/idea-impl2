import React from 'react';
import { VisualizationMode } from '../../types/memoryPalace';

interface VisualizationSwitcherProps {
  currentMode: VisualizationMode;
  onModeChange: (mode: VisualizationMode) => void;
}

const modeConfig: Record<VisualizationMode, { label: string; icon: string; description: string }> = {
  grid: { label: 'Grid', icon: '📊', description: 'Grid layout view' },
  timeline: { label: 'Timeline', icon: '📈', description: 'Chronological timeline' },
  map: { label: 'Map', icon: '🗺️', description: 'Geographic visualization' },
  network: { label: 'Network', icon: '🕸️', description: 'Relationship graph' },
};

export const VisualizationSwitcher: React.FC<VisualizationSwitcherProps> = ({
  currentMode,
  onModeChange,
}) => {
  const handleModeClick = (mode: VisualizationMode) => {
    onModeChange(mode);
  };

  return (
    <div className="visualization-switcher" role="tablist" aria-label="Visualization modes">
      {Object.entries(modeConfig).map(([mode, config]) => {
        const isActive = currentMode === mode;
        return (
          <button
            key={mode}
            onClick={() => handleModeClick(mode as VisualizationMode)}
            role="tab"
            aria-selected={isActive}
            aria-controls={`visualization-${mode}`}
            className={`visualization-switcher-button ${isActive ? 'active' : ''}`}
            title={config.description}
          >
            <span className="visualization-switcher-icon" aria-hidden="true">
              {config.icon}
            </span>
            <span className="visualization-switcher-label">{config.label}</span>
            {isActive && (
              <span className="visualization-switcher-indicator" aria-hidden="true"></span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default VisualizationSwitcher;
