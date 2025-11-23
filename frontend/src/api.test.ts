import { describe, it, expect, vi, afterEach } from 'vitest';
import { getProblems, getProblem } from './api';

const makeResponse = (body: unknown, ok = true, status = 200) =>
  new Response(JSON.stringify(body), { status, statusText: ok ? 'OK' : 'Bad Request' });

afterEach(() => {
  vi.restoreAllMocks();
});

describe('api.ts', () => {
  it('builds query params for getProblems', async () => {
    const mockFetch = vi.fn(async (url: RequestInfo, init?: RequestInit) => {
      expect(url).toBe('/api/problems?tags=angles%2Cgeometry&grade=7&year=2025');
      expect(init).toBeUndefined();
      return makeResponse([]);
    });
    vi.stubGlobal('fetch', mockFetch);

    await getProblems(['angles', 'geometry'], 7, 2025);
    expect(mockFetch).toHaveBeenCalledOnce();
  });

  it('throws on non-200 responses', async () => {
    const mockFetch = vi.fn(async () => makeResponse({}, false, 500));
    vi.stubGlobal('fetch', mockFetch);

    await expect(getProblem('abc')).rejects.toThrow(/Failed to fetch problem/);
  });
});
