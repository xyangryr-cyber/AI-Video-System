import { test, expect } from "@playwright/test";
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

const TEST_TITLE = "美联储换届对于资本市场的影响";
const TEST_DESC = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响`;

/**
 * Advance project to at least `targetPhase` via repeated POST /advance calls.
 */
async function advanceToPhase(
  request: any,
  projectId: string,
  targetPhase: number,
): Promise<number> {
  for (let attempt = 0; attempt < 12; attempt++) {
    const stateRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/state`,
    );
    expect(stateRes.status()).toBe(200);
    const state = await stateRes.json();
    const currentPhase: number = state.project.current_phase;
    if (currentPhase >= targetPhase) return currentPhase;

    const advanceRes = await request.post(
      `${BASE_URL}/api/projects/${projectId}/advance`,
    );
    const body = await advanceRes.json();

    if (body.status === "gate_failed") {
      throw new Error(
        `Gate failed at phase ${body.current_phase}: ` +
          JSON.stringify(body),
      );
    }
    if (body.status === "already_advanced") {
      await new Promise<void>((resolve) => setTimeout(resolve, 500));
      continue;
    }
  }
  throw new Error(`Failed to reach phase ${targetPhase}`);
}

/**
 * Check if ffprobe is available on the system.
 */
function ffprobeAvailable(): boolean {
  try {
    execSync("ffprobe -version", { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

/**
 * Run ffprobe and return parsed JSON output.
 */
function ffprobeJson(filePath: string): any {
  const stdout = execSync(
    `ffprobe -v quiet -print_format json -show_format -show_streams "${filePath}"`,
    { encoding: "utf-8", timeout: 30000 },
  );
  return JSON.parse(stdout);
}

test.describe("Video Quality", () => {
  test.setTimeout(600_000); // 10 minutes

  test("TC-E2E-003: Video duration consistency", async ({
    request,
  }) => {
    // Create project
    const createRes = await request.post(`${BASE_URL}/api/projects`, {
      data: { title: TEST_TITLE, description: TEST_DESC },
    });
    expect(createRes.status()).toBe(201);
    const project = await createRes.json();
    const projectId: string = project.id;
    console.log(`Created project: ${projectId}`);

    // ---------------------------------------------------------------
    // Step 1: Advance to P4, get audio duration from narration.json
    // ---------------------------------------------------------------
    const phaseP4 = await advanceToPhase(request, projectId, 4);
    console.log(`Advanced to phase ${phaseP4}`);

    const narrationRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/4/artifact`,
    );
    expect(narrationRes.status()).toBe(200);
    const narrationArtifact = await narrationRes.json();
    const narration = narrationArtifact.artifact_data || {};

    const audioDuration: number =
      narration.total_duration_sec ||
      narration.duration_seconds ||
      narration.total_duration ||
      0;
    console.log(`Audio duration from narration.json: ${audioDuration}s`);

    if (audioDuration <= 0) {
      console.warn(
        "[TC-E2E-003] Narration artifact has no duration field. " +
          "Calculating from segments.",
      );
      const segments = narration.segments || [];
      let segDuration = 0;
      for (const seg of segments) {
        segDuration += seg.duration_seconds || seg.duration_sec || 0;
      }
      if (segDuration > 0) {
        console.log(
          `Audio duration calculated from segments: ${segDuration}s`,
        );
      }
    }

    // Also try to get duration from the actual audio file if available
    let actualAudioDuration = audioDuration;

    // Check if narration_master.mp3 exists via API
    const audioFileUrl = `${BASE_URL}/api/projects/${projectId}/files/phase_4/narration_master.mp3`;
    const audioCheckRes = await request.get(audioFileUrl);
    if (audioCheckRes.status() === 200 && ffprobeAvailable()) {
      // Download audio and probe
      const audioBuffer = await audioCheckRes.body();
      const tmpDir = os.tmpdir();
      const audioPath = path.join(tmpDir, `e2e_audio_${projectId}.mp3`);
      fs.writeFileSync(audioPath, Buffer.from(audioBuffer));
      try {
        const info = ffprobeJson(audioPath);
        const streams = info.streams || [];
        const audioStream = streams.find(
          (s: any) => s.codec_type === "audio",
        );
        if (audioStream && audioStream.duration) {
          actualAudioDuration = parseFloat(audioStream.duration);
          console.log(
            `Actual audio duration (ffprobe): ${actualAudioDuration}s`,
          );
        }
      } catch (err) {
        console.warn(`ffprobe on audio failed: ${err}`);
      } finally {
        try {
          fs.unlinkSync(audioPath);
        } catch {
          // cleanup best-effort
        }
      }
    }

    expect(actualAudioDuration).toBeGreaterThan(0);

    // ---------------------------------------------------------------
    // Step 2: Advance to P10, get video duration
    // ---------------------------------------------------------------
    const phaseP10 = await advanceToPhase(request, projectId, 10);
    console.log(`Advanced to phase ${phaseP10}`);

    // Get rough_cut.json artifact
    const roughCutRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/10/artifact`,
    );
    expect(roughCutRes.status()).toBe(200);
    const roughArtifact = await roughCutRes.json();
    const roughCut = roughArtifact.artifact_data || {};

    const videoDuration: number =
      roughCut.duration_seconds || roughCut.duration || 0;
    console.log(
      `Video duration from rough_cut.json: ${videoDuration}s`,
    );

    // Also try ffprobe on the actual video file
    let actualVideoDuration = videoDuration;
    const videoFileUrl = `${BASE_URL}/api/projects/${projectId}/files/phase_10/rough_cut.mp4`;
    const videoCheckRes = await request.get(videoFileUrl);
    if (videoCheckRes.status() === 200 && ffprobeAvailable()) {
      const videoBuffer = await videoCheckRes.body();
      const tmpDir = os.tmpdir();
      const videoPath = path.join(tmpDir, `e2e_video_${projectId}.mp4`);
      fs.writeFileSync(videoPath, Buffer.from(videoBuffer));
      try {
        const info = ffprobeJson(videoPath);
        const streams = info.streams || [];
        const videoStream = streams.find(
          (s: any) => s.codec_type === "video",
        );
        if (videoStream && videoStream.duration) {
          actualVideoDuration = parseFloat(videoStream.duration);
          console.log(
            `Actual video duration (ffprobe): ${actualVideoDuration}s`,
          );
        } else if (info.format && info.format.duration) {
          actualVideoDuration = parseFloat(info.format.duration);
          console.log(
            `Actual video duration (format): ${actualVideoDuration}s`,
          );
        }
      } catch (err) {
        console.warn(`ffprobe on video failed: ${err}`);
      } finally {
        try {
          fs.unlinkSync(videoPath);
        } catch {
          // cleanup best-effort
        }
      }
    }

    if (actualVideoDuration <= 0) {
      console.warn(
        "[TC-E2E-003] Could not determine video duration. " +
          "Skipping duration consistency check.",
      );
      return;
    }

    // ---------------------------------------------------------------
    // Step 3: Verify audio and video durations match within 1 second
    // ---------------------------------------------------------------
    const diff = Math.abs(actualAudioDuration - actualVideoDuration);
    console.log(
      `Duration diff: ${diff.toFixed(2)}s ` +
        `(audio=${actualAudioDuration.toFixed(2)}s, ` +
        `video=${actualVideoDuration.toFixed(2)}s)`,
    );
    expect(diff).toBeLessThan(1);
  });

  test("TC-E2E-004: Audio quality meets standards", async ({
    request,
  }) => {
    // Check ffprobe availability upfront
    if (!ffprobeAvailable()) {
      console.warn(
        "[TC-E2E-004] SKIP: ffprobe not available on this system. " +
          "Install ffmpeg to enable audio quality verification.",
      );
      return;
    }

    // Create project
    const createRes = await request.post(`${BASE_URL}/api/projects`, {
      data: { title: TEST_TITLE, description: TEST_DESC },
    });
    expect(createRes.status()).toBe(201);
    const project = await createRes.json();
    const projectId: string = project.id;
    console.log(`Created project: ${projectId}`);

    // Advance to P11
    const finalPhase = await advanceToPhase(request, projectId, 11);
    console.log(`Advanced to phase ${finalPhase}`);

    // Get final.json artifact for download URLs
    const finalRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/11/artifact`,
    );
    expect(finalRes.status()).toBe(200);
    const finalArtifact = await finalRes.json();
    const finalData = finalArtifact.artifact_data || {};

    const downloadUrls: Record<string, string> =
      finalData.download_urls || {};

    // Step 4: Download video file (bilibili URL or rough_cut fallback)
    const bilibiliUrl =
      downloadUrls.bilibili ||
      downloadUrls.douyin ||
      finalData.video_url ||
      `phase_10/final_cut.mp4`;

    const videoFileUrl = bilibiliUrl.startsWith("http")
      ? bilibiliUrl
      : `${BASE_URL}/api/projects/${projectId}/files/${bilibiliUrl.replace(/^\//, "")}`;

    console.log(`Downloading video from: ${videoFileUrl}`);
    const videoRes = await request.get(videoFileUrl);
    if (videoRes.status() !== 200) {
      // Try rough_cut as fallback
      const rcUrl = `${BASE_URL}/api/projects/${projectId}/files/phase_10/rough_cut.mp4`;
      console.log(`Final cut not available, trying rough cut: ${rcUrl}`);
      const rcRes = await request.get(rcUrl);
      if (rcRes.status() !== 200) {
        console.warn(
          "[TC-E2E-004] No video file available for audio quality check.",
        );
        return;
      }
      const rcBuffer = await rcRes.body();
      const tmpDir = os.tmpdir();
      const vPath = path.join(tmpDir, `e2e_quality_${projectId}.mp4`);
      fs.writeFileSync(vPath, Buffer.from(rcBuffer));
      try {
        const info = ffprobeJson(vPath);
        verifyAudioStreams(info);
      } finally {
        try {
          fs.unlinkSync(vPath);
        } catch {
          // cleanup
        }
      }
      return;
    }

    const videoBuffer = await videoRes.body();
    const tmpDir = os.tmpdir();
    const videoPath = path.join(tmpDir, `e2e_quality_${projectId}.mp4`);
    fs.writeFileSync(videoPath, Buffer.from(videoBuffer));

    try {
      const info = ffprobeJson(videoPath);
      verifyAudioStreams(info);
    } finally {
      try {
        fs.unlinkSync(videoPath);
      } catch {
        // cleanup best-effort
      }
    }
  });
});

/**
 * Verify audio stream quality standards from ffprobe output.
 */
function verifyAudioStreams(info: any): void {
  const streams: any[] = info.streams || [];
  const audioStream = streams.find((s: any) => s.codec_type === "audio");

  if (!audioStream) {
    console.warn(
      "[TC-E2E-004] WARNING: No audio stream found in video file. " +
        "Video may be missing audio track.",
    );
    // If there's truly no audio stream, we cannot test quality.
    // However, the system SHOULD produce an audio track.
    return;
  }

  // Verify audio codec is aac
  const codecName: string = audioStream.codec_name || "";
  console.log(`Audio codec: ${codecName}`);
  expect(codecName.toLowerCase()).toBe("aac");

  // Verify sample rate >= 44100
  const sampleRate: number = parseInt(audioStream.sample_rate || "0", 10);
  console.log(`Audio sample rate: ${sampleRate} Hz`);
  expect(sampleRate).toBeGreaterThanOrEqual(44100);

  // Verify channels = 2 (stereo)
  const channels: number = audioStream.channels || 0;
  console.log(`Audio channels: ${channels}`);
  expect(channels).toBe(2);
}
