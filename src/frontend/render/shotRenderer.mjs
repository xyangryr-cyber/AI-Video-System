// shotRenderer.mjs — Node.js render script for Remotion shot rendering.
// Called by Python backend via subprocess.
// Input: CLI flags, Output: MP4 video file + JSON result on stdout.
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Project root (2 levels up from src/frontend/render/)
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");

// Resolve tsconfig path aliases for webpack
function resolveAlias(aliasPath) {
  return path.resolve(PROJECT_ROOT, aliasPath);
}

// Cached Remotion modules — lazily loaded on first use, overridable for testing
let _bundler = null;
let _renderer = null;

async function _loadRemotion() {
  if (!_bundler || !_renderer) {
    [_bundler, _renderer] = await Promise.all([
      import("@remotion/bundler"),
      import("@remotion/renderer"),
    ]);
  }
  return {
    bundle: _bundler.bundle,
    renderMedia: _renderer.renderMedia,
    selectComposition: _renderer.selectComposition,
  };
}

// Testing hook: inject mock Remotion modules
export function __setRemotionModules(bundler, renderer) {
  _bundler = bundler;
  _renderer = renderer;
}

export function parseArgs(argv = process.argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--shot-id") args.shotId = argv[++i];
    else if (arg === "--template") args.template = argv[++i];
    else if (arg === "--input") args.input = argv[++i];
    else if (arg === "--output") args.output = argv[++i];
    else if (arg === "--duration") args.duration = parseFloat(argv[++i]);
    else if (arg === "--resolution") args.resolution = argv[++i];
    else if (arg === "--fps") args.fps = parseInt(argv[++i], 10);
  }
  args.resolution = args.resolution || "1920x1080";
  args.fps = args.fps || 30;
  return args;
}

export async function renderShot(options) {
  const { shotId, template, input, output, duration, resolution, fps } = options;
  const [width, height] = resolution.split("x").map(Number);
  const durationInFrames = Math.ceil(duration * fps);

  try {
    const { bundle, renderMedia, selectComposition } = await _loadRemotion();

    const bundleLocation = await bundle({
      entryPoint: path.resolve(__dirname, "..", "remotion", "RootShotRender.tsx"),
      webpackOverride: (currentConfiguration) => ({
        ...currentConfiguration,
        resolve: {
          ...currentConfiguration.resolve,
          alias: {
            ...currentConfiguration.resolve?.alias,
            "@shared": resolveAlias("src/shared"),
            "@frontend": resolveAlias("src/frontend"),
          },
        },
      }),
    });

    const parsedInput = JSON.parse(input);

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "ShotRender",
      inputProps: {
        shot: { ...parsedInput, template_type: template },
        templateType: template,
        durationInFrames,
        width,
        height,
        fps,
      },
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: path.resolve(output),
      inputProps: composition.inputProps,
    });

    return {
      status: "ok",
      output_path: output,
      duration_seconds: duration,
    };
  } catch (err) {
    return {
      status: "error",
      error: err.message,
    };
  }
}

async function main() {
  const opts = parseArgs();
  const result = await renderShot(opts);
  console.log(JSON.stringify(result));
  if (result.status === "error") process.exit(1);
}

const isMain =
  process.argv[1] === __filename ||
  process.argv[1]?.endsWith("/shotRenderer.mjs") ||
  process.argv[1]?.endsWith("\\shotRenderer.mjs");

if (isMain) {
  main();
}
