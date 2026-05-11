import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, type Video, type VideoCreate, type PaginatedResponse, type Field, type FieldCreate, type Table } from './api';

// Mock fetch
global.fetch = vi.fn();

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('videos.list', () => {
    it('should fetch videos with default parameters', async () => {
      const mockResponse: PaginatedResponse<Video> = {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await api.videos.list();

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/videos',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should fetch videos with search parameter', async () => {
      const mockResponse: PaginatedResponse<Video> = {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await api.videos.list({ search: 'test' });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/videos',
        expect.any(Object)
      );
    });

    it('should fetch videos with status filter', async () => {
      const mockResponse: PaginatedResponse<Video> = {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      await api.videos.list({ status: 'published' });

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('videos.get', () => {
    it('should fetch a single video', async () => {
      const mockVideo: Video = {
        id: '1',
        table_id: '1',
        title: 'Test Video',
        description: 'Test Description',
        status: 'published',
        tags: ['test'],
        publish_date: null,
        thumbnail_url: null,
        youtube_video_id: 'abc123',
        custom_fields: {},
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockVideo),
      });

      const result = await api.videos.get('1');

      expect(result).toEqual(mockVideo);
      expect(global.fetch).toHaveBeenCalledWith('/api/videos/1', expect.any(Object));
    });

    it('should throw error on API failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Video not found' }),
      });

      await expect(api.videos.get('999')).rejects.toThrow('Video not found');
    });
  });

  describe('videos.create', () => {
    it('should create a video', async () => {
      const mockVideo: Video = {
        id: '1',
        table_id: '1',
        title: 'New Video',
        description: 'New Description',
        status: 'draft',
        tags: [],
        publish_date: null,
        thumbnail_url: null,
        youtube_video_id: null,
        custom_fields: {},
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockVideo),
      });

      const data: VideoCreate = {
        title: 'New Video',
        description: 'New Description',
        status: 'draft',
        tags: [],
      };

      const result = await api.videos.create(data);

      expect(result).toEqual(mockVideo);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/videos',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        })
      );
    });
  });

  describe('videos.update', () => {
    it('should update a video', async () => {
      const mockVideo: Video = {
        id: '1',
        table_id: '1',
        title: 'Updated Video',
        description: 'Updated Description',
        status: 'published',
        tags: ['updated'],
        publish_date: null,
        thumbnail_url: null,
        youtube_video_id: null,
        custom_fields: {},
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockVideo),
      });

      const data: VideoCreate = {
        title: 'Updated Video',
        description: 'Updated Description',
        status: 'published',
        tags: ['updated'],
      };

      const result = await api.videos.update('1', data);

      expect(result).toEqual(mockVideo);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/videos/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(data),
        })
      );
    });
  });

  describe('videos.delete', () => {
    it('should delete a video', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      await api.videos.delete('1');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/videos/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('fields.list', () => {
    it('should fetch fields for a table', async () => {
      const mockFields: Field[] = [
        {
          id: '1',
          name: 'title',
          field_type: 'text',
          options: [],
          is_required: true,
          is_deleted: false,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockFields),
      });

      const result = await api.fields.list('1');

      expect(result).toEqual(mockFields);
      expect(global.fetch).toHaveBeenCalledWith('/api/tables/1/fields', expect.any(Object));
    });
  });

  describe('fields.create', () => {
    it('should create a field', async () => {
      const mockField: Field = {
        id: '1',
        name: 'new_field',
        field_type: 'text',
        options: [],
        is_required: false,
        is_deleted: false,
        created_at: '2024-01-01T00:00:00Z',
      };
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockField),
      });

      const data: FieldCreate = {
        name: 'new_field',
        field_type: 'TEXT',
        is_required: false,
      };

      const result = await api.fields.create('1', data);

      expect(result).toEqual(mockField);
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/tables/1/fields',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        })
      );
    });
  });

  describe('fields.delete', () => {
    it('should delete a field', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      await api.fields.delete('1');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/fields/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('tables.list', () => {
    it('should fetch tables', async () => {
      const mockTables: Table[] = [
        {
          id: '1',
          name: 'Videos',
          description: 'Video content',
          is_deleted: false,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTables),
      });

      const result = await api.tables.list();

      expect(result).toEqual(mockTables);
      expect(global.fetch).toHaveBeenCalledWith('/api/tables', expect.any(Object));
    });
  });
});
