export interface TagWithConfidence {
  name: string;
  confidence: number;
}

export interface Problem {
  id: string;
  source: string;
  grade: number;
  year: number;
  problem_number: number;
  statement: string;
  choices: string[];
  tags: string[];
  url: string;
  images: string[];  // Base64 data URIs for problem images
}

export interface ProblemDetail extends Problem {
  answer: string | null;
  solution: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AnalyzeResponse {
  tags: TagWithConfidence[];
}

export interface HintResponse {
  response: string;
}

export interface TagsResponse {
  tags: Record<string, string[]>;
  all_tags: string[];
  tag_counts: Record<string, number>;
}
