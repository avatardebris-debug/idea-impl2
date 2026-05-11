import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import VideoForm from '../components/VideoForm';
import * as apiModule from '../api';

// Mock the api module
vi.mock('../api', () => ({
  api: {
    videos: {
      create: vi.fn(),
      update: vi.fn(),
      get: vi.fn(),
    },
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '1' }),
}));

const mockVideo = {
  id: '1',
  table_id: '1',
  title: 'Test Video',
  description: 'Test Description',
  status: 'draft' as const,
  tags: ['test'],
  publish_date: null,
  thumbnail_url: null,
  youtube_video_id: null,
  custom_fields: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('VideoForm Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = (isEditing = false) => {
    if (isEditing) {
      (apiModule.api.videos.get as any).mockResolvedValueOnce(mockVideo);
    }
    render(
      <MemoryRouter>
        <VideoForm tableId="1" isEditing={isEditing} />
      </MemoryRouter>
    );
  };

  it('should render the form', () => {
    renderComponent();
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
  });

  it('should render create form when not editing', () => {
    renderComponent(false);
    expect(screen.getByText('Create Video')).toBeInTheDocument();
  });

  it('should render edit form when editing', () => {
    renderComponent(true);
    expect(screen.getByText('Update Video')).toBeInTheDocument();
  });

  it('should pre-fill form when editing', async () => {
    renderComponent(true);
    await waitFor(() => {
      expect(screen.getByLabelText('Title').value).toBe('Test Video');
      expect(screen.getByLabelText('Description').value).toBe('Test Description');
    });
  });

  it('should create a video', async () => {
    (apiModule.api.videos.create as any).mockResolvedValueOnce(mockVideo);
    renderComponent(false);
    
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'New Video' } });
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'New Description' } });
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'published' } });
    
    fireEvent.click(screen.getByText('Create Video'));
    
    await waitFor(() => {
      expect(apiModule.api.videos.create).toHaveBeenCalledWith('1', expect.objectContaining({
        title: 'New Video',
        description: 'New Description',
        status: 'published',
      }));
    });
  });

  it('should update a video', async () => {
    (apiModule.api.videos.update as any).mockResolvedValueOnce(mockVideo);
    renderComponent(true);
    
    await waitFor(() => {
      fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Updated Video' } });
      fireEvent.click(screen.getByText('Update Video'));
    });
    
    await waitFor(() => {
      expect(apiModule.api.videos.update).toHaveBeenCalledWith('1', expect.objectContaining({
        title: 'Updated Video',
      }));
    });
  });

  it('should show validation error for empty title', async () => {
    renderComponent(false);
    
    fireEvent.click(screen.getByText('Create Video'));
    
    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });
  });

  it('should handle API error', async () => {
    (apiModule.api.videos.create as any).mockRejectedValueOnce(new Error('API Error'));
    renderComponent(false);
    
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'New Video' } });
    fireEvent.click(screen.getByText('Create Video'));
    
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should cancel and navigate back', () => {
    renderComponent();
    fireEvent.click(screen.getByText('Cancel'));
    expect(mockNavigate).toHaveBeenCalledWith('/videos');
  });

  it('should handle custom fields JSON', async () => {
    renderComponent(false);
    
    const customFieldsInput = screen.getByLabelText('Custom Fields (JSON)');
    fireEvent.change(customFieldsInput, { target: { value: '{"key": "value"}' } });
    
    expect(customFieldsInput.value).toBe('{"key": "value"}');
  });

  it('should disable submit button while loading', async () => {
    (apiModule.api.videos.create as any).mockReturnValueOnce(new Promise(() => {}));
    renderComponent(false);
    
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'New Video' } });
    fireEvent.click(screen.getByText('Create Video'));
    
    await waitFor(() => {
      expect(screen.getByText('Creating...')).toBeInTheDocument();
    });
  });
});
