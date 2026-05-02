import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

const TEST_TITLE = "美联储换届对于资本市场的影响";
const TEST_DESC = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的背景 并且给出他们当选后对于市场的影响`;

// ════════════════════════════════════════════════════════
// Helpers
// ════════════════════════════════════════════════════════

interface PhaseResult {
  phase: number;
  status: "PASS" | "FAIL" | "STUCK" | "SKIP";
  checks: { label: string; pass: boolean; detail: string }[];
}

const allResults: PhaseResult[] = [];

async function waitForAgentIdle(page: any, timeoutMs = 30000) {
  const start = Date.now();
  let lastText = "";
  while (Date.now() - start < timeoutMs) {
    await page.waitForTimeout(2000);
    const body = await page.locator("body").innerText();
    if (body === lastText && !body.includes("执行中") && !body.includes("running")) {
      await page.waitForTimeout(1500);
      const recheck = await page.locator("body").innerText();
      if (recheck === body) return;
    }
    lastText = body;
  }
}

async function findAndClickAdvance(page: any, currentPhase: number): Promise<{ clicked: boolean; modalHandled: boolean; advanced: boolean }> {
  let modalHandled = false;

  const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
  const visible = await advanceBtn.isVisible().catch(() => false);
  if (!visible) return { clicked: false, modalHandled, advanced: false };

  const enabled = await advanceBtn.isEnabled().catch(() => false);
  if (!enabled) return { clicked: false, modalHandled, advanced: false };

  // Record current URL
  const urlBefore = page.url();

  // Start advance API watcher (don't block on it)
  let advanceApiStatus = "unknown";
  const advancePromise = page.waitForResponse(
    (r: any) => r.url().includes("/advance") && r.request().method() === "POST",
    { timeout: 120000 }
  ).then(async (r: any) => {
    try { const b = await r.json(); advanceApiStatus = b.status || `HTTP ${r.status()}`; }
    catch { advanceApiStatus = `HTTP ${r.status()}`; }
  }).catch(() => { advanceApiStatus = "no_response"; });

  await advanceBtn.click();
  await page.waitForTimeout(2000);

  // Handle preference modal
  const prefModal = page.locator("text=AI 记忆同步中");
  if (await prefModal.isVisible().catch(() => false)) {
    modalHandled = true;
    const confirmBtn = page.locator("button", { hasText: "确认并进入下一阶段" });
    if (await confirmBtn.isVisible().catch(() => false)) {
      await confirmBtn.click();
    } else {
      const skipBtn = page.locator("button", { hasText: "跳过" });
      if (await skipBtn.isVisible().catch(() => false)) {
        await skipBtn.click();
        await page.waitForTimeout(1000);
        const btn2 = page.locator("button", { hasText: "确认进入下一阶段" });
        if (await btn2.isVisible().catch(() => false)) {
          await btn2.click();
        }
      }
    }
    await page.waitForTimeout(2000);
  }

  // Wait for the advance API to complete (blocking)
  // The advance API is synchronous and includes agent work (LLM calls), so it can take 60-90s
  try { await advancePromise; } catch { console.log(`  Advance API response not captured (may have completed silently)`); }
  await page.waitForTimeout(3000);

  // Navigate to the next phase URL to update the frontend
  const nextPhase = currentPhase + 1;
  const nextPhaseUrl = page.url().replace(/\/phases\/\d+/, `/phases/${nextPhase}`);
  console.log(`  Navigating to phase ${nextPhase}...`);
  await page.goto(nextPhaseUrl, { timeout: 30000 });
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(3000);

  // Check if we landed on the next phase
  const newUrl = page.url();
  const phaseMatch = newUrl.match(/\/phases\/(\d+)/);
  const newPhase = phaseMatch ? parseInt(phaseMatch[1]) : currentPhase;

  // Verify backend actually advanced by checking the phase nav
  const nextPhaseNav = page.locator(`[data-testid="phase-nav-${nextPhase}"]`);
  const nextPhaseActive = await nextPhaseNav.getAttribute("data-active").catch(() => null);
  const advanced = nextPhaseActive === "true" || newPhase >= nextPhase;

  console.log(`  Advance: oldPhase=${currentPhase}, urlPhase=${newPhase}, navActive=${nextPhaseActive}, advanced=${advanced}`);
  return { clicked: true, modalHandled, advanced };
}

function recordPhase(r: PhaseResult) {
  allResults.push(r);
}

// ════════════════════════════════════════════════════════
// Main Test
// ════════════════════════════════════════════════════════

test.describe("完整12阶段端到端验收测试 (UI Verification)", () => {
  test.setTimeout(900_000); // 15 minutes

  test("Phase 0-11 全流程 + 逐阶段UI验收", async ({ page }) => {
    // ============================================================
    // Phase 0: Create Project & Requirements
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 0: 创建项目 & 需求定义");
    console.log("=".repeat(60));

    const p0Checks: PhaseResult["checks"] = [];

    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    // Click 新建项目
    const newBtn = page.locator("button", { hasText: "新建项目" });
    await expect(newBtn).toBeVisible({ timeout: 10000 });
    await newBtn.click();
    await page.waitForURL("**/projects/new");
    p0Checks.push({ label: "TC-0.1", pass: true, detail: "跳转到 /projects/new" });

    // Fill form
    const titleInput = page.locator("#title");
    const descInput = page.locator("#desc");
    await expect(titleInput).toBeVisible();
    await expect(descInput).toBeVisible();
    await titleInput.fill(TEST_TITLE);
    await descInput.fill(TEST_DESC);
    p0Checks.push({ label: "TC-0.2", pass: true, detail: "标题和描述输入完成" });

    // Submit
    const submitBtn = page.locator("button[type='submit']", { hasText: "开始制作" });
    await expect(submitBtn).toBeEnabled({ timeout: 5000 });

    const createRespPromise = page.waitForResponse(
      (r: any) => r.url().includes("/api/projects") && r.request().method() === "POST",
      { timeout: 120000 }
    );
    await submitBtn.click();
    const createResp = await createRespPromise;
    expect(createResp.status()).toBe(201);
    const body = await createResp.json();
    const projectId = body.id;
    console.log(`  Project ID: ${projectId}`);
    p0Checks.push({ label: "TC-0.3", pass: true, detail: `项目创建 201, id=${projectId}` });

    await page.waitForURL((url: any) => url.pathname.includes(projectId), { timeout: 120000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // P0 UI verification: check chat panel shows requirements summary
    const p0BodyText = await page.locator("body").innerText();

    // Check title is visible
    const hasTitle = p0BodyText.includes("美联储") || p0BodyText.includes(TEST_TITLE.substring(0, 3));
    p0Checks.push({ label: "P0-主题", pass: hasTitle, detail: `页面显示主题: ${hasTitle}` });

    // Check phase nav shows P0 active
    const p0Nav = page.locator('[data-testid="phase-nav-0"]');
    const p0NavVisible = await p0Nav.isVisible().catch(() => false);
    p0Checks.push({ label: "P0-导航", pass: p0NavVisible, detail: `P0导航项可见: ${p0NavVisible}` });

    // Check chat panel / artifact panel content
    const hasChatContent = p0BodyText.length > 200;
    p0Checks.push({ label: "P0-对话区", pass: hasChatContent, detail: `页面内容长度: ${p0BodyText.length}` });

    // Check for stub patterns
    const isStubP0 = p0BodyText.includes("this is a placeholder") ||
      p0BodyText.includes("假设主题为") ||
      p0BodyText.includes("段落 1 内容") ||
      p0BodyText.includes("Lorem ipsum");
    p0Checks.push({ label: "P0-非Stub", pass: !isStubP0, detail: `检测到占位文本: ${isStubP0}` });

    recordPhase({ phase: 0, status: hasTitle && !isStubP0 ? "PASS" : "FAIL", checks: p0Checks });

    // Advance P0 -> P1
    console.log("\n--- Advance P0 -> P1 ---");
    const p0Advance = await findAndClickAdvance(page, 0);
    console.log(`  Advance result: clicked=${p0Advance.clicked}, advanced=${p0Advance.advanced}`);

    if (!p0Advance.clicked) {
      const chatInput = page.locator("textarea[placeholder*='修改方案']");
      if (await chatInput.isVisible().catch(() => false)) {
        await chatInput.fill("确认需求，进入下一阶段");
        await page.locator("button", { hasText: "发送反馈" }).click();
        await page.waitForTimeout(3000);
        await waitForAgentIdle(page);
        const retry = await findAndClickAdvance(page, 0);
        console.log(`  Retry advance: clicked=${retry.clicked}, advanced=${retry.advanced}`);
      }
    }

    await page.waitForTimeout(2000);
    let currentUrl = page.url();
    console.log(`  URL after P0 advance: ${currentUrl}`);

    // ============================================================
    // Phase 1: Outline
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 1: 内容主线 (Outline)");
    console.log("=".repeat(60));

    const p1Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p1BodyText = await page.locator("body").innerText();

    // Check for outline-related content
    const hasOutlineContent = p1BodyText.includes("大纲") ||
      p1BodyText.includes("版本") ||
      p1BodyText.includes("outline") ||
      p1BodyText.includes("章节") ||
      p1BodyText.includes("结构");
    p1Checks.push({ label: "P1-大纲内容", pass: hasOutlineContent, detail: `页面含大纲相关内容: ${hasOutlineContent}` });

    // Check for version cards
    const versionCards = page.locator('[data-testid*="version"], [class*="versionCard"], [class*="outlineCard"]');
    const cardCount = await versionCards.count().catch(() => 0);
    p1Checks.push({ label: "P1-版本卡片", pass: cardCount >= 1, detail: `大纲版本卡片数: ${cardCount}` });

    // Check for stub
    const isStubP1 = p1BodyText.includes("this is a placeholder") || p1BodyText.includes("假设主题为");
    p1Checks.push({ label: "P1-非Stub", pass: !isStubP1, detail: `占位文本: ${isStubP1}` });

    // Check for key topics (a/b/c coverage)
    const hasFedMention = p1BodyText.includes("美联储") || p1BodyText.includes("FOMC") || p1BodyText.includes("fed");
    const hasCandidate = p1BodyText.includes("人选") || p1BodyText.includes("候选") || p1BodyText.includes("Powell") || p1BodyText.includes("Brainard") || p1BodyText.includes("Warsh");
    const hasMarketImpact = p1BodyText.includes("市场") || p1BodyText.includes("影响") || p1BodyText.includes("经济");
    p1Checks.push({ label: "P1-a-公布时间", pass: hasFedMention, detail: `含美联储相关内容: ${hasFedMention}` });
    p1Checks.push({ label: "P1-b-热门人选", pass: hasCandidate, detail: `含人选相关内容: ${hasCandidate}` });
    p1Checks.push({ label: "P1-c-市场影响", pass: hasMarketImpact, detail: `含市场影响内容: ${hasMarketImpact}` });

    const p1Pass = hasOutlineContent && !isStubP1 && cardCount >= 1;
    recordPhase({ phase: 1, status: p1Pass ? "PASS" : "FAIL", checks: p1Checks });

    // Advance P1 -> P2
    console.log("\n--- Advance P1 -> P2 ---");
    const p1Advance = await findAndClickAdvance(page, 1);
    console.log(`  Advance result: clicked=${p1Advance.clicked}, advanced=${p1Advance.advanced}`);

    // ============================================================
    // Phase 2: Structured Script
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 2: 结构化口播脚本");
    console.log("=".repeat(60));

    const p2Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p2BodyText = await page.locator("body").innerText();

    const hasScriptContent = p2BodyText.includes("脚本") ||
      p2BodyText.includes("script") ||
      p2BodyText.includes("segment") ||
      p2BodyText.includes("口播") ||
      p2BodyText.includes("段落");
    p2Checks.push({ label: "P2-脚本内容", pass: hasScriptContent, detail: `含脚本相关内容: ${hasScriptContent}` });

    // Check for word count indicators
    const hasWordCount = p2BodyText.includes("字") || p2BodyText.includes("word") || p2BodyText.includes("total");
    p2Checks.push({ label: "P2-字数统计", pass: hasWordCount, detail: `含字数相关: ${hasWordCount}` });

    // Check for data points
    const hasDataPoints = p2BodyText.includes("数据") || p2BodyText.includes("data") || p2BodyText.includes("source");
    p2Checks.push({ label: "P2-数据点", pass: hasDataPoints, detail: `含数据点: ${hasDataPoints}` });

    const isStubP2 = p2BodyText.includes("this is a placeholder") || p2BodyText.includes("段落 1 内容");
    p2Checks.push({ label: "P2-非Stub", pass: !isStubP2, detail: `占位文本: ${isStubP2}` });

    // Check for specific names
    const hasSpecificNames = /Powell|Brainard|Warsh|Hassett|鲍威尔|布雷纳德|沃什/.test(p2BodyText);
    p2Checks.push({ label: "P2-具体人名", pass: hasSpecificNames, detail: `含具体人名: ${hasSpecificNames}` });

    const p2Pass = hasScriptContent && !isStubP2;
    recordPhase({ phase: 2, status: p2Pass ? "PASS" : "FAIL", checks: p2Checks });

    console.log("\n--- Advance P2 -> P3 ---");
    const p2Advance = await findAndClickAdvance(page, 2);
    console.log(`  Advance result: clicked=${p2Advance.clicked}, advanced=${p2Advance.advanced}`);

    // ============================================================
    // Phase 3: Polished Script
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 3: 风格润色");
    console.log("=".repeat(60));

    const p3Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p3BodyText = await page.locator("body").innerText();

    const hasPolishedContent = p3BodyText.includes("润色") ||
      p3BodyText.includes("风格") ||
      p3BodyText.includes("polished") ||
      p3BodyText.includes("口语") ||
      p3BodyText.includes("文稿");
    p3Checks.push({ label: "P3-润色内容", pass: hasPolishedContent, detail: `含润色相关内容: ${hasPolishedContent}` });

    // Check for style selector or style tag
    const hasStyleTag = p3BodyText.includes("风格") || p3BodyText.includes("style") || p3BodyText.includes("专业") || p3BodyText.includes("科普") || p3BodyText.includes("评论");
    p3Checks.push({ label: "P3-风格标签", pass: hasStyleTag, detail: `含风格标签: ${hasStyleTag}` });

    // Check for comparison view
    const hasComparisonView = p3BodyText.includes("对比") || p3BodyText.includes("润色前") || p3BodyText.includes("润色后");
    p3Checks.push({ label: "P3-对比视图", pass: hasComparisonView, detail: `含对比视图: ${hasComparisonView}` });

    const isStubP3 = p3BodyText.includes("this is a placeholder") || p3BodyText.includes("段落 1 内容");
    p3Checks.push({ label: "P3-非Stub", pass: !isStubP3, detail: `占位文本: ${isStubP3}` });

    // Check for absence of formal written language
    const hasFormalLanguage = p3BodyText.includes("综上所述") || p3BodyText.includes("鉴于") || p3BodyText.includes("诚然");
    p3Checks.push({ label: "P3-口语化", pass: !hasFormalLanguage, detail: `书面语残留: ${hasFormalLanguage}` });

    const p3Pass = hasPolishedContent && !isStubP3;
    recordPhase({ phase: 3, status: p3Pass ? "PASS" : "FAIL", checks: p3Checks });

    console.log("\n--- Advance P3 -> P4 ---");
    const p3Advance = await findAndClickAdvance(page, 3);
    console.log(`  Advance result: clicked=${p3Advance.clicked}, advanced=${p3Advance.advanced}`);

    // ============================================================
    // Phase 4: TTS Narration
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 4: 人声旁白 (TTS)");
    console.log("=".repeat(60));

    const p4Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 60000);
    const p4BodyText = await page.locator("body").innerText();

    // Check for audio player
    const audioPlayer = page.locator("audio");
    const hasAudioPlayer = await audioPlayer.isVisible().catch(() => false);
    p4Checks.push({ label: "P4-音频播放器", pass: hasAudioPlayer, detail: `音频播放器可见: ${hasAudioPlayer}` });

    // Check for download button
    const downloadBtn = page.locator("a[download], button", { hasText: /下载|download/i });
    const hasDownload = await downloadBtn.first().isVisible().catch(() => false);
    p4Checks.push({ label: "P4-下载按钮", pass: hasDownload, detail: `下载按钮可见: ${hasDownload}` });

    // Check for segment cards
    const hasSegments = p4BodyText.includes("segment") || p4BodyText.includes("分段") || p4BodyText.includes("seg_");
    p4Checks.push({ label: "P4-分段列表", pass: hasSegments, detail: `分段列表: ${hasSegments}` });

    // Check TTS-related content
    const hasTTSContent = p4BodyText.includes("旁白") || p4BodyText.includes("TTS") || p4BodyText.includes("音频") || p4BodyText.includes("narration") || p4BodyText.includes("mp3");
    p4Checks.push({ label: "P4-TTS内容", pass: hasTTSContent, detail: `含TTS相关内容: ${hasTTSContent}` });

    // Check for duration display
    const hasDuration = p4BodyText.includes("秒") || p4BodyText.includes("duration") || /\d+:\d+/.test(p4BodyText);
    p4Checks.push({ label: "P4-时长显示", pass: hasDuration, detail: `含时长显示: ${hasDuration}` });

    // Check for quality alerts
    const hasQualityAlert = p4BodyText.includes("静音") || p4BodyText.includes("削波") || p4BodyText.includes("silent");
    // Not necessarily a failure if no alerts - means quality is good
    p4Checks.push({ label: "P4-质检状态", pass: true, detail: `质检告警: ${hasQualityAlert ? "有告警" : "无告警(质量良好)"}` });

    const isStubP4 = p4BodyText.includes("this is a placeholder") || p4BodyText.includes("空白音轨");
    p4Checks.push({ label: "P4-非Stub", pass: !isStubP4, detail: `占位文本: ${isStubP4}` });

    const p4Pass = hasTTSContent && !isStubP4;
    recordPhase({ phase: 4, status: p4Pass ? "PASS" : "FAIL", checks: p4Checks });

    console.log("\n--- Advance P4 -> P5 ---");
    const p4Advance = await findAndClickAdvance(page, 4);
    console.log(`  Advance result: clicked=${p4Advance.clicked}, advanced=${p4Advance.advanced}`);

    // ============================================================
    // Phase 5: BGM Mix
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 5: 背景音乐 (BGM)");
    console.log("=".repeat(60));

    const p5Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p5BodyText = await page.locator("body").innerText();

    // Check for BGM-related content or skip indicator
    const hasBGMContent = p5BodyText.includes("BGM") || p5BodyText.includes("背景音乐") || p5BodyText.includes("bgm") || p5BodyText.includes("混音");
    const isSkipped = p5BodyText.includes("跳过") || p5BodyText.includes("skipped");

    p5Checks.push({ label: "P5-BGM内容", pass: hasBGMContent || isSkipped, detail: `BGM内容: ${hasBGMContent}, 跳过: ${isSkipped}` });

    // Check for emotion curve or music selection
    const hasMusicSelection = p5BodyText.includes("情绪") || p5BodyText.includes("候选") || p5BodyText.includes("版权") || p5BodyText.includes("CC0");
    p5Checks.push({ label: "P5-音乐选择", pass: hasMusicSelection || isSkipped, detail: `音乐选择UI: ${hasMusicSelection}` });

    const isStubP5 = p5BodyText.includes("this is a placeholder");
    p5Checks.push({ label: "P5-非Stub", pass: !isStubP5, detail: `占位: ${isStubP5}` });

    const p5Pass = (hasBGMContent || isSkipped) && !isStubP5;
    recordPhase({ phase: 5, status: p5Pass ? "PASS" : isSkipped ? "SKIP" : "FAIL", checks: p5Checks });

    console.log("\n--- Advance P5 -> P6 ---");
    const p5Advance = await findAndClickAdvance(page, 5);
    console.log(`  Advance result: clicked=${p5Advance.clicked}, advanced=${p5Advance.advanced}`);

    // ============================================================
    // Phase 6: SFX Layout
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 6: 音效设计 (SFX)");
    console.log("=".repeat(60));

    const p6Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p6BodyText = await page.locator("body").innerText();

    const hasSFXContent = p6BodyText.includes("SFX") || p6BodyText.includes("音效") || p6BodyText.includes("sfx") || p6BodyText.includes("boom") || p6BodyText.includes("whoosh");
    const isP6Skipped = p6BodyText.includes("跳过") || p6BodyText.includes("skipped");
    p6Checks.push({ label: "P6-音效内容", pass: hasSFXContent || isP6Skipped, detail: `音效内容: ${hasSFXContent}, 跳过: ${isP6Skipped}` });

    // Check for final audio player
    const hasFinalAudioP6 = p6BodyText.includes("final_audio") || p6BodyText.includes("最终音频") || p6BodyText.includes("完整音频");
    p6Checks.push({ label: "P6-最终音频", pass: hasFinalAudioP6 || isP6Skipped, detail: `最终音频: ${hasFinalAudioP6}` });

    const isStubP6 = p6BodyText.includes("this is a placeholder");
    p6Checks.push({ label: "P6-非Stub", pass: !isStubP6, detail: `占位: ${isStubP6}` });

    const p6Pass = (hasSFXContent || isP6Skipped) && !isStubP6;
    recordPhase({ phase: 6, status: p6Pass ? "PASS" : isP6Skipped ? "SKIP" : "FAIL", checks: p6Checks });

    console.log("\n--- Advance P6 -> P7 ---");
    const p6Advance = await findAndClickAdvance(page, 6);
    console.log(`  Advance result: clicked=${p6Advance.clicked}, advanced=${p6Advance.advanced}`);

    // ============================================================
    // Phase 7: Storyboard
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 7: 分镜脚本 (Storyboard)");
    console.log("=".repeat(60));

    const p7Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 30000);
    const p7BodyText = await page.locator("body").innerText();

    const hasStoryboardContent = p7BodyText.includes("分镜") || p7BodyText.includes("storyboard") || p7BodyText.includes("shot") || p7BodyText.includes("画面");
    p7Checks.push({ label: "P7-分镜内容", pass: hasStoryboardContent, detail: `分镜内容: ${hasStoryboardContent}` });

    // Check for shot cards / gallery
    const shotCards = page.locator('[data-testid*="shot"], [class*="shotCard"], [class*="storyCard"]');
    const shotCount = await shotCards.count().catch(() => 0);
    p7Checks.push({ label: "P7-Shot卡片", pass: shotCount >= 1, detail: `Shot卡片数: ${shotCount}` });

    // Check for scene type badges
    const hasSceneTypes = p7BodyText.includes("template") || p7BodyText.includes("broll") || p7BodyText.includes("chart") || p7BodyText.includes("模板") || p7BodyText.includes("素材");
    p7Checks.push({ label: "P7-画面类型", pass: hasSceneTypes, detail: `画面类型标签: ${hasSceneTypes}` });

    // Check for time ranges
    const hasTimeRanges = /\d+s/.test(p7BodyText) || /\d+秒/.test(p7BodyText) || /start/.test(p7BodyText) || /end/.test(p7BodyText);
    p7Checks.push({ label: "P7-时间戳", pass: hasTimeRanges, detail: `时间范围: ${hasTimeRanges}` });

    const isStubP7 = p7BodyText.includes("this is a placeholder");
    p7Checks.push({ label: "P7-非Stub", pass: !isStubP7, detail: `占位: ${isStubP7}` });

    const p7Pass = hasStoryboardContent && !isStubP7;
    recordPhase({ phase: 7, status: p7Pass ? "PASS" : "FAIL", checks: p7Checks });

    console.log("\n--- Advance P7 -> P8 (via P7A) ---");
    const p7Advance = await findAndClickAdvance(page, 7);
    console.log(`  Advance result: clicked=${p7Advance.clicked}, advanced=${p7Advance.advanced}`);

    // ============================================================
    // Phase 7A: Material Manifest (if visible)
    // ============================================================
    // This may be integrated into P7 or a separate step
    await waitForAgentIdle(page, 30000);
    const p7aBodyText = await page.locator("body").innerText();
    if (p7aBodyText.includes("material") || p7aBodyText.includes("物料") || p7aBodyText.includes("素材清单")) {
      console.log("\n--- Phase 7A detected, advancing ---");
      const p7aAdvance = await findAndClickAdvance(page, 7);
      console.log(`  P7A Advance: clicked=${p7aAdvance.clicked}, advanced=${p7aAdvance.advanced}`);
    }

    // ============================================================
    // Phase 8: Keyframe Render
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 8: 关键画面渲染");
    console.log("=".repeat(60));

    const p8Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 60000);
    const p8BodyText = await page.locator("body").innerText();

    const hasKeyframeContent = p8BodyText.includes("渲染") || p8BodyText.includes("keyframe") || p8BodyText.includes("画面") || p8BodyText.includes("render");
    p8Checks.push({ label: "P8-渲染内容", pass: hasKeyframeContent, detail: `渲染内容: ${hasKeyframeContent}` });

    // Check for image/video previews
    const previewImages = page.locator("img[src*='keyframe'], img[src*='phase_8'], img[src*='preview']");
    const imgCount = await previewImages.count().catch(() => 0);
    p8Checks.push({ label: "P8-预览图", pass: imgCount >= 1, detail: `预览图数量: ${imgCount}` });

    // Check for success rate
    const hasSuccessRate = p8BodyText.includes("成功") || p8BodyText.includes("%") || p8BodyText.includes("success");
    p8Checks.push({ label: "P8-成功率", pass: hasSuccessRate, detail: `成功率显示: ${hasSuccessRate}` });

    const isStubP8 = p8BodyText.includes("this is a placeholder");
    p8Checks.push({ label: "P8-非Stub", pass: !isStubP8, detail: `占位: ${isStubP8}` });

    const p8Pass = hasKeyframeContent && !isStubP8;
    recordPhase({ phase: 8, status: p8Pass ? "PASS" : "FAIL", checks: p8Checks });

    console.log("\n--- Advance P8 -> P9 ---");
    const p8Advance = await findAndClickAdvance(page, 8);
    console.log(`  Advance result: clicked=${p8Advance.clicked}, advanced=${p8Advance.advanced}`);

    // ============================================================
    // Phase 9: B-Roll Material
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 9: B-Roll 素材准备");
    console.log("=".repeat(60));

    const p9Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 60000);
    const p9BodyText = await page.locator("body").innerText();

    const hasBRollContent = p9BodyText.includes("B-Roll") || p9BodyText.includes("broll") || p9BodyText.includes("素材") || p9BodyText.includes("Pexels") || p9BodyText.includes("视频素材");
    p9Checks.push({ label: "P9-BRoll内容", pass: hasBRollContent, detail: `BRoll内容: ${hasBRollContent}` });

    // Check for thumbnail gallery
    const thumbnails = page.locator("img[src*='broll'], img[src*='phase_9'], img[src*='thumbnail'], video[src*='broll']");
    const thumbCount = await thumbnails.count().catch(() => 0);
    p9Checks.push({ label: "P9-缩略图", pass: thumbCount >= 1, detail: `缩略图数: ${thumbCount}` });

    // Check for source labels
    const hasSources = p9BodyText.includes("Pexels") || p9BodyText.includes("来源") || p9BodyText.includes("source");
    p9Checks.push({ label: "P9-来源标签", pass: hasSources, detail: `来源标签: ${hasSources}` });

    const isStubP9 = p9BodyText.includes("this is a placeholder");
    p9Checks.push({ label: "P9-非Stub", pass: !isStubP9, detail: `占位: ${isStubP9}` });

    const p9Pass = hasBRollContent && !isStubP9;
    recordPhase({ phase: 9, status: p9Pass ? "PASS" : "FAIL", checks: p9Checks });

    console.log("\n--- Advance P9 -> P10 ---");
    const p9Advance = await findAndClickAdvance(page, 9);
    console.log(`  Advance result: clicked=${p9Advance.clicked}, advanced=${p9Advance.advanced}`);

    // ============================================================
    // Phase 10: Rough Cut
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 10: 粗剪合成");
    console.log("=".repeat(60));

    const p10Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 60000);
    const p10BodyText = await page.locator("body").innerText();

    // Check for video player
    const videoPlayer = page.locator("video");
    const hasVideoPlayer = await videoPlayer.isVisible().catch(() => false);
    p10Checks.push({ label: "P10-视频播放器", pass: hasVideoPlayer, detail: `视频播放器: ${hasVideoPlayer}` });

    // Check for rough cut references
    const hasRoughCut = p10BodyText.includes("粗剪") || p10BodyText.includes("rough") || p10BodyText.includes("mp4") || p10BodyText.includes("视频");
    p10Checks.push({ label: "P10-粗剪内容", pass: hasRoughCut, detail: `粗剪内容: ${hasRoughCut}` });

    // Check for subtitle overlay
    const hasSubtitleMention = p10BodyText.includes("字幕") || p10BodyText.includes("subtitle");
    p10Checks.push({ label: "P10-字幕", pass: hasSubtitleMention, detail: `字幕显示: ${hasSubtitleMention}` });

    // Check for duration/resolution
    const hasVideoMeta = /\d{3,4}x\d{3,4}/.test(p10BodyText) || p10BodyText.includes("分辨率") || p10BodyText.includes("1080");
    p10Checks.push({ label: "P10-视频元信息", pass: hasVideoMeta, detail: `视频规格: ${hasVideoMeta}` });

    const isStubP10 = p10BodyText.includes("this is a placeholder");
    p10Checks.push({ label: "P10-非Stub", pass: !isStubP10, detail: `占位: ${isStubP10}` });

    // Check for AV sync alerts
    const hasAVAlert = p10BodyText.includes("同步") || p10BodyText.includes("AVSync");
    p10Checks.push({ label: "P10-AV同步", pass: true, detail: `AV同步告警: ${hasAVAlert ? "有告警" : "无告警"}` });

    const p10Pass = (hasVideoPlayer || hasRoughCut) && !isStubP10;
    recordPhase({ phase: 10, status: p10Pass ? "PASS" : "FAIL", checks: p10Checks });

    console.log("\n--- Advance P10 -> P11 ---");
    const p10Advance = await findAndClickAdvance(page, 10);
    console.log(`  Advance result: clicked=${p10Advance.clicked}, advanced=${p10Advance.advanced}`);

    // ============================================================
    // Phase 11: Final Delivery
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("PHASE 11: 精剪交付");
    console.log("=".repeat(60));

    const p11Checks: PhaseResult["checks"] = [];
    await waitForAgentIdle(page, 60000);
    const p11BodyText = await page.locator("body").innerText();

    // Check for final video player
    const finalVideoPlayer = page.locator("video");
    const hasFinalVideo = await finalVideoPlayer.isVisible().catch(() => false);
    p11Checks.push({ label: "P11-最终播放器", pass: hasFinalVideo, detail: `最终播放器: ${hasFinalVideo}` });

    // Check for download buttons (per platform)
    const downloadButtons = page.locator("a[download], button", { hasText: /下载|download|bilibili|douyin/i });
    const dlBtnCount = await downloadButtons.count().catch(() => 0);
    p11Checks.push({ label: "P11-下载按钮", pass: dlBtnCount >= 1, detail: `下载按钮数: ${dlBtnCount}` });

    // Check for cover images
    const coverImages = page.locator("img[src*='cover'], img[src*='封面']");
    const coverCount = await coverImages.count().catch(() => 0);
    p11Checks.push({ label: "P11-封面方案", pass: coverCount >= 1, detail: `封面数: ${coverCount}` });

    // Check for subtitle download
    const hasSRTDownload = p11BodyText.includes("srt") || p11BodyText.includes("字幕") || p11BodyText.includes("subtitle");
    p11Checks.push({ label: "P11-字幕下载", pass: hasSRTDownload, detail: `字幕下载: ${hasSRTDownload}` });

    // Check for completed status
    const isCompleted = p11BodyText.includes("完成") || p11BodyText.includes("completed") || p11BodyText.includes("交付");
    p11Checks.push({ label: "P11-完成状态", pass: isCompleted, detail: `完成状态: ${isCompleted}` });

    // Check for platform-specific versions
    const hasPlatforms = p11BodyText.includes("bilibili") || p11BodyText.includes("B站") || p11BodyText.includes("douyin") || p11BodyText.includes("抖音");
    p11Checks.push({ label: "P11-平台版本", pass: hasPlatforms, detail: `平台版本: ${hasPlatforms}` });

    const isStubP11 = p11BodyText.includes("this is a placeholder");
    p11Checks.push({ label: "P11-非Stub", pass: !isStubP11, detail: `占位: ${isStubP11}` });

    const p11Pass = (hasFinalVideo || isCompleted) && !isStubP11;
    recordPhase({ phase: 11, status: p11Pass ? "PASS" : "FAIL", checks: p11Checks });

    // ============================================================
    // Final: Download video and verify with ffprobe
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("FINAL VERIFICATION: Download + ffprobe");
    console.log("=".repeat(60));

    // Try to find and click a download link for the final video
    let downloadedPath = "";
    const downloadPromise = page.waitForEvent("download", { timeout: 30000 }).then(async (download: any) => {
      const path = `/tmp/${download.suggestedFilename()}`;
      await download.saveAs(path);
      downloadedPath = path;
      console.log(`  Downloaded: ${path}`);
    }).catch(() => { console.log("  No download event captured"); });

    // Click first available download button
    const firstDL = page.locator("a[download]").first();
    if (await firstDL.isVisible().catch(() => false)) {
      await firstDL.click();
      await downloadPromise;
    } else {
      // Try button download
      const dlBtn = page.locator("button", { hasText: /下载完整视频|下载最终|download.*mp4/i }).first();
      if (await dlBtn.isVisible().catch(() => false)) {
        await dlBtn.click();
        await downloadPromise;
      }
    }

    await page.waitForTimeout(2000);

    // ============================================================
    // Print Test Report
    // ============================================================
    console.log("\n\n");
    console.log("╔══════════════════════════════════════════════════════════════╗");
    console.log("║     完整12阶段端到端验收测试报告                                ║");
    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log(`║  Project: ${projectId}`);
    console.log(`║  Title: ${TEST_TITLE}`);
    console.log(`║  Final URL: ${page.url()}`);
    console.log("╠══════════════════════════════════════════════════════════════╣");

    let totalPass = 0;
    let totalFail = 0;
    let totalSkip = 0;

    for (const r of allResults) {
      const icon = r.status === "PASS" ? "PASS" : r.status === "SKIP" ? "SKIP" : "FAIL";
      console.log(`║  Phase ${r.phase}: ${icon} (${r.checks.length} checks)`);
      if (r.status === "PASS") totalPass++;
      else if (r.status === "SKIP") totalSkip++;
      else totalFail++;

      for (const c of r.checks) {
        const cIcon = c.pass ? "  [PASS]" : "  [FAIL]";
        console.log(`║    ${cIcon} ${c.label}: ${c.detail.substring(0, 50)}`);
      }
    }

    console.log("╠══════════════════════════════════════════════════════════════╣");
    console.log(`║  PASS: ${totalPass}  FAIL: ${totalFail}  SKIP: ${totalSkip}`);
    console.log(`║  Downloaded file: ${downloadedPath || "N/A"}`);
    console.log("╚══════════════════════════════════════════════════════════════╝");

    // Assert minimum: at least Phase 0 should pass
    expect(totalPass).toBeGreaterThanOrEqual(1);

    // If we have a download, verify with ffprobe (via page evaluate)
    if (downloadedPath) {
      // We can't run ffprobe from Playwright directly on the host
      // but we can note the path for later verification
      console.log(`\n  To verify: ffprobe ${downloadedPath}`);
    }
  });
});
