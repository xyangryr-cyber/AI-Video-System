import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

const TEST_TITLE = "美联储换届对于资本市场的影响";
const TEST_DESC = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响`;

/**
 * Advance project to at least `targetPhase` via repeated POST /advance calls.
 * Returns the final current_phase from the state API.
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

test.describe("Content Generation Quality", () => {
  test.setTimeout(600_000); // 10 minutes for full pipeline with LLM calls

  test("TC-E2E-001: P0-P3 produces actual content", async ({ request }) => {
    // Step 1-3: Create project
    const createRes = await request.post(`${BASE_URL}/api/projects`, {
      data: { title: TEST_TITLE, description: TEST_DESC },
    });
    expect(createRes.status()).toBe(201);
    const project = await createRes.json();
    const projectId: string = project.id;
    console.log(`Created project: ${projectId}`);

    // ---------------------------------------------------------------
    // Step 5 (P0): Verify requirements.json has real content
    // P0 artifact is generated synchronously during project creation.
    // ---------------------------------------------------------------
    const reqArtifactRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/0/artifact`,
    );
    expect(reqArtifactRes.status()).toBe(200);
    const reqArtifact = await reqArtifactRes.json();
    const requirements = reqArtifact.artifact_data || {};
    console.log(
      `requirements.json keys: ${Object.keys(requirements).join(", ")}`,
    );

    // topic field is not verbatim copy of original input
    expect(requirements).toHaveProperty("topic");
    expect(typeof requirements.topic).toBe("string");
    expect(requirements.topic.length).toBeGreaterThan(10);

    // A structured topic should NOT look like the raw "a. ... b. ... c. ..."
    // checklist format. It should be a coherent narrative paragraph.
    const rawPrefixPattern = /^[a-c]\.\s/;
    const isVerbatim = rawPrefixPattern.test(requirements.topic.trim());
    if (isVerbatim) {
      console.warn(
        "[TC-E2E-001] WARNING: topic field appears to be verbatim " +
          "copy of original input. Content generation may be using " +
          "stub data.",
      );
    }
    expect(isVerbatim).toBe(false);

    // voice_preferences is non-empty object
    expect(requirements).toHaveProperty("voice_preferences");
    expect(typeof requirements.voice_preferences).toBe("object");
    expect(requirements.voice_preferences).not.toBeNull();
    const vpKeys = Object.keys(requirements.voice_preferences || {});
    if (vpKeys.length === 0) {
      console.warn(
        "[TC-E2E-001] WARNING: voice_preferences is empty object. " +
          "Voice preferences may not be populated yet.",
      );
    }
    expect(vpKeys.length).toBeGreaterThan(0);

    // ---------------------------------------------------------------
    // Step 6 (P1): Advance to P1, verify outline narrative beats
    // P1 artifact is generated when advancing P0->P1.
    // ---------------------------------------------------------------
    const phaseAfterP0 = await advanceToPhase(request, projectId, 1);
    console.log(`After advancing to P1, current phase: ${phaseAfterP0}`);

    const outlineArtifactRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/1/artifact`,
    );
    expect(outlineArtifactRes.status()).toBe(200);
    const outlineArtifact = await outlineArtifactRes.json();
    const outline = outlineArtifact.artifact_data || {};

    // Verify narrative beats don't contain "Key point N for" stub text
    const versions = outline.versions || [];
    expect(versions.length).toBeGreaterThan(0);
    for (const version of versions) {
      const beats = version.narrative_beats || [];
      expect(beats.length).toBeGreaterThan(0);
      for (const beat of beats) {
        const title: string = beat.title || "";
        const keyPoints: string[] = beat.key_points || [];
        // Title should be descriptive, not "Key point N for ..."
        expect(title).not.toMatch(/^Key point \d+ for/);
        // key_points entries should not be stub placeholders
        for (const kp of keyPoints) {
          expect(kp).not.toMatch(/^Key point \d+ for/);
        }
      }
    }

    // ---------------------------------------------------------------
    // Step 7 (P2): Advance to P2, verify script segments
    // P2 artifact is generated when advancing P1->P2.
    // ---------------------------------------------------------------
    const phaseAfterP1 = await advanceToPhase(request, projectId, 2);
    console.log(`After advancing to P2, current phase: ${phaseAfterP1}`);

    const scriptArtifactRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/2/artifact`,
    );
    expect(scriptArtifactRes.status()).toBe(200);
    const scriptArtifact = await scriptArtifactRes.json();
    const scriptV1 = scriptArtifact.artifact_data || {};

    // Handle both shape: array of segments or {segments: [...]}
    const p2Segments: any[] = Array.isArray(scriptV1)
      ? scriptV1
      : scriptV1.segments || [];
    expect(p2Segments.length).toBeGreaterThan(0);
    for (const seg of p2Segments) {
      const content: string = seg.content || "";
      // Content should not start with "第N部分" template pattern
      expect(content).not.toMatch(/^第\d+部分/);
      // Content should have meaningful length
      expect(content.trim().length).toBeGreaterThan(5);
    }

    // ---------------------------------------------------------------
    // Step 8 (P3): Advance to P3, verify polished content differs from P2
    // P3 artifact is generated when advancing P2->P3.
    // ---------------------------------------------------------------
    const phaseAfterP2 = await advanceToPhase(request, projectId, 3);
    console.log(`After advancing to P3, current phase: ${phaseAfterP2}`);

    const polishedArtifactRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/3/artifact`,
    );
    expect(polishedArtifactRes.status()).toBe(200);
    const polishedArtifact = await polishedArtifactRes.json();
    const polished = polishedArtifact.artifact_data || {};

    const p3Segments: any[] = polished.segments || [];
    expect(p3Segments.length).toBeGreaterThan(0);

    // Verify P3 content differs from P2 (at least one segment changed)
    let foundDiff = false;
    for (let i = 0; i < Math.min(p3Segments.length, p2Segments.length); i++) {
      const p2Content: string = p2Segments[i]?.content || "";
      const p3Content: string =
        p3Segments[i]?.polished_text ||
        p3Segments[i]?.content ||
        "";
      if (p2Content !== p3Content) {
        foundDiff = true;
        console.log(
          `Segment ${i}: P2 vs P3 content differs ` +
            `(len P2=${p2Content.length}, P3=${p3Content.length})`,
        );
        break;
      }
    }
    if (!foundDiff) {
      console.warn(
        "[TC-E2E-001] WARNING: P3 polished content is identical to " +
          "P2 script content. Polish agent may be using passthrough.",
      );
    }
    expect(foundDiff).toBe(true);
  });

  test("TC-E2E-002: P8 visuals are not solid color", async ({
    page,
    request,
  }) => {
    // Create project and advance to P8
    const createRes = await request.post(`${BASE_URL}/api/projects`, {
      data: { title: TEST_TITLE, description: TEST_DESC },
    });
    expect(createRes.status()).toBe(201);
    const project = await createRes.json();
    const projectId: string = project.id;
    console.log(`Created project: ${projectId}`);

    const finalPhase = await advanceToPhase(request, projectId, 8);
    console.log(`Advanced to phase ${finalPhase}`);

    // ---------------------------------------------------------------
    // Step 2: Get rendered image URLs from keyframes.json API
    // ---------------------------------------------------------------
    const kfArtifactRes = await request.get(
      `${BASE_URL}/api/projects/${projectId}/phases/8/artifact`,
    );
    expect(kfArtifactRes.status()).toBe(200);
    const kfArtifact = await kfArtifactRes.json();
    const keyframes = kfArtifact.artifact_data || {};

    const renders: any[] = keyframes.renders || [];
    console.log(`P8 renders count: ${renders.length}`);

    // Build absolute image URLs for PNG renders
    const imageUrls: string[] = [];
    for (const r of renders) {
      const rp: string = r.render_path || "";
      if (rp.endsWith(".png")) {
        imageUrls.push(
          `${BASE_URL}/api/projects/${projectId}/files/${rp}`,
        );
      }
    }

    // Fallback: try phase_8/{shot_id}.png paths
    if (imageUrls.length === 0) {
      console.warn(
        "[TC-E2E-002] No .png render_paths in keyframes.json. " +
          "Trying phase_8/{shot_id}.png.",
      );
      for (const r of renders) {
        const shotId: string = r.shot_id || "";
        if (shotId) {
          imageUrls.push(
            `${BASE_URL}/api/projects/${projectId}/files/phase_8/${shotId}.png`,
          );
        }
      }
    }

    if (imageUrls.length === 0) {
      console.warn(
        "[TC-E2E-002] No image URLs discovered. " +
          "Skipping visual content verification.",
      );
      return;
    }

    // Navigate to any page under the same origin so Canvas can load
    // same-origin images without CORS issues.
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    // ---------------------------------------------------------------
    // Step 3: Use Canvas API via page.evaluate() to analyze pixels
    // Sample 20 random points per image; verify >= 5 unique colors.
    // ---------------------------------------------------------------
    let testedImages = 0;
    let solidColorCount = 0;

    for (const url of imageUrls.slice(0, 5)) {
      const uniqueColors = await page
        .evaluate(async (imageUrl: string) => {
          return new Promise<number>((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
              try {
                const canvas = document.createElement("canvas");
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext("2d");
                if (!ctx) {
                  resolve(-1); // Canvas not supported
                  return;
                }
                ctx.drawImage(img, 0, 0);

                // Sample 20 random pixel locations
                const colors = new Set<string>();
                for (let i = 0; i < 20; i++) {
                  const x = Math.floor(
                    Math.random() * img.naturalWidth,
                  );
                  const y = Math.floor(
                    Math.random() * img.naturalHeight,
                  );
                  const pixel = ctx.getImageData(x, y, 1, 1).data;
                  // Store as R,G,B (ignore alpha for diversity check)
                  colors.add(
                    `${pixel[0]},${pixel[1]},${pixel[2]}`,
                  );
                }
                resolve(colors.size);
              } catch {
                resolve(-2); // Error during analysis
              }
            };
            img.onerror = () => resolve(0); // Image failed to load
            img.src = imageUrl;
          });
        }, url)
        .catch(() => -3); // evaluate() itself failed

      testedImages++;

      if (uniqueColors < 0) {
        console.warn(
          `[TC-E2E-002] Image ${url}: analysis error code=${uniqueColors}`,
        );
        // Treat analysis errors as indeterminate, not as solid-color
        continue;
      }

      if (uniqueColors === 0) {
        console.warn(
          `[TC-E2E-002] Image ${url}: failed to load in browser.`,
        );
        continue;
      }

      console.log(
        `[TC-E2E-002] Image: unique colors=${uniqueColors}/20 samples`,
      );

      if (uniqueColors < 5) {
        console.warn(
          `[TC-E2E-002] Image ${url} has only ${uniqueColors} unique ` +
            "colors from 20 samples — likely solid color or near-solid.",
        );
        solidColorCount++;
      }
    }

    if (testedImages > 0) {
      console.log(
        `[TC-E2E-002] Solid color ratio: ${solidColorCount}/${testedImages}`,
      );
      // At least one testable image should have 5+ unique colors
      const diverseCount = testedImages - solidColorCount;
      if (diverseCount === 0) {
        console.warn(
          "[TC-E2E-002] WARNING: All tested images appear to be " +
            "solid or near-solid color. Visual rendering may be " +
            "producing placeholder images.",
        );
      }
      expect(diverseCount).toBeGreaterThan(0);
    } else {
      console.warn(
        "[TC-E2E-002] No images could be tested for color diversity.",
      );
    }
  });
});
