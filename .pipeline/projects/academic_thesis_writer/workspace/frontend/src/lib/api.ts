/**
 * API client for the Academic Thesis Writer backend.
 * All methods call the FastAPI server at http://localhost:8000.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types ────────────────────────────────────────────────────────────────

export interface Source {
  id: string;
  title: string;
  authors: string[];
  year?: number;
  abstract: string;
  url?: string;
  source_type: string;
  metadata_completeness: number;
}

export interface Draft {
  id: string;
  topic: string;
  title: string;
  citation_style: string;
  sections: Section[];
  bibliography: BibliographyEntry[];
}

export interface Section {
  name: string;
  content: string;
  inline_citations: InlineCitation[];
}

export interface InlineCitation {
  citation_key: string;
  source_id: string;
  position: number;
}

export interface BibliographyEntry {
  citation_key: string;
  source_id: string;
  style: string;
  formatted: string;
}

export interface ThesisProject {
  id: string;
  topic: string;
  sources: Source[];
  draft: Draft | null;
  citation_style: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────

async function request<T>(
  method: string,
  url: string,
  body?: unknown
): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) {
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${method} ${url} failed: ${res.status} ${err}`);
  }
  return res.json() as Promise<T>;
}

// ── Project / Source endpoints ────────────────────────────────────────────

export async function createProject(topic: string): Promise<ThesisProject> {
  return request<ThesisProject>('POST', `${API_BASE}/api/projects`, { topic });
}

export async function addSource(
  projectId: string,
  title: string,
  authors: string[],
  year?: number,
  abstract?: string,
  url?: string
): Promise<{ status: string; source: Source }> {
  return request<{ status: string; source: Source }>(
    'POST',
    `${API_BASE}/api/projects/${projectId}/sources`,
    { title, authors, year, abstract: abstract || '', url }
  );
}

export async function getSources(projectId: string): Promise<{ sources: Source[] }> {
  return request<{ sources: Source[] }>(
    'GET',
    `${API_BASE}/api/projects/${projectId}/sources`
  );
}

// ── Draft endpoints ───────────────────────────────────────────────────────

export async function createDraft(
  projectId: string,
  topic: string,
  title: string,
  citationStyle: string
): Promise<{ status: string; draft: Draft }> {
  return request<{ status: string; draft: Draft }>(
    'POST',
    `${API_BASE}/api/projects/${projectId}/drafts`,
    { topic, title, citation_style: citationStyle }
  );
}

export async function getDraft(
  projectId: string,
  draftId: string
): Promise<{ draft: Draft | null }> {
  return request<{ draft: Draft | null }>(
    'GET',
    `${API_BASE}/api/projects/${projectId}/drafts/${draftId}`
  );
}

export async function generateDraft(
  projectId: string,
  draftId: string
): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(
    'POST',
    `${API_BASE}/api/projects/${projectId}/drafts/${draftId}/generate`
  );
}

export async function verifyDraft(
  projectId: string,
  draftId: string
): Promise<{ status: string; result: { is_valid: boolean; errors: string[]; warnings: string[] } }> {
  return request<{ status: string; result: { is_valid: boolean; errors: string[]; warnings: string[] } }>(
    'POST',
    `${API_BASE}/api/projects/${projectId}/drafts/${draftId}/verify`
  );
}

// ── Export endpoints ──────────────────────────────────────────────────────

export async function exportMarkdown(
  projectId: string,
  draftId: string
): Promise<{ status: string; content: string }> {
  return request<{ status: string; content: string }>(
    'GET',
    `${API_BASE}/api/projects/${projectId}/drafts/${draftId}/export/markdown`
  );
}

export async function exportDocx(
  projectId: string,
  draftId: string
): Promise<Blob> {
  const res = await fetch(
    `${API_BASE}/api/projects/${projectId}/drafts/${draftId}/export/docx`,
    { method: 'GET', headers: { 'Content-Type': 'application/json' } }
  );
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`DOCX export failed: ${res.status} ${err}`);
  }
  return res.blob();
}
