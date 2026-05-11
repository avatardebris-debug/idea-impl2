'use client';

import React, { useState } from 'react';
import TopicInput from '../components/TopicInput';
import SourceList from '../components/SourceList';
import CitationStyleSelector from '../components/CitationStyleSelector';
import DraftPreview from '../components/DraftPreview';
import ExportButtons from '../components/ExportButtons';
import { Source, createProject, addSource, createDraft, generateDraft, exportMarkdown, exportDocx } from '../lib/api';

export default function Home() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [draftId, setDraftId] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [citationStyle, setCitationStyle] = useState('APA');
  const [draftContent, setDraftContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateProject = async (topic: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await createProject(topic);
      setProjectId(res.id);
      setDraftContent('');
      setSources([]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSource = async (sourceData: Omit<Source, 'id' | 'metadata_completeness' | 'source_type'>) => {
    if (!projectId) return;
    try {
      const res = await addSource(projectId, sourceData.title, sourceData.authors, sourceData.year, sourceData.abstract, sourceData.url);
      setSources((prev) => [...prev, res.source]);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleRemoveSource = (sourceId: string) => {
    setSources((prev) => prev.filter((s) => s.id !== sourceId));
  };

  const handleGenerate = async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      // Create draft
      const draftRes = await createDraft(projectId, '', 'Thesis Draft', citationStyle);
      const newDraftId = draftRes.draft.id;
      setDraftId(newDraftId);

      // Generate
      const genRes = await generateDraft(projectId, newDraftId);

      // For now, show a placeholder draft content
      setDraftContent(`# Thesis Draft\n\nTopic: ${''}\n\nCitation Style: ${citationStyle}\n\nSources: ${sources.length}\n\n[Draft will appear here after generation completes.]`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportMarkdown = async () => {
    if (!projectId || !draftId) return;
    try {
      const res = await exportMarkdown(projectId, draftId);
      const blob = new Blob([res.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'thesis.md';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleExportDocx = async () => {
    if (!projectId || !draftId) return;
    try {
      const blob = await exportDocx(projectId, draftId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'thesis.docx';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <header className="header">
        <h1>📚 Academic Thesis Writer</h1>
      </header>

      <main className="container">
        {error && (
          <div style={{ background: '#ffe0e0', color: '#e71d36', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}

        <div className="grid grid-2">
          {/* Left column: inputs */}
          <div>
            <section className="card" style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>1. Create Project</h2>
              <TopicInput onSubmit={handleCreateProject} loading={loading} />
            </section>

            {projectId && (
              <>
                <section className="card" style={{ marginBottom: '1.5rem' }}>
                  <SourceList
                    sources={sources}
                    onAdd={handleAddSource}
                    onRemove={handleRemoveSource}
                  />
                </section>

                <section className="card" style={{ marginBottom: '1.5rem' }}>
                  <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>2. Settings</h2>
                  <div style={{ display: 'grid', gap: '1rem' }}>
                    <CitationStyleSelector value={citationStyle} onChange={setCitationStyle} />
                    <button
                      className="btn btn-primary"
                      onClick={handleGenerate}
                      disabled={loading || sources.length < 1}
                      style={{ width: '100%' }}
                    >
                      {loading ? <span className="spinner" /> : 'Generate Draft'}
                    </button>
                  </div>
                </section>
              </>
            )}
          </div>

          {/* Right column: preview */}
          <div>
            <section className="card" style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>3. Draft Preview</h2>
              <DraftPreview
                content={draftContent}
                isLoading={loading}
                error={error}
              />
            </section>

            {draftId && (
              <section className="card">
                <h2 style={{ fontWeight: 600, marginBottom: '1rem' }}>4. Export</h2>
                <ExportButtons
                  onExportMarkdown={handleExportMarkdown}
                  onExportDocx={handleExportDocx}
                  disabled={!draftContent}
                />
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
