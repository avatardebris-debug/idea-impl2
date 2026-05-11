'use client';

import React, { useState } from 'react';
import { Source } from '../lib/api';

interface SourceListProps {
  sources: Source[];
  onAdd: (source: Omit<Source, 'id' | 'metadata_completeness' | 'source_type'>) => void;
  onRemove: (sourceId: string) => void;
}

export default function SourceList({ sources, onAdd, onRemove }: SourceListProps) {
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [authorsStr, setAuthorsStr] = useState('');
  const [year, setYear] = useState('');
  const [abstract, setAbstract] = useState('');
  const [url, setUrl] = useState('');

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const authors = authorsStr
      ? authorsStr.split(',').map((a) => a.trim()).filter(Boolean)
      : [];

    onAdd({
      title: title.trim(),
      authors,
      year: year ? parseInt(year, 10) : undefined,
      abstract: abstract || '',
      url: url || undefined,
    });

    // Reset form
    setTitle('');
    setAuthorsStr('');
    setYear('');
    setAbstract('');
    setUrl('');
    setShowForm(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ fontWeight: 600 }}>
          Sources ({sources.length})
        </h3>
        <button
          className="btn btn-secondary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Add Source'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            <input
              className="input"
              placeholder="Title *"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <input
              className="input"
              placeholder="Authors (comma-separated)"
              value={authorsStr}
              onChange={(e) => setAuthorsStr(e.target.value)}
            />
            <input
              className="input"
              type="number"
              placeholder="Year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
            <textarea
              className="input"
              placeholder="Abstract"
              rows={3}
              value={abstract}
              onChange={(e) => setAbstract(e.target.value)}
            />
            <input
              className="input"
              placeholder="URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <button type="submit" className="btn btn-primary">
              Add Source
            </button>
          </div>
        </form>
      )}

      {sources.length === 0 && !showForm && (
        <p style={{ color: '#888', fontStyle: 'italic' }}>
          No sources added yet. Click "+ Add Source" to begin.
        </p>
      )}

      <div className="card" style={{ padding: 0 }}>
        {sources.map((src) => (
          <div key={src.id} className="source-item">
            <div className="source-info">
              <div className="source-title">{src.title}</div>
              <div className="source-meta">
                {src.authors.length > 0 && <span>{src.authors.join(', ')}</span>}
                {src.year && <span> · {src.year}</span>}
                {src.url && <span> · <a href={src.url} target="_blank" rel="noopener noreferrer">{src.url}</a></span>}
              </div>
            </div>
            <button
              className="btn btn-danger"
              style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
              onClick={() => onRemove(src.id)}
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
