const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: "school_admin" | "student" | "teacher";
  school_name: string | null;
  school_code: string | null;
  grade: number | null;
  grade_label: string | null;
};

export type Subject = { id: number; name: string; slug: string; description: string; topic_count: number };
export type Topic = {
  id: number;
  subject: number;
  title: string;
  slug: string;
  summary: string;
  content: string;
  grade: number | null;
  term: number | null;
  question_count: number;
};
export type SchoolClass = { id: number; name: string };
export type NewStudent = { username: string; password: string; first_name: string; last_name: string; grade: number; class_id: number | null };
export type NewTeacher = { username: string; password: string; first_name: string; last_name: string };
export type SchoolStudent = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  grade: number | null;
  grade_label: string | null;
  class_name: string | null;
  is_active: boolean;
  total_attempts: number;
  average_score: number | null;
};
export type StudentPerformance = {
  student: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    grade: number | null;
    grade_label: string | null;
    class_name: string | null;
    is_active: boolean;
  };
  summary: {
    total_attempts: number;
    correct_attempts: number;
    scored_attempts: number;
    average_score: number | null;
  };
  subjects: Array<{
    subject_id: number;
    subject: string;
    attempts: number;
    correct_attempts: number;
    scored_attempts: number;
    average_score: number | null;
    topics: Array<{
      topic_id: number;
      topic: string;
      attempts: number;
      correct_attempts: number;
      scored_attempts: number;
      average_score: number | null;
    }>;
  }>;
};
export type Question = {
  id: number;
  topic: number;
  kind: "mcq" | "theory";
  prompt: string;
  options: string[];
  difficulty: "easy" | "medium" | "hard";
  work_check_available: boolean;
};
export type StructuredQuestion = Question & { kind: "theory"; options: [] };
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
  worked_solution: string;
  mark_guide: string;
  question_kind: "mcq" | "theory";
  created_at: string;
};
export type WorkCheck = {
  status: "correct" | "partly_correct" | "incorrect" | "unreadable";
  feedback: string;
  worked_solution: string;
};
export type Progress = {
  summary: { total_attempts: number; correct_attempts: number; scored_attempts: number; average_score: number };
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
  students: Array<{ id: number; username: string; first_name: string; last_name: string; grade: number | null; class_name: string | null; is_active: boolean; total_attempts: number; average_score: number | null }>;
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
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
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
  login: (school_code: string, username: string, password: string) =>
    request<Tokens>("/auth/login/", { method: "POST", body: JSON.stringify({ school_code, username, password }) }),
  registerSchool: (data: { school_name: string; first_name: string; last_name: string; username: string; password: string }) =>
    request<{ detail: string; school_name: string; school_code: string }>("/auth/register-school/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  registerStudent: (data: { school_code: string; first_name: string; last_name: string; username: string; password: string; grade: number }) =>
    request<Tokens>("/auth/register-student/", { method: "POST", body: JSON.stringify(data) }),
  me: () => request<User>("/auth/me/"),
  subjects: () => request<Subject[]>("/subjects/"),
  topics: (subjectId: number, grade?: number) =>
    request<Topic[]>(`/subjects/${subjectId}/topics/${grade ? `?grade=${grade}` : ""}`),
  topic: (topicId: number) => request<Topic>(`/topics/${topicId}/`),
  questions: (topicId: number) => request<Question[]>(`/topics/${topicId}/questions/`),
  submit: (questionId: number, answer: string) =>
    request<Attempt>("/attempts/", { method: "POST", body: JSON.stringify({ question_id: questionId, answer }) }),
  checkWork: (attemptId: number, file: File) => {
    const data = new FormData();
    data.set("work", file);
    return request<WorkCheck>(`/attempts/${attemptId}/work-check/`, { method: "POST", body: data });
  },
  progress: () => request<Progress>("/progress/"),
  report: (filters: { class_id?: number; subject_id?: number; grade?: number } = {}) => {
    const params = new URLSearchParams();
    if (filters.class_id) params.set("class_id", String(filters.class_id));
    if (filters.subject_id) params.set("subject_id", String(filters.subject_id));
    if (filters.grade) params.set("grade", String(filters.grade));
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
  createTeacher: (teacher: NewTeacher) =>
    request<{ id: number; username: string; first_name: string; last_name: string; school_name: string; school_code: string; role: "teacher" }>("/admin/teachers/", {
      method: "POST",
      body: JSON.stringify(teacher),
    }),
  importStudents: (file: File) => {
    const data = new FormData();
    data.set("file", file);
    return request<{ created: number; usernames: string[] }>("/admin/students/import/", {
      method: "POST",
      body: data,
    });
  },
  students: () => request<SchoolStudent[]>("/admin/students/"),
  studentPerformance: (studentId: number) =>
    request<StudentPerformance>(`/admin/students/${studentId}/performance/`),
  updateStudent: (studentId: number, is_active: boolean) =>
    request<SchoolStudent>(`/admin/students/${studentId}/`, {
      method: "PATCH",
      body: JSON.stringify({ is_active }),
    }),
  resetStudentPassword: (studentId: number, password: string) =>
    request<{ detail: string }>(`/admin/students/${studentId}/reset-password/`, {
      method: "POST",
      body: JSON.stringify({ password }),
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
