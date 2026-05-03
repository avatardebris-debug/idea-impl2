# Phase 4 Tasks

- [x] Task 1: Create extended data type definitions
  - What: Define TypeScript interfaces for new data types (words, phrases, images, dates) and extend existing types
  - Files: src/types/memoryPalace.ts (extend), src/types/index.ts (create new exports)
  - Done when: All data types have proper TypeScript interfaces with id, type, value, metadata fields; types are exported and can be used across the app

- [x] Task 2: Implement custom data type components
  - What: Create reusable React components for displaying words, phrases, images, and dates in the memory palace visualization
  - Files: src/components/CustomDataTypes/WordItem.tsx, src/components/CustomDataTypes/PhraseItem.tsx, src/components/CustomDataTypes/ImageItem.tsx, src/components/CustomDataTypes/DateItem.tsx, src/components/CustomDataTypes/index.ts
  - Done when: Each component renders appropriately for its data type; components accept standard props (item, onClick, isSelected); components are properly styled and accessible

- [x] Task 3: Create visualization mode switcher component
  - What: Build a component that allows users to switch between different visualization modes (grid, timeline, map, network graph)
  - Files: src/components/VisualizationModes/VisualizationSwitcher.tsx, src/components/VisualizationModes/VisualizationSwitcher.css
  - Done when: Switcher displays all available modes with icons; clicking a mode updates the active visualization; UI shows current mode selection clearly

- [x] Task 4: Implement timeline visualization mode
  - What: Create a timeline-based visualization that displays items chronologically based on their date metadata
  - Files: src/components/VisualizationModes/TimelineVisualization.tsx, src/components/VisualizationModes/TimelineVisualization.css
  - Done when: Items are arranged horizontally/vertically by date; date labels are visible; items can be clicked to show details; timeline scales appropriately for different date ranges

- [x] Task 5: Implement map visualization mode
  - What: Create a geographic/map-based visualization that displays items with location data
  - Files: src/components/VisualizationModes/MapVisualization.tsx, src/components/VisualizationModes/MapVisualization.css
  - Done when: Items with location data appear on a map interface; items can be clustered by proximity; clicking items shows details; fallback to grid view when no location data exists

- [x] Task 6: Implement network graph visualization mode
  - What: Create a node-link visualization that shows relationships between memory items
  - Files: src/components/VisualizationModes/NetworkGraphVisualization.tsx, src/components/VisualizationModes/NetworkGraphVisualization.css, src/utils/visualizationUtils.ts (add graph layout functions)
  - Done when: Items are displayed as nodes with connections showing relationships; graph is interactive (pan/zoom); nodes can be dragged; relationships are visually distinct

- [x] Task 7: Implement drag-and-drop item management
  - What: Add drag-and-drop functionality for reordering and moving items between locations/rooms
  - Files: src/hooks/useDragAndDrop.ts, src/components/MemoryPalace/DraggableItem.tsx, src/components/MemoryPalace/DroppableLocation.tsx
  - Done when: Items can be dragged and dropped onto locations; visual feedback during drag (highlight drop zones); items can be moved between rooms; keyboard accessibility for drag operations

- [x] Task 8: Create data type input forms
  - What: Build forms for users to add words, phrases, images, and dates to their memory palace
  - Files: src/components/DataInput/WordInput.tsx, src/components/DataInput/PhraseInput.tsx, src/components/DataInput/ImageInput.tsx, src/components/DataInput/DateInput.tsx, src/components/DataInput/DataInputForm.tsx, src/components/DataInput/index.ts
  - Done when: Each form validates input appropriately; forms can be submitted to add items to the palace; image input supports URL and file upload; date input uses proper date picker


<!-- 4 tasks removed by guardrail (max 8 per phase) -->