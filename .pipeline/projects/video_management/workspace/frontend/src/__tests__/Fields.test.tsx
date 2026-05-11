import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Fields from '../components/Fields';
import * as apiModule from '../api';

// Mock the api module
vi.mock('../api', () => ({
  api: {
    tables: {
      list: vi.fn(),
    },
    fields: {
      list: vi.fn(),
      create: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

const mockTables = [
  {
    id: '1',
    name: 'Videos',
    description: 'Video content',
    is_deleted: false,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Articles',
    description: 'Article content',
    is_deleted: false,
    created_at: '2024-01-02T00:00:00Z',
  },
];

const mockFields = [
  {
    id: '1',
    name: 'title',
    field_type: 'text',
    options: [],
    is_required: true,
    is_deleted: false,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'description',
    field_type: 'text',
    options: [],
    is_required: false,
    is_deleted: false,
    created_at: '2024-01-02T00:00:00Z',
  },
];

describe('Fields Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiModule.api.tables.list as any).mockResolvedValueOnce(mockTables);
    (apiModule.api.fields.list as any).mockResolvedValueOnce(mockFields);
  });

  const renderComponent = () => {
    render(
      <MemoryRouter>
        <Fields tableId="1" />
      </MemoryRouter>
    );
  };

  it('should render the component', () => {
    renderComponent();
    expect(screen.getByText('Fields')).toBeInTheDocument();
  });

  it('should render table selector', () => {
    renderComponent();
    expect(screen.getByLabelText('Select table')).toBeInTheDocument();
  });

  it('should populate table selector', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Videos')).toBeInTheDocument();
      expect(screen.getByText('Articles')).toBeInTheDocument();
    });
  });

  it('should display fields', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('title')).toBeInTheDocument();
      expect(screen.getByText('description')).toBeInTheDocument();
    });
  });

  it('should display field types', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('TEXT')).toBeInTheDocument();
    });
  });

  it('should display required indicator', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Required')).toBeInTheDocument();
    });
  });

  it('should show loading state', () => {
    (apiModule.api.tables.list as any).mockResolvedValueOnce([]);
    (apiModule.api.fields.list as any).mockResolvedValueOnce([]);
    renderComponent();
    expect(screen.getByText('Loading fields...')).toBeInTheDocument();
  });

  it('should show error state on API failure', async () => {
    (apiModule.api.tables.list as any).mockRejectedValueOnce(new Error('API Error'));
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should create a field', async () => {
    (apiModule.api.fields.create as any).mockResolvedValueOnce({
      id: '3',
      name: 'new_field',
      field_type: 'text',
      options: [],
      is_required: false,
      is_deleted: false,
      created_at: '2024-01-03T00:00:00Z',
    });
    renderComponent();
    
    await waitFor(() => {
      const nameInput = screen.getByLabelText('Field name');
      fireEvent.change(nameInput, { target: { value: 'new_field' } });
      
      const typeSelect = screen.getByLabelText('Field type');
      fireEvent.change(typeSelect, { target: { value: 'TEXT' } });
      
      fireEvent.click(screen.getByText('Add Field'));
    });
    
    await waitFor(() => {
      expect(apiModule.api.fields.create).toHaveBeenCalledWith('1', expect.objectContaining({
        name: 'new_field',
        field_type: 'TEXT',
      }));
    });
  });

  it('should delete a field', async () => {
    (apiModule.api.fields.delete as any).mockResolvedValueOnce(undefined);
    renderComponent();
    
    await waitFor(() => {
      const deleteButton = screen.getAllByText('Delete')[0];
      window.confirm = vi.fn(() => true);
      fireEvent.click(deleteButton);
    });
    
    expect(apiModule.api.fields.delete).toHaveBeenCalledWith('1');
  });

  it('should switch tables', async () => {
    const mockFields2 = [
      {
        id: '3',
        name: 'content',
        field_type: 'text',
        options: [],
        is_required: true,
        is_deleted: false,
        created_at: '2024-01-03T00:00:00Z',
      },
    ];
    (apiModule.api.fields.list as any).mockResolvedValueOnce(mockFields);
    (apiModule.api.fields.list as any).mockResolvedValueOnce(mockFields2);
    
    renderComponent();
    
    await waitFor(() => {
      const tableSelect = screen.getByLabelText('Select table');
      fireEvent.change(tableSelect, { target: { value: '2' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('content')).toBeInTheDocument();
    });
  });

  it('should show empty state when no fields', async () => {
    (apiModule.api.fields.list as any).mockResolvedValueOnce([]);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('No fields found.')).toBeInTheDocument();
    });
  });

  it('should validate field name', async () => {
    renderComponent();
    
    await waitFor(() => {
      const nameInput = screen.getByLabelText('Field name');
      fireEvent.change(nameInput, { target: { value: '' } });
      
      fireEvent.click(screen.getByText('Add Field'));
    });
    
    await waitFor(() => {
      expect(screen.getByText('Field name is required')).toBeInTheDocument();
    });
  });
});
