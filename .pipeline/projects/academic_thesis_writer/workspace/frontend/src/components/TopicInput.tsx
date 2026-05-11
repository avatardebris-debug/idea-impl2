'use client';

import React, { useState } from 'react';

interface TopicInputProps {
  onSubmit: (topic: string) => void;
  loading?: boolean;
}

export default function TopicInput({ onSubmit, loading = false }: TopicInputProps) {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      onSubmit(topic.trim());
      setTopic('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '1.5rem' }}>
      <label htmlFor="topic" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
        Research Topic
      </label>
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <input
          id="topic"
          type="text"
          className="input"
          placeholder="Enter your research topic..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          style={{ flex: 1 }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !topic.trim()}
        >
          {loading ? <span className="spinner" /> : 'Create Project'}
        </button>
      </div>
    </form>
  );
}
