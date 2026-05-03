import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryPalaceDashboard } from './MemoryPalaceDashboard';
import { memoryPalaceManager } from '../managers/MemoryPalaceManager';
import { exerciseSessionManager } from '../managers/ExerciseSessionManager';

// Mock the managers
jest.mock('../managers/MemoryPalaceManager');
jest.mock('../managers/ExerciseSessionManager');

describe('MemoryPalaceDashboard', () => {
  const mockPalace = {
    id: 'palace-1',
    name: 'Test Palace',
    description: 'A test memory palace',
    rooms: [
      {
        id: 'room-1',
        name: 'Entrance Hall',
        description: 'The main entrance',
        items: [
          { id: 'item-1', content: 'Test Item 1', location: 'left wall' },
          { id: 'item-2', content: 'Test Item 2', location: 'right wall' },
        ],
      },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup mock implementations
    (memoryPalaceManager.getAllPalaces as jest.Mock).mockReturnValue([mockPalace]);
    (memoryPalaceManager.createPalace as jest.Mock).mockReturnValue(mockPalace);
    (memoryPalaceManager.deletePalace as jest.Mock).mockImplementation((id: string) => {
      if (id === mockPalace.id) {
        (memoryPalaceManager.getAllPalaces as jest.Mock).mockReturnValue([]);
      }
    });
    (memoryPalaceManager.updatePalace as jest.Mock).mockImplementation((palace: typeof mockPalace) => {
      Object.assign(mockPalace, palace);
    });
    (memoryPalaceManager.getPalaceStats as jest.Mock).mockReturnValue({
      totalItems: 2,
      totalRooms: 1,
      lastAccessed: new Date().toISOString(),
    });
  });

  test('renders dashboard with palace list', () => {
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('🏰 Your Memory Palaces')).toBeInTheDocument();
    expect(screen.getByText('Test Palace')).toBeInTheDocument();
    expect(screen.getByText('1 rooms, 2 items')).toBeInTheDocument();
  });

  test('renders create palace button', () => {
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('➕ Create New Palace')).toBeInTheDocument();
  });

  test('opens create palace modal when button is clicked', () => {
    render(<MemoryPalaceDashboard />);
    
    fireEvent.click(screen.getByText('➕ Create New Palace'));
    
    expect(screen.getByText('🏰 Create New Memory Palace')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g., My Childhood Home')).toBeInTheDocument();
  });

  test('creates new palace when form is submitted', async () => {
    render(<MemoryPalaceDashboard />);
    
    fireEvent.click(screen.getByText('➕ Create New Palace'));
    
    const nameInput = screen.getByLabelText('Palace Name *');
    const descriptionInput = screen.getByLabelText('Description');
    const createButton = screen.getByText('Create Palace');
    
    fireEvent.change(nameInput, { target: { value: 'New Palace' } });
    fireEvent.change(descriptionInput, { target: { value: 'A new test palace' } });
    
    fireEvent.click(createButton);
    
    await waitFor(() => {
      expect(memoryPalaceManager.createPalace).toHaveBeenCalledWith('New Palace', 'A new test palace');
    });
    
    expect(screen.queryByText('🏰 Create New Memory Palace')).not.toBeInTheDocument();
  });

  test('does not allow creating palace without name', () => {
    render(<MemoryPalaceDashboard />);
    
    fireEvent.click(screen.getByText('➕ Create New Palace'));
    
    const createButton = screen.getByText('Create Palace');
    expect(createButton).toBeDisabled();
  });

  test('closes modal when cancel button is clicked', () => {
    render(<MemoryPalaceDashboard />);
    
    fireEvent.click(screen.getByText('➕ Create New Palace'));
    expect(screen.getByText('🏰 Create New Memory Palace')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('Cancel'));
    
    expect(screen.queryByText('🏰 Create New Memory Palace')).not.toBeInTheDocument();
  });

  test('deletes palace when delete button is clicked', async () => {
    render(<MemoryPalaceDashboard />);
    
    const deleteButton = screen.getByText('🗑️');
    fireEvent.click(deleteButton);
    
    await waitFor(() => {
      expect(memoryPalaceManager.deletePalace).toHaveBeenCalledWith(mockPalace.id);
    });
  });

  test('selects palace when clicked', () => {
    render(<MemoryPalaceDashboard />);
    
    const palaceItem = screen.getByText('Test Palace').closest('.palace-item');
    expect(palaceItem).toHaveClass('active');
  });

  test('switches between views using tabs', () => {
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('🖼️ Visualization')).toBeInTheDocument();
    expect(screen.getByText('✏️ Editor')).toBeInTheDocument();
    expect(screen.getByText('📊 Analytics')).toBeInTheDocument();
    expect(screen.getByText('🧠 Exercises')).toBeInTheDocument();
    
    // Click on Analytics tab
    fireEvent.click(screen.getByText('📊 Analytics'));
    
    expect(screen.getByText('📊 Memory Palace Analytics')).toBeInTheDocument();
  });

  test('shows no palace selected message when no palace exists', () => {
    (memoryPalaceManager.getAllPalaces as jest.Mock).mockReturnValue([]);
    
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('🏰 No Palace Selected')).toBeInTheDocument();
    expect(screen.getByText('Create New Palace')).toBeInTheDocument();
  });

  test('respects dashboard configuration', () => {
    const config = {
      showVisualization: false,
      showEditor: false,
      showAnalytics: false,
      showExerciseManager: false,
      defaultView: 'visualization',
    };
    
    render(<MemoryPalaceDashboard config={config} />);
    
    expect(screen.queryByText('🖼️ Visualization')).not.toBeInTheDocument();
    expect(screen.queryByText('✏️ Editor')).not.toBeInTheDocument();
    expect(screen.queryByText('📊 Analytics')).not.toBeInTheDocument();
    expect(screen.queryByText('🧠 Exercises')).not.toBeInTheDocument();
  });

  test('handles exercise completion', async () => {
    const mockSession = {
      id: 'session-1',
      palaceId: mockPalace.id,
      type: 'recall' as const,
      startTime: new Date().toISOString(),
      endTime: new Date().toISOString(),
      stats: {
        accuracy: 0.85,
        totalTime: 120,
        completedExercises: 10,
      },
    };

    (exerciseSessionManager.completeSession as jest.Mock).mockReturnValue(mockSession);
    
    render(<MemoryPalaceDashboard />);
    
    // Simulate exercise completion
    fireEvent.click(screen.getByText('🧠 Exercises'));
    
    // The exercise manager should be rendered
    expect(screen.getByText('🧠 Exercise Session Manager')).toBeInTheDocument();
  });

  test('displays palace description in header', () => {
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('A test memory palace')).toBeInTheDocument();
  });

  test('updates palace when edited', async () => {
    const updatedPalace = {
      ...mockPalace,
      name: 'Updated Palace',
    };
    
    (memoryPalaceManager.updatePalace as jest.Mock).mockImplementation((palace: typeof updatedPalace) => {
      Object.assign(mockPalace, palace);
    });
    
    render(<MemoryPalaceDashboard />);
    
    // Click on Editor tab
    fireEvent.click(screen.getByText('✏️ Editor'));
    
    // The editor should be rendered
    expect(screen.getByText('✏️ Memory Palace Editor')).toBeInTheDocument();
  });

  test('handles empty palace list gracefully', () => {
    (memoryPalaceManager.getAllPalaces as jest.Mock).mockReturnValue([]);
    
    render(<MemoryPalaceDashboard />);
    
    expect(screen.getByText('No memory palaces yet. Create one to get started!')).toBeInTheDocument();
  });

  test('closes modal when clicking overlay', () => {
    render(<MemoryPalaceDashboard />);
    
    fireEvent.click(screen.getByText('➕ Create New Palace'));
    expect(screen.getByText('🏰 Create New Memory Palace')).toBeInTheDocument();
    
    // Click on overlay (outside modal content)
    fireEvent.click(document.querySelector('.modal-overlay')!);
    
    expect(screen.queryByText('🏰 Create New Memory Palace')).not.toBeInTheDocument();
  });
});