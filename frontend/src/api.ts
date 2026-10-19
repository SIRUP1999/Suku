const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: "school_admin" | "student" | "teacher";
  school_name: string | null;
};

export type Subject = { id: number; name: string; slug: string; description: string; topic_count: number };
export type Topic = {
  id: number;
  subject: number;
  title: string;
  slug: string;
  summary: string;
  content: string;
  question_count: number;
};
export type SchoolClass = { id: number; name: string };
export type NewStudent = { username: string; password: string; first_name: string; last_name: string; class_id: number | null };
export type Question = {
  id: number;
  topic: number;
  kind: "mcq" | "theory";
  prompt: string;
  options: string[];
  difficulty: "easy" | "medium" | "hard";
};
export type Attempt = {
  id: number;
  question: number;
  question_prompt: string;
  subject: string;
  topic: string;
  submitted_answer: string;
  is_correct: boolean | null;
  score: number | null;
  feedback: string;
  correct_answer: string;
  created_at: string;
};
export type Progress = {
  summary: { total_attempts: number; correct_attempts: number; average_score: number };
  attempts: Attempt[];
};
export type Report = {
  school: string;
  student_count: number;
  total_student_count: number;
  classes: SchoolClass[];
  available_subjects: Array<{ id: number; name: string }>;
  subscription: { term_name: string; starts_at: string; ends_at: string; seat_limit: number; status: string; is_current: boolean } | null;
  summary: { total_attempts: number; correct_attempts: number; average_score: number };
  subjects: Array<{ question__topic__subject__id: number; question__topic__subject__name: string; attempts: number; correct: number; average_score: number | null }>;
  students: Array<{ id: number; username: string; first_name: string; last_name: string; total_attempts: number; average_score: number | null }>;
};

type Tokens = { access: string; refresh: string; user: User };
const tokenKey = "suku-access-token";
const refreshKey = "suku-refresh-token";

export function getToken() {
  return localStorage.getItem(tokenKey);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(tokenKey, token);
  else {
    localStorage.removeItem(tokenKey);
    localStorage.removeItem(refreshKey);
  }
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(tokenKey, access);
  localStorage.setItem(refreshKey, refresh);
}

async function request<T>(path: string, options: RequestInit = {}, mayRefresh = true): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 401 && mayRefresh && path !== "/auth/login/") {
    const refresh = localStorage.getItem(refreshKey);
    if (refresh) {
      const refreshed = await fetch(`${API_URL}/auth/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
      const tokens = (await refreshed.json().catch(() => ({}))) as { access?: string };
      if (refreshed.ok && tokens.access) {
        localStorage.setItem(tokenKey, tokens.access);
        return request<T>(path, options, false);
      }
    }
    setToken(null);
  }
  const payload: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const messages = errorMessages(payload);
    throw new Error(messages.join(" ") || `Request failed (${response.status})`);
  }
  return payload as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<Tokens>("/auth/login/", { method: "POST", body: JSON.stringify({ username, password }) }),
  me: () => request<User>("/auth/me/"),
  subjects: () => request<Subject[]>("/subjects/"),
  topics: (subjectId: number) => request<Topic[]>(`/subjects/${subjectId}/topics/`),
  questions: (topicId: number) => request<Question[]>(`/topics/${topicId}/questions/`),
  submit: (questionId: number, answer: string) =>
    request<Attempt>("/attempts/", { method: "POST", body: JSON.stringify({ question_id: questionId, answer }) }),
  progress: () => request<Progress>("/progress/"),
  report: (filters: { class_id?: number; subject_id?: number } = {}) => {
    const params = new URLSearchParams();
    if (filters.class_id) params.set("class_id", String(filters.class_id));
    if (filters.subject_id) params.set("subject_id", String(filters.subject_id));
    const query = params.size ? `?${params.toString()}` : "";
    return request<Report>(`/admin/reports/${query}`);
  },
  schoolClasses: () => request<SchoolClass[]>("/admin/classes/"),
  createClass: (name: string) => request<SchoolClass>("/admin/classes/", { method: "POST", body: JSON.stringify({ name }) }),
  createStudents: (students: NewStudent[]) =>
    request<{ created: number; usernames: string[] }>("/admin/students/bulk-create/", {
      method: "POST",
      body: JSON.stringify({ students }),
    }),
};

function errorMessages(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(errorMessages);
  if (value && typeof value === "object") {
    return Object.values(value).flatMap(errorMessages);
  }
  return [];
}
