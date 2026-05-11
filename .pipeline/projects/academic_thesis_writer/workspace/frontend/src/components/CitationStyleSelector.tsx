'use client';

import React from 'react';

interface CitationStyleSelectorProps {
  value: string;
  onChange: (style: string) => void;
}

const STYLES = [
  { value: 'APA', label: 'APA 7th' },
  { value: 'MLA', label: 'MLA 9th' },
  { value: 'CHICAGO', label: 'Chicago 17th' },
  { value: 'IEEE', label: 'IEEE' },
];

export default function CitationStyleSelector({ value, onChange }: CitationStyleSelectorProps) {
  return (
    <div>
      <label htmlFor="citation-style" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
        Citation Style
      </label>
      <select
        id="citation-style"
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {STYLES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>
    </div>
  );
}
