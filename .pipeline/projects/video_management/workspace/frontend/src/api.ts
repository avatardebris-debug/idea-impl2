/**
 * API client for the Video Management Platform.
 * Provides typed methods for interacting with the backend.
 */

export interface Video {
  id: string;
  table_id: string;
  title: string;
  description: string;
  status: 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed';
  tags: string[];
  publish_date: string | null;
  thumbnail_url: string | null;
  youtube_video_id: string | null;
  custom_fields: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface VideoCreate {
  title: string;
  description?: string;
  status?: 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed';
  tags?: string[];
  publish_date?: string;
  thumbnail_url?: string;
  youtube_video_id?: string;
  custom_fields?: Record<string, any>;
}

export interface VideoUpdate {
  title?: string;
  description?: string;
  status?: 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed';
  tags?: string[];
  publish_date?: string;
  thumbnail_url?: string;
  youtube_video_id?: string;
  custom_fields?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Field {
  id: string;
  name: string;
  field_type: 'text' | 'number' | 'select' | 'tags' | 'date' | 'url' | 'boolean' | 'json';
  options?: string[];
  is_required: boolean;
  is_deleted: boolean;
  created_at: string;
}

export interface FieldCreate {
  name: string;
  field_type: 'text' | 'number' | 'select' | 'tags' | 'date' | 'url' | 'boolean' | 'json';
  options?: string[];
  is_required?: boolean;
}

export interface Table {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface TableResponse extends Table {}

const API_BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  if (response.status === 204) return null as unknown as T;
  return response.json();
}

export const api = {
  videos: {
    list: (params?: {
      page?: number;
      page_size?: number;
      status?: string;
      search?: string;
    }): Promise<PaginatedResponse<Video>> => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', String(params.page));
      if (params?.page_size) searchParams.set('page_size', String(params.page_size));
      if (params?.status) searchParams.set('status', params.status);
      if (params?.search) searchParams.set('search', params.search);
      const queryString = searchParams.toString();
      return request(`/videos${queryString ? `?${queryString}` : ''}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    },

    get: (id: string): Promise<Video> =>
      request(`/videos/${id}`),

    create: (data: VideoCreate): Promise<Video> =>
      request('/videos', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: string, data: VideoUpdate): Promise<Video> =>
      request(`/videos/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (id: string): Promise<void> =>
      request(`/videos/${id}`, {
        method: 'DELETE',
      }),
  },

  fields: {
    list: (tableId: string): Promise<Field[]> =>
      request(`/tables/${tableId}/fields`),

    create: (tableId: string, data: FieldCreate): Promise<Field> =>
      request(`/tables/${tableId}/fields`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    delete: (fieldId: string): Promise<void> =>
      request(`/tables/fields/${fieldId}`, {
        method: 'DELETE',
      }),
  },

  tables: {
    list: (): Promise<Table[]> =>
      request('/tables'),

    get: (id: string): Promise<Table> =>
      request(`/tables/${id}`),
  },
};
