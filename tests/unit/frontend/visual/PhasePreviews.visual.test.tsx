import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { P3VoiceScriptView } from "@frontend/components/previews/P3VoiceScriptView";
import { P4SegmentAudioPlayer } from "@frontend/components/previews/P4SegmentAudioPlayer";
import { P5WaveformPlayer } from "@frontend/components/previews/P5WaveformPlayer";
import { P6SfxListPlayer } from "@frontend/components/previews/P6SfxListPlayer";
import { P7StoryboardGallery } from "@frontend/components/previews/P7StoryboardGallery";
import { P8FrameGallery } from "@frontend/components/previews/P8FrameGallery";
import { P9BrollGallery } from "@frontend/components/previews/P9BrollGallery";
import { P10VideoPlayer } from "@frontend/components/previews/P10VideoPlayer";
import { P11FinalPlayer } from "@frontend/components/previews/P11FinalPlayer";
import type { BrollItem } from "@frontend/types/preview";

// ---------------------------------------------------------------------------
// P3VoiceScriptView
// ---------------------------------------------------------------------------
describe("P3VoiceScriptView visual alignment", () => {
  const SAMPLE_CONTENT =
    "大家还记得去年这时候，黄金才多少钱一克吗？现在再看看金价，是不是觉得有些高攀不起了？今天咱们不聊虚的，直接来盘一盘这波黄金暴涨背后的核心推手。";

  const SAMPLE_VOICE_DIRECTIONS = [
    { text: "开头口语化", tone: "亲切科普型", pace: "中速" },
  ];

  it("renders purple style badge with Sparkles icon", () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    const badge = document.querySelector(".bg-purple-100");
    expect(badge).not.toBeNull();
    expect(screen.getByText(/亲切科普型/)).toBeDefined();
    expect(screen.getByText(/Style Applied:/)).toBeDefined();
  });

  it("renders word count and duration", () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    expect(screen.getByText(/总字数/)).toBeDefined();
  });

  it("renders amber callout with border-l styling", () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    const callout = document.querySelector(".bg-amber-50");
    expect(callout).not.toBeNull();
    const borderLeft = document.querySelector(".border-l-4");
    expect(borderLeft).not.toBeNull();
  });

  it('renders "口语化优化" label on callout', () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    expect(screen.getByText(/口语化优化/)).toBeDefined();
  });

  it("renders prose text content", () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    expect(screen.getByText(/黄金才多少钱一克/)).toBeDefined();
  });

  it("renders empty state when no content", () => {
    render(<P3VoiceScriptView />);
    expect(screen.getByTestId("preview-p3")).toBeDefined();
    const emptyContainer = document.querySelector(".flex.flex-col.items-center");
    expect(emptyContainer).not.toBeNull();
  });

  it("renders card with border-2 border-slate-200 rounded-xl", () => {
    render(
      <P3VoiceScriptView
        content={SAMPLE_CONTENT}
        voice_directions={SAMPLE_VOICE_DIRECTIONS}
      />,
    );
    const card = document.querySelector(".border-2.border-slate-200.rounded-xl");
    expect(card).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// P4SegmentAudioPlayer
// ---------------------------------------------------------------------------
describe("P4SegmentAudioPlayer visual alignment", () => {
  const SEGMENTS = [
    { id: "seg1", audio_url: "/audio/seg1.wav", text: "段落 1 音频", duration_sec: 30, cps: "4.0", status: "ready" },
    { id: "seg2", audio_url: "/audio/seg2.wav", text: "段落 2 音频", duration_sec: 45, cps: "4.2", status: "ready" },
    { id: "seg3", audio_url: "/audio/seg3.wav", text: "段落 3 音频", duration_sec: 72, cps: "3.8", status: "ready", warn: true },
  ];

  it("renders empty state with centered layout when no segments", () => {
    render(<P4SegmentAudioPlayer />);
    expect(screen.getByTestId("preview-p4")).toBeDefined();
    const emptyContainer = document.querySelector(".flex.flex-col.items-center");
    expect(emptyContainer).not.toBeNull();
  });

  it('renders "分段试听与干音确认" header', () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    expect(screen.getByText(/分段试听与干音确认/)).toBeDefined();
  });

  it("renders dark play button for each segment", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    const darkBtns = document.querySelectorAll(".bg-slate-900.text-white.rounded-full");
    expect(darkBtns.length).toBe(3);
  });

  it("renders waveform bars for each segment", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    const gapElements = document.querySelectorAll("[class*='gap-\\[2px\\]']");
    expect(gapElements.length).toBeGreaterThanOrEqual(3);
  });

  it("renders CPS label for each segment", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    expect(screen.getByText(/CPS: 4.0/)).toBeDefined();
    expect(screen.getByText(/CPS: 4.2/)).toBeDefined();
    expect(screen.getByText(/CPS: 3.8/)).toBeDefined();
  });

  it("renders warning state with amber styling", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    const warnRow = document.querySelector(".border-amber-200");
    expect(warnRow).not.toBeNull();
    expect(screen.getByText(/语速略缓/)).toBeDefined();
  });

  it("renders segment duration text", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    expect(screen.getByText(/0:30/)).toBeDefined();
    expect(screen.getByText(/1:12/)).toBeDefined();
  });

  it("renders footer with completed status and download button", () => {
    render(<P4SegmentAudioPlayer segments={SEGMENTS} />);
    expect(screen.getByText(/全案干音/)).toBeDefined();
    expect(screen.getByText(/已生成完毕/)).toBeDefined();
    expect(screen.getByText(/下载完整干音版/)).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// P5WaveformPlayer
// ---------------------------------------------------------------------------
describe("P5WaveformPlayer visual alignment", () => {
  it("renders empty state with centered layout when no audio_url", () => {
    render(<P5WaveformPlayer />);
    expect(screen.getByTestId("preview-p5")).toBeDefined();
    const emptyContainer = document.querySelector(".flex.flex-col.items-center");
    expect(emptyContainer).not.toBeNull();
  });

  it('renders "情感与能量曲线规划" mood curve header', () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/情感与能量曲线规划/)).toBeDefined();
  });

  it("renders mood curve bars with varying heights", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    const curveContainer = document.querySelector(".border-b.border-l");
    expect(curveContainer).not.toBeNull();
  });

  it("renders mood labels (引入, 正文, 结尾)", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/引入/)).toBeDefined();
    const bodyTexts = screen.getAllByText(/正文/);
    expect(bodyTexts.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/结尾/)).toBeDefined();
  });

  it("renders BGM track card with Music icon and track name", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/全局配乐混合试听/)).toBeDefined();
    expect(screen.getByText(/Corporate/)).toBeDefined();
  });

  it("renders two-layer waveform in dark player bar", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    const playerBar = document.querySelector(".bg-slate-800");
    expect(playerBar).not.toBeNull();
  });

  it("renders play button and time display", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    const playBtn = screen.getByRole("button", { name: /play/i });
    expect(playBtn).toBeDefined();
    // Time display shows "0:00"
    expect(screen.getByText(/0:00/)).toBeDefined();
  });

  it("renders CC-BY license badge with green styling", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/CC-BY/)).toBeDefined();
    const greenBadge = document.querySelector(".text-green-600.bg-green-100");
    expect(greenBadge).not.toBeNull();
  });

  it("renders Ducking info section", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/Ducking/)).toBeDefined();
  });

  it("renders Review Agent verdict badge and change BGM button", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/Review Agent/)).toBeDefined();
    expect(screen.getByText(/更换配乐/)).toBeDefined();
  });

  it("renders download button for mixed audio", () => {
    render(<P5WaveformPlayer audio_url="https://example.com/mix.wav" />);
    expect(screen.getByText(/下载混音初版/)).toBeDefined();
    expect(screen.getByText(/\.wav/)).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// P6SfxListPlayer
// ---------------------------------------------------------------------------
function makeSfxItems() {
  return [
    { type: "Whoosh", time_sec: 5.0, audio_url: "/sfx/whoosh.wav" },
    { type: "Ding", time_sec: 12.5, audio_url: "/sfx/ding.wav" },
  ];
}

describe("P6SfxListPlayer visual alignment", () => {
  it("renders empty state matching design tokens when sfx_list is empty", () => {
    render(<P6SfxListPlayer sfx_list={[]} />);
    const el = screen.getByTestId("preview-p6");
    expect(el.className).toContain("flex");
    expect(el.className).toContain("flex-col");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("justify-center");
    expect(el.className).toContain("h-64");
    expect(el.className).toContain("text-slate-400");
  });

  it("renders section 1 with SFX annotation text when sfx_list has items", () => {
    render(<P6SfxListPlayer sfx_list={makeSfxItems()} />);
    expect(screen.getByText(/全局音效布局规划/)).toBeDefined();
    expect(screen.getByText(/脚本批注/)).toBeDefined();
  });

  it("renders SFX hover tooltips with highlighted text for each sfx item", () => {
    render(<P6SfxListPlayer sfx_list={makeSfxItems()} />);
    const whooshElements = screen.getAllByText("Whoosh");
    expect(whooshElements.length).toBeGreaterThanOrEqual(1);
    const dingElements = screen.getAllByText("Ding");
    expect(dingElements.length).toBeGreaterThanOrEqual(1);
    const groups = document.querySelectorAll(".group");
    expect(groups.length).toBeGreaterThanOrEqual(2);
  });

  it("renders section 2 with segment mix preview rows", () => {
    render(<P6SfxListPlayer sfx_list={makeSfxItems()} />);
    expect(screen.getByText(/分段带反馈试听/)).toBeDefined();
    expect(screen.getByText(/人声\+BGM\+SFX/)).toBeDefined();
    const playBtns = screen.getAllByRole("button", { name: /play/i });
    expect(playBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("renders download button for composite audio", () => {
    render(<P6SfxListPlayer sfx_list={makeSfxItems()} />);
    expect(screen.getByText(/下载复合音频版/)).toBeDefined();
    expect(screen.getByText(/\.wav/)).toBeDefined();
  });

  it("uses design tokens for the card background", () => {
    render(<P6SfxListPlayer sfx_list={makeSfxItems()} />);
    const cards = document.querySelectorAll(".bg-white.border-2.border-slate-200.rounded-xl");
    expect(cards.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// P7StoryboardGallery
// ---------------------------------------------------------------------------
function makeShots() {
  return [
    { id: "S1E1", description: "开场引入镜头", duration_sec: 8, template_id: "tpl_broll" },
    { id: "S1E2", description: "数据展示画面", duration_sec: 7, template_id: "tpl_chart" },
  ];
}

describe("P7StoryboardGallery visual alignment", () => {
  it("renders empty state with flex-col, items-center, justify-center, h-64 and text-slate-400 when no shots", () => {
    render(<P7StoryboardGallery shots={[]} />);
    const el = screen.getByTestId("preview-p7");
    expect(el.className).toContain("flex");
    expect(el.className).toContain("flex-col");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("justify-center");
    expect(el.className).toContain("h-64");
    expect(el.className).toContain("text-slate-400");
  });

  it("renders timeline layout with border-l-2 border-slate-200 when shots present", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const container = document.querySelector("[class*='border-l-2'][class*='border-slate-200']");
    expect(container).not.toBeNull();
  });

  it("renders timeline dot markers on left border for each shot", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const dots = document.querySelectorAll("[class*='border-\\[3px\\]'][class*='border-blue-500']");
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  it("renders shot cards with bg-white border-2 border-slate-200 rounded-2xl shadow-sm", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const card = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-2xl']");
    expect(card).not.toBeNull();
  });

  it("renders ID badge with bg-[#1e293b] text-white tracking-widest", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const badge = document.querySelector("[class*='bg-\\[\\#1e293b\\]'][class*='text-white']");
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toContain("S1E1");
  });

  it("renders visualType badge with blue or emerald styling", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const badge = document.querySelector("[class*='bg-blue-50'][class*='text-blue-600']");
    const altBadge = document.querySelector("[class*='bg-emerald-50'][class*='text-emerald-600']");
    expect(badge || altBadge).not.toBeNull();
  });

  it("renders description as italic script quote", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const matches = screen.getAllByText(/开场引入镜头/);
    expect(matches.length).toBeGreaterThanOrEqual(1);
    const italic = document.querySelector("[class*='italic']");
    expect(italic).not.toBeNull();
  });

  it("renders action button with modify text per shot", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const modifyBtns = screen.getAllByText(/修改/);
    expect(modifyBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("renders small label headers with 10px uppercase tracking-wider", () => {
    render(<P7StoryboardGallery shots={makeShots()} />);
    const smallLabels = document.querySelectorAll("[class*='text-\\[10px\\]'][class*='uppercase'][class*='tracking-wider']");
    expect(smallLabels.length).toBeGreaterThanOrEqual(2);
  });
});

// ---------------------------------------------------------------------------
// P8FrameGallery
// ---------------------------------------------------------------------------
function makeFrames() {
  return [
    { id: "S1E1", image_url: "/frames/s1e1.png", is_downgraded: true },
    { id: "S2E1", image_url: "/frames/s2e1.png", is_downgraded: false },
  ];
}

describe("P8FrameGallery visual alignment", () => {
  it("renders empty state with flex-col, items-center, justify-center, h-64 and text-slate-400 when no frames", () => {
    render(<P8FrameGallery frames={[]} />);
    const el = screen.getByTestId("preview-p8");
    expect(el.className).toContain("flex");
    expect(el.className).toContain("flex-col");
    expect(el.className).toContain("items-center");
    expect(el.className).toContain("justify-center");
    expect(el.className).toContain("h-64");
    expect(el.className).toContain("text-slate-400");
  });

  it("renders timeline layout with border-l-2 border-slate-200 when frames present", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const container = document.querySelector("[class*='border-l-2'][class*='border-slate-200']");
    expect(container).not.toBeNull();
  });

  it("renders timeline dot markers on left border for each frame", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const dots = document.querySelectorAll("[class*='border-\\[3px\\]'][class*='border-blue-500']");
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  it("renders frame cards with bg-white border-2 border-slate-200 rounded-2xl shadow-sm", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const card = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-2xl']");
    expect(card).not.toBeNull();
  });

  it("renders ID badge with bg-[#1e293b] text-white tracking-widest", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const badge = document.querySelector("[class*='bg-\\[\\#1e293b\\]'][class*='text-white']");
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toContain("S1E1");
  });

  it("renders visualType badge with blue or emerald styling", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const badge = document.querySelector("[class*='bg-blue-50'][class*='text-blue-600']");
    const altBadge = document.querySelector("[class*='bg-emerald-50'][class*='text-emerald-600']");
    expect(badge || altBadge).not.toBeNull();
  });

  it("shows not-needed asset status with CheckCircle2 icon for downgraded frames", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    expect(screen.getByText(/无需额外动态数据源/)).toBeDefined();
  });

  it("shows fetched asset trace with dark code block for non-downgraded frames", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const codeBlock = document.querySelector("[class*='bg-\\[\\#1e293b\\]'][class*='text-emerald-400'][class*='font-mono']");
    expect(codeBlock).not.toBeNull();
  });

  it("shows Verified badge with green styling for fetched items", () => {
    render(<P8FrameGallery frames={makeFrames()} />);
    const verifiedBadge = document.querySelector("[class*='text-green-700'][class*='bg-green-100']");
    expect(verifiedBadge).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// P9BrollGallery
// ---------------------------------------------------------------------------
describe("P9BrollGallery visual alignment", () => {
  const renderedBroll: BrollItem = {
    id: "S1E2",
    thumbnail_url: "https://example.com/thumb.jpg",
    source: "B-Roll",
    is_placeholder: false,
  };

  const pendingBroll: BrollItem = {
    id: "S1E1",
    thumbnail_url: "",
    source: "B-Roll",
    is_placeholder: true,
  };

  it("shows empty state with flex-col, items-center, justify-center, h-64 and text-slate-400 when no brolls", () => {
    render(<P9BrollGallery brolls={[]} />);
    const el = screen.getByTestId("preview-p9");
    expect(el.className).toMatch(/flex/);
    expect(el.className).toMatch(/flex-col/);
    expect(el.className).toMatch(/items-center/);
    expect(el.className).toMatch(/justify-center/);
    expect(el.className).toMatch(/h-64/);
    expect(el.className).toMatch(/text-slate-400/);
  });

  it("renders timeline layout with border-l-2 border-slate-200 when brolls present", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const timeline = document.querySelector("[class*='border-l-2'][class*='border-slate-200']");
    expect(timeline).not.toBeNull();
  });

  it("renders timeline dot markers on left border for each shot", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const dots = document.querySelectorAll("[class*='border-\\[3px\\]'][class*='border-blue-500']");
    expect(dots.length).toBeGreaterThanOrEqual(1);
  });

  it("renders card with bg-white border-2 border-slate-200 rounded-2xl shadow-sm", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const card = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-2xl']");
    expect(card).not.toBeNull();
  });

  it("renders ID badge with bg-[#1e293b] text-white font-bold", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const badge = document.querySelector("[class*='bg-\\[\\#1e293b\\]'][class*='text-white']");
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toContain("S1E2");
  });

  it("renders source text as visual description", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    expect(screen.getByText("B-Roll")).toBeDefined();
  });

  it("shows rendered status badge with green styling for non-placeholder items", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const greenBadge = document.querySelector("[class*='text-green-700'][class*='bg-green-100']");
    expect(greenBadge).not.toBeNull();
  });

  it("shows awaiting status badge with amber styling for placeholder items", () => {
    render(<P9BrollGallery brolls={[pendingBroll]} />);
    const amberBadge = document.querySelector("[class*='text-amber-700'][class*='bg-amber-50']");
    expect(amberBadge).not.toBeNull();
  });

  it("renders video placeholder area with bg-slate-50 for each shot", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const placeholderArea = document.querySelector("[class*='bg-slate-50']");
    expect(placeholderArea).not.toBeNull();
  });

  it("shows play overlay with backdrop-blur for rendered shots", () => {
    render(<P9BrollGallery brolls={[renderedBroll]} />);
    const overlay = document.querySelector("[class*='backdrop-blur']");
    expect(overlay).not.toBeNull();
  });

  it("shows waiting message for pending shots", () => {
    render(<P9BrollGallery brolls={[pendingBroll]} />);
    expect(screen.getByText(/等待/)).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// P10VideoPlayer
// ---------------------------------------------------------------------------
describe("P10VideoPlayer visual alignment", () => {
  it("shows empty/awaiting state with centered layout when no video_url", () => {
    render(<P10VideoPlayer />);
    const el = screen.getByTestId("preview-p10");
    expect(el).toBeDefined();
  });

  it("renders B-Roll list items with Video icon when no video_url is provided", () => {
    render(<P10VideoPlayer />);
    const videoIcons = document.querySelectorAll(".lucide-video");
    expect(videoIcons.length).toBeGreaterThan(0);
  });

  it("renders thumbnail placeholder with bg-slate-200 rounded-lg", () => {
    render(<P10VideoPlayer />);
    const thumb = document.querySelector("[class*='bg-slate-200'][class*='rounded-lg']");
    expect(thumb).not.toBeNull();
  });

  it("renders license badge with text-green-600 bg-green-50 uppercase", () => {
    render(<P10VideoPlayer />);
    const licenseBadge = document.querySelector("[class*='text-green-600'][class*='bg-green-50'][class*='uppercase']");
    expect(licenseBadge).not.toBeNull();
  });

  it("renders duration badge", () => {
    render(<P10VideoPlayer />);
    const durationBadge = document.querySelector("[class*='bg-slate-100'][class*='rounded']");
    expect(durationBadge).not.toBeNull();
  });

  it("renders coverage summary text", () => {
    render(<P10VideoPlayer />);
    expect(screen.getByText(/覆盖/)).toBeDefined();
  });

  it("renders broll card with bg-white border-2 border-slate-200 rounded-xl", () => {
    render(<P10VideoPlayer />);
    const card = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-xl']");
    expect(card).not.toBeNull();
  });

  it("renders video player with play button when video_url is provided", () => {
    render(<P10VideoPlayer video_url="https://example.com/video.mp4" />);
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// P11FinalPlayer
// ---------------------------------------------------------------------------
describe("P11FinalPlayer visual alignment", () => {
  it("renders completion green checkmark circle w-16 h-16 bg-green-100 rounded-full", () => {
    render(<P11FinalPlayer />);
    const circle = document.querySelector("[class*='bg-green-100'][class*='rounded-full']");
    expect(circle).not.toBeNull();
  });

  it("renders completion heading with Chinese text", () => {
    render(<P11FinalPlayer />);
    expect(screen.getByText(/完成/)).toBeDefined();
  });

  it("renders platform download buttons in a 2-column grid", () => {
    render(<P11FinalPlayer />);
    const grid = document.querySelector("[class*='grid-cols-2']");
    expect(grid).not.toBeNull();
  });

  it("renders B站 download button card with bg-white border-2 border-slate-200 rounded-xl", () => {
    render(<P11FinalPlayer />);
    const card = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-xl']");
    expect(card).not.toBeNull();
  });

  it("renders download icon in platform buttons", () => {
    render(<P11FinalPlayer />);
    const downloadIcons = document.querySelectorAll(".lucide-download");
    expect(downloadIcons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders B站 version text and 抖音 version text", () => {
    render(<P11FinalPlayer />);
    expect(screen.getByText(/B\s*站/)).toBeDefined();
    expect(screen.getByText(/抖音/)).toBeDefined();
  });

  it("renders video spec info (1080P, H.264, 竖屏, 1080x1920)", () => {
    render(<P11FinalPlayer />);
    expect(screen.getByText(/1080P/)).toBeDefined();
    expect(screen.getByText(/H\.264/)).toBeDefined();
    expect(screen.getByText(/竖屏/)).toBeDefined();
    expect(screen.getByText(/1080x1920/)).toBeDefined();
  });

  it("renders SRT subtitle row with 字幕 text", () => {
    render(<P11FinalPlayer />);
    expect(screen.getByText(/字幕/)).toBeDefined();
    expect(screen.getByText(/SRT/)).toBeDefined();
  });

  it("renders SRT row with bg-white border-2 border-slate-200 rounded-xl shadow-sm", () => {
    render(<P11FinalPlayer />);
    const srtRow = document.querySelector("[class*='bg-white'][class*='border-2'][class*='border-slate-200'][class*='rounded-xl'][class*='shadow-sm']");
    expect(srtRow).not.toBeNull();
  });

  it("renders video player when video_url is provided", () => {
    render(<P11FinalPlayer video_url="https://example.com/final.mp4" />);
    const video = document.querySelector("video");
    expect(video).not.toBeNull();
  });

  it("shows no-video placeholder when video_url is not provided", () => {
    render(<P11FinalPlayer />);
    expect(screen.getByText(/无视频/)).toBeDefined();
  });
});
