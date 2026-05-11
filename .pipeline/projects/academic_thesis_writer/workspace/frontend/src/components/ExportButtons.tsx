'use client';

import React from 'react';

interface ExportButtonsProps {
  onExportMarkdown: () => void;
  onExportDocx: () => void;
  disabled: boolean;
}

export default function ExportButtons({ onExportMarkdown, onExportDocx, disabled }: ExportButtonsProps) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
      <button
        className="btn btn-secondary"
        onClick={onExportMarkdown}
        disabled={disabled}
      >
        📄 Export Markdown
      </button>
      <button
        className="btn btn-secondary"
        onClick={onExportDocx}
        disabled={disabled}
      >
        📝 Export DOCX
      </button>
    </div>
  );
}
