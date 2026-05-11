'use client';

import React from 'react';

interface DraftPreviewProps {
  content: string;
  isLoading: boolean;
  error: string | null;
}

export default function DraftPreview({ content, isLoading, error }: DraftPreviewProps) {
  if (isLoading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <div className="spinner" style={{ width: '2rem', height: '2rem', border: '3px solid #e0e0e0', borderTopColor: '#4361ee' }} />
        <p style={{ marginTop: '1rem', color: '#666' }}>Generating your thesis draft...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem', color: '#e71d36' }}>
        <p style={{ fontWeight: 600 }}>Error generating draft</p>
        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>{error}</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
        <p>No draft generated yet. Add sources and click "Generate Draft" to begin.</p>
      </div>
    );
  }

  return (
    <div className="draft-preview">
      {content}
    </div>
  );
}
