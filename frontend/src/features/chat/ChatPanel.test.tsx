import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPanel } from "./ChatPanel";

// Mock the API client (the transport boundary). The component test then
// only exercises rendering + state, with no real HTTP, URLs, or sessions.
vi.mock("../../lib/api", () => ({
  sendChatMessage: vi.fn().mockResolvedValue({ reply: "Hello from the backend." }),
}));

describe("ChatPanel", () => {
  it("submits a message and renders the backend reply", async () => {
    const user = userEvent.setup();
    render(<ChatPanel />);

    await user.type(screen.getByLabelText("Message"), "Hi there");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(screen.getByText("Hi there")).toBeInTheDocument();
    expect(await screen.findByText("Hello from the backend.")).toBeInTheDocument();
  });
});
