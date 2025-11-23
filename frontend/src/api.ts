import type { AnalyzeResponse, Problem, ProblemDetail, HintResponse, TagsResponse, ChatMessage } from './types';

const API_BASE = '/api';

export async function analyzeLaTeX(latex: string): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latex }),
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze: ${response.statusText}`);
  }

  return response.json();
}

export async function getProblems(tags?: string[], grade?: number, year?: number): Promise<Problem[]> {
  const params = new URLSearchParams();
  if (tags && tags.length > 0) {
    params.set('tags', tags.join(','));
  }
  if (grade !== undefined) {
    params.set('grade', grade.toString());
  }
  if (year !== undefined) {
    params.set('year', year.toString());
  }

  const url = params.toString() ? `${API_BASE}/problems?${params}` : `${API_BASE}/problems`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch problems: ${response.statusText}`);
  }

  return response.json();
}

export async function getProblem(id: string): Promise<ProblemDetail> {
  const response = await fetch(`${API_BASE}/problems/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch problem: ${response.statusText}`);
  }

  return response.json();
}

export async function getHint(
  problemId: string,
  conversation: ChatMessage[],
  message: string
): Promise<HintResponse> {
  const response = await fetch(`${API_BASE}/hint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      problem_id: problemId,
      conversation,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to get hint: ${response.statusText}`);
  }

  return response.json();
}

export async function getTags(): Promise<TagsResponse> {
  const response = await fetch(`${API_BASE}/tags`);

  if (!response.ok) {
    throw new Error(`Failed to fetch tags: ${response.statusText}`);
  }

  return response.json();
}
