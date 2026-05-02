// @vitest-environment node

import { describe, it, expect, vi, beforeEach } from "vitest";

const mockBundle = vi.fn();
const mockRenderMedia = vi.fn();
const mockSelectComposition = vi.fn();

const mod = await import(
  "../../../../src/frontend/render/shotRenderer.mjs"
);

const { parseArgs, renderShot, __setRemotionModules } = mod;

// Inject mock Remotion modules before any renderShot call
__setRemotionModules(
  { bundle: (...args: any[]) => mockBundle(...args) },
  { renderMedia: (...args: any[]) => mockRenderMedia(...args), selectComposition: (...args: any[]) => mockSelectComposition(...args) }
);

beforeEach(() => {
  vi.clearAllMocks();
  mockBundle.mockResolvedValue("/tmp/bundle-output");
  mockSelectComposition.mockResolvedValue({
    id: "ShotRender",
    durationInFrames: 465,
    fps: 30,
    width: 1920,
    height: 1080,
  });
  mockRenderMedia.mockResolvedValue(undefined);
});

describe("parseArgs", () => {
  it("parses all CLI flags into a structured options object", () => {
    const argv = [
      "/usr/local/bin/node",
      "/app/shotRenderer.mjs",
      "--shot-id", "shot_01",
      "--template", "animated_line_chart",
      "--input", '{"content":{"title":"test"}}',
      "--output", "data/projects/p1/phase_8/shot_01.mp4",
      "--duration", "15.5",
      "--resolution", "1920x1080",
      "--fps", "30",
    ];

    const opts = parseArgs(argv);

    expect(opts.shotId).toBe("shot_01");
    expect(opts.template).toBe("animated_line_chart");
    expect(opts.input).toBe('{"content":{"title":"test"}}');
    expect(opts.output).toBe("data/projects/p1/phase_8/shot_01.mp4");
    expect(opts.duration).toBe(15.5);
    expect(opts.resolution).toBe("1920x1080");
    expect(opts.fps).toBe(30);
  });

  it("uses defaults for resolution and fps when not provided", () => {
    const argv = [
      "node",
      "render.mjs",
      "--shot-id", "s1",
      "--template", "data_card",
      "--input", "{}",
      "--output", "out.mp4",
      "--duration", "10",
    ];

    const opts = parseArgs(argv);

    expect(opts.resolution).toBe("1920x1080");
    expect(opts.fps).toBe(30);
  });
});

describe("renderShot", () => {
  it("calls bundle with the composition entry point", async () => {
    const opts = {
      shotId: "shot_01",
      template: "animated_line_chart",
      input: '{"content":{}}',
      output: "data/projects/p1/phase_8/shot_01.mp4",
      duration: 15.5,
      resolution: "1920x1080",
      fps: 30,
    };

    await renderShot(opts);

    expect(mockBundle).toHaveBeenCalledTimes(1);
    const bundleArg = mockBundle.mock.calls[0][0];
    expect(bundleArg.entryPoint).toContain("RootShotRender");
  });

  it("calls selectComposition with ShotRender id and correct inputProps", async () => {
    const opts = {
      shotId: "shot_01",
      template: "animated_line_chart",
      input: '{"content":{"title":"Test Chart"}}',
      output: "out.mp4",
      duration: 15.5,
      resolution: "1920x1080",
      fps: 30,
    };

    await renderShot(opts);

    expect(mockSelectComposition).toHaveBeenCalledTimes(1);
    const callArgs = mockSelectComposition.mock.calls[0][0];
    expect(callArgs.id).toBe("ShotRender");
    expect(callArgs.inputProps.shot.template_type).toBe("animated_line_chart");
    expect(callArgs.inputProps.durationInFrames).toBe(465);
  });

  it("calls renderMedia with h264 codec and correct output path", async () => {
    const opts = {
      shotId: "shot_01",
      template: "data_card",
      input: "{}",
      output: "/abs/path/out.mp4",
      duration: 10,
      resolution: "1280x720",
      fps: 24,
    };

    await renderShot(opts);

    expect(mockRenderMedia).toHaveBeenCalledTimes(1);
    const renderOpts = mockRenderMedia.mock.calls[0][0];
    expect(renderOpts.codec).toBe("h264");
    expect(renderOpts.outputLocation).toBe("/abs/path/out.mp4");
  });

  it("returns { status: ok } with output path on success", async () => {
    const opts = {
      shotId: "shot_01",
      template: "data_card",
      input: "{}",
      output: "out.mp4",
      duration: 10,
      resolution: "1920x1080",
      fps: 30,
    };

    const result = await renderShot(opts);

    expect(result).toEqual({
      status: "ok",
      output_path: "out.mp4",
      duration_seconds: 10,
    });
  });

  it("returns { status: error } when bundle fails", async () => {
    mockBundle.mockRejectedValue(new Error("Bundle failed: out of memory"));

    const opts = {
      shotId: "shot_01",
      template: "data_card",
      input: "{}",
      output: "out.mp4",
      duration: 10,
      resolution: "1920x1080",
      fps: 30,
    };

    const result = await renderShot(opts);

    expect(result.status).toBe("error");
    expect(result.error).toContain("Bundle failed");
  });
});
