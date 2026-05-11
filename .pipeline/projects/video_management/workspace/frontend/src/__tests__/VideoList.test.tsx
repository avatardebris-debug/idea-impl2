import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import VideoList from '../components/VideoList';
import * as apiModule from '../api';

// Mock the api module
vi.mock('../api', () => ({
  api: {
    videos: {
      list: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

const mockVideos = [
  {
    id: '1',
    table_id: '1',
    title: 'Test Video 1',
    description: 'Description 1',
    status: 'draft' as const,
    tags: ['test', 'video'],
    publish_date: null,
    thumbnail_url: null,
    youtube_video_id: null,
    custom_fields: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    table_id: '1',
    title: 'Test Video 2',
    description: 'Description 2',
    status: 'published' as const,
    tags: ['published'],
    publish_date: '2024-01-15T00:00:00Z',
    thumbnail_url: 'https://example.com/thumb.jpg',
    youtube_video_id: 'abc123',
    custom_fields: {},
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

describe('VideoList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiModule.api.videos.list as any).mockResolvedValue({
      items: mockVideos,
      total: 2,
      page: 1,
      page_size: 10,
    });
  });

  const renderComponent = () => {
    render(
      <MemoryRouter>
        <VideoList tableId="1" />
      </MemoryRouter>
    );
  };

  it('should render the component', () => {
    renderComponent();
    expect(screen.getByText('Videos')).toBeInTheDocument();
  });

  it('should display videos', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
      expect(screen.getByText('Test Video 2')).toBeInTheDocument();
    });
  });

  it('should display status badges', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('draft')).toBeInTheDocument();
      expect(screen.getByText('published')).toBeInTheDocument();
    });
  });

  it('should display tags', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('#test')).toBeInTheDocument();
      expect(screen.getByText('#video')).toBeInTheDocument();
    });
  });

  it('should show loading state initially', () => {
    (apiModule.api.videos.list as any).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    });
    renderComponent();
    expect(screen.getByText('Loading videos...')).toBeInTheDocument();
  });

  it('should show error state on API failure', async () => {
    (apiModule.api.videos.list as any).mockRejectedValueOnce(new Error('API Error'));
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should navigate to create video page', () => {
    renderComponent();
    const addButton = screen.getByText('+ Add Video');
    fireEvent.click(addButton);
    expect(mockNavigate).toHaveBeenCalledWith('/videos/new');
  });

  it('should navigate to edit video page', async () => {
    renderComponent();
    await waitFor(() => {
      const editButton = screen.getAllByText('Edit')[0];
      fireEvent.click(editButton);
      expect(mockNavigate).toHaveBeenCalledWith('/videos/1/edit');
    });
  });

  it('should delete a video', async () => {
    (apiModule.api.videos.delete as any).mockResolvedValueOnce(undefined);
    renderComponent();
    await waitFor(() => {
      const deleteButton = screen.getAllByText('Delete')[0];
      // Mock confirm
      window.confirm = vi.fn(() => true);
      fireEvent.click(deleteButton);
    });
    expect(apiModule.api.videos.delete).toHaveBeenCalledWith('1');
  });

  it('should show empty state when no videos', async () => {
    (apiModule.api.videos.list as any).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    });
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('No videos found.')).toBeInTheDocument();
    });
  });

  it('should render search bar', () => {
    renderComponent();
    expect(screen.getByPlaceholderText('Search videos...')).toBeInTheDocument();
  });

  it('should render status filter', () => {
    renderComponent();
    expect(screen.getByLabelText('')).toBeInTheDocument();
  });

  it('should render pagination', async () => {
    (apiModule.api.videos.list as any).mockResolvedValueOnce({
      items: mockVideos,
      total: 20,
      page: 1,
      page_size: 10,
    });
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/Page 1 of/)).toBeInTheDocument();
    });
  });
});
