import "@testing-library/jest-dom/vitest";

// Stub HTMLMediaElement for jsdom (play/pause not implemented)
if (typeof HTMLMediaElement !== "undefined") {
  beforeAll(() => {
    HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
    HTMLMediaElement.prototype.pause = vi.fn();
  });
}

// Mock remotion — provides test-friendly implementations of all remotion exports.
// The real <Composition> requires the Remotion runtime (Headless Browser)
// and does not render children in jsdom.
vi.mock("remotion", async () => {
  const React = await import("react");
  return {
    Composition: ({
      component: Comp,
      defaultProps,
    }: {
      component: React.ComponentType<any>;
      defaultProps: Record<string, any>;
    }) => React.createElement(Comp, defaultProps),
    useCurrentFrame: vi.fn(() => 0),
    useVideoConfig: vi.fn(() => ({
      fps: 30,
      width: 1920,
      height: 1080,
      durationInFrames: 300,
    })),
    AbsoluteFill: ({
      children,
      style,
    }: {
      children?: React.ReactNode;
      style?: React.CSSProperties;
    }) => React.createElement("div", { style }, children),
    Sequence: ({ children }: { children?: React.ReactNode }) =>
      React.createElement("div", {}, children),
  };
});
