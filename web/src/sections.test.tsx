import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import type { Sections } from "./api";
import { SectionsEditor, emptySections, hasAnyContent } from "./SectionsEditor";

function Harness() {
  const [sections, setSections] = useState<Sections>(emptySections());
  return (
    <>
      <SectionsEditor sections={sections} onChange={setSections} />
      <output data-testid="has-content">{String(hasAnyContent(sections))}</output>
    </>
  );
}

describe("SectionsEditor", () => {
  it("adds skills as chips and reports content", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    expect(screen.getByTestId("has-content").textContent).toBe("false");

    await user.click(screen.getByRole("button", { name: /^skills$/i }));
    const input = screen.getByPlaceholderText(/add a skill/i);
    await user.type(input, "Go{Enter}");
    await user.type(input, "Python{Enter}");

    expect(screen.getByText(/Go ×/)).toBeInTheDocument();
    expect(screen.getByText(/Python ×/)).toBeInTheDocument();
    expect(screen.getByTestId("has-content").textContent).toBe("true");
  });

  it("adds and removes an experience entry", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByRole("button", { name: /experience/i }));
    await user.click(screen.getByRole("button", { name: /add experience/i }));

    await user.type(screen.getByPlaceholderText(/staff engineer/i), "Lead Dev");
    expect(screen.getByDisplayValue("Lead Dev")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^remove$/i }));
    expect(screen.queryByDisplayValue("Lead Dev")).not.toBeInTheDocument();
  });
});
