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
    if (url.endsWith("/api/profiles") && method === "POST") return ok({ id: 1 });
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

describe("App", () => {
  it("loads and shows the empty editor state", async () => {
    render(<App />);
    expect(await screen.findByText(/your generated cover letter will appear here/i)).toBeInTheDocument();
  });

  it("disables export buttons until a letter exists", async () => {
    render(<App />);
    await screen.findByText(/will appear here/i);
    expect(screen.getByRole("button", { name: "PDF" })).toBeDisabled();
  });

  it("generates a letter and shows it in the preview", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/will appear here/i);

    await user.type(screen.getByPlaceholderText(/jane developer/i), "Vitor");
    await user.type(screen.getByPlaceholderText(/10 years building/i), "10y backend in Go and Python");
    await user.type(screen.getByPlaceholderText(/staff engineer/i), "Staff Engineer");
    await user.type(screen.getByPlaceholderText(/paste the job posting/i), "Backend platform role");

    await user.click(screen.getByRole("button", { name: /generate cover letter/i }));

    expect(await screen.findByText(/i am a great fit/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "PDF" })).toBeEnabled();
  });

  it("toggles to manual editing", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/will appear here/i);
    await user.type(screen.getByPlaceholderText(/jane developer/i), "Vitor");
    await user.type(screen.getByPlaceholderText(/10 years building/i), "bg text here");
    await user.type(screen.getByPlaceholderText(/staff engineer/i), "Staff Engineer");
    await user.type(screen.getByPlaceholderText(/paste the job posting/i), "role");
    await user.click(screen.getByRole("button", { name: /generate cover letter/i }));
    await screen.findByText(/i am a great fit/i);

    await user.click(screen.getByRole("button", { name: /edit manually/i }));
    expect(await screen.findByDisplayValue(/i am a great fit/i)).toBeInTheDocument();
  });
});
