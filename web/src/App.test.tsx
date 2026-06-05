import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

const settings = {
  ai_provider: "fake",
  default_language: "en",
  available_providers: ["ollama", "gemini", "anthropic", "openai"],
  providers_with_keys: [],
};

function mockFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";
    const ok = (body: unknown) =>
      new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });

    if (url.endsWith("/api/settings") && method === "GET") return ok(settings);
    // No saved profiles → the app starts blank on the Background step.
    if (url.endsWith("/api/profiles") && method === "GET") return ok([]);
    if (url.endsWith("/api/profiles") && method === "POST") return ok({ id: 1 });
    if (url.includes("/api/profiles/") && method === "PATCH") return ok({ id: 1 });
    if (url.endsWith("/api/jobs") && method === "POST") return ok({ id: 2 });
    if (url.endsWith("/api/generation") && method === "POST")
      return ok({
        id: 7,
        profile_id: 1,
        job_id: 2,
        language: "en",
        provider: "fake",
        model: "fake-1",
        created_at: "now",
        latest_version: { id: 1, version_no: 1, content: "Dear team, I am a great fit.", origin: "ai", created_at: "now" },
      });
    return new Response("{}", { status: 200 });
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch());
});
afterEach(() => {
  vi.unstubAllGlobals();
});

// Walk the stepper from the Background step through to a generated letter.
async function generateLetter(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByText(/your background/i);
  await user.type(screen.getByPlaceholderText(/jane developer/i), "Vitor");
  await user.type(screen.getByPlaceholderText(/10 years building/i), "10y backend in Go and Python");
  await user.click(screen.getByRole("button", { name: /continue/i }));

  await user.type(screen.getByPlaceholderText(/staff engineer/i), "Staff Engineer");
  await user.type(screen.getByPlaceholderText(/paste the job posting/i), "Backend platform role");
  await user.click(screen.getByRole("button", { name: /generate cover letter/i }));
}

describe("App", () => {
  it("loads on the Background step", async () => {
    render(<App />);
    expect(await screen.findByText(/your background/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/jane developer/i)).toBeInTheDocument();
  });

  it("locks the Review step until a letter exists", async () => {
    render(<App />);
    await screen.findByText(/your background/i);
    expect(screen.getByRole("button", { name: /review letter/i })).toBeDisabled();
  });

  it("generates a letter and shows it in the preview", async () => {
    const user = userEvent.setup();
    render(<App />);
    await generateLetter(user);

    expect(await screen.findByText(/i am a great fit/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "PDF" })).toBeEnabled();
  });

  it("toggles to manual editing", async () => {
    const user = userEvent.setup();
    render(<App />);
    await generateLetter(user);
    await screen.findByText(/i am a great fit/i);

    await user.click(screen.getByRole("button", { name: /edit manually/i }));
    expect(await screen.findByDisplayValue(/i am a great fit/i)).toBeInTheDocument();
  });
});
