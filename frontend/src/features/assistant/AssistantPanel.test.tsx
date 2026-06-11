import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantPanel } from "./AssistantPanel";

// Mock the API transport boundary so the test exercises rendering + state only.
vi.mock("../../app/api", () => ({
  runQuery: vi.fn().mockResolvedValue({
    mode: "assistant",
    intent: "approvals",
    title: "Purchase orders & invoices pending approval",
    narrative: "There are 347 items currently awaiting approval.",
    bullets: ["347 items pending approval"],
    metrics: [{ label: "Pending", value: "347" }],
    table: null,
    alerts: [],
    actions: [],
    evidence: [],
    data_scope: ["approvals"],
    confidence: 0.85,
  }),
}));

describe("AssistantPanel", () => {
  it("submits a prompt and renders the grounded response", async () => {
    const user = userEvent.setup();
    render(<AssistantPanel />);

    await user.type(screen.getByLabelText("Message"), "What is pending approval?");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(screen.getByText("What is pending approval?")).toBeInTheDocument();
    expect(
      await screen.findByText("Purchase orders & invoices pending approval"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("There are 347 items currently awaiting approval."),
    ).toBeInTheDocument();
  });
});
