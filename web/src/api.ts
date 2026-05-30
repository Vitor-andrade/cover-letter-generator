// Typed client mirroring the FastAPI DTOs (src/clg/api/schemas.py).

export type ProfileSource = "manual" | "upload";
export type VersionOrigin = "ai" | "manual";

export interface Profile {
  id: number;
  name: string;
  background_text: string;
  source: ProfileSource;
  created_at: string;
}

export interface Job {
  id: number;
  title: string;
  company: string | null;
  description: string;
  created_at: string;
}

export interface LetterVersion {
  id: number;
  version_no: number;
  content: string;
  origin: VersionOrigin;
  created_at: string;
}

export interface Letter {
  id: number;
  profile_id: number;
  job_id: number;
  language: string;
  provider: string;
  model: string | null;
  created_at: string;
  latest_version: LetterVersion | null;
}

export interface Settings {
  ai_provider: string;
  default_language: string;
  available_providers: string[];
  providers_with_keys: string[];
}

export type ExportFormat = "txt" | "markdown" | "html" | "pdf" | "docx";

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetch("/api/health").then(json<{ status: string; version: string }>),

  createProfile: (body: { name: string; background_text: string; source: ProfileSource }) =>
    fetch("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json<Profile>),

  uploadProfile: (name: string, file: File) => {
    const form = new FormData();
    form.append("name", name);
    form.append("file", file);
    return fetch("/api/profiles/upload", { method: "POST", body: form }).then(json<Profile>);
  },

  createJob: (body: { title: string; company: string | null; description: string }) =>
    fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json<Job>),

  generate: (body: {
    profile_id: number;
    job_id: number;
    language: string;
    provider?: string | null;
  }) =>
    fetch("/api/generation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json<Letter>),

  regenerate: (body: { letter_id: number; instruction: string; language?: string | null }) =>
    fetch("/api/generation/regenerate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json<LetterVersion>),

  getSettings: () => fetch("/api/settings").then(json<Settings>),

  updateSettings: (body: { ai_provider?: string; default_language?: string }) =>
    fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(json<Settings>),

  setProviderKey: (provider: string, api_key: string) =>
    fetch("/api/settings/keys", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key }),
    }).then(json<Settings>),

  exportUrl: (letterId: number, fmt: ExportFormat) => `/api/export/${letterId}/${fmt}`,
};

export { ApiError };
