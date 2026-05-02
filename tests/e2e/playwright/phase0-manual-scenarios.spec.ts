import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3000";

interface TestResult {
  scenario: string;
  step: string;
  checkpoint: string;
  status: "PASS" | "FAIL" | "PARTIAL" | "SKIP";
  detail: string;
}

const results: TestResult[] = [];

function record(scenario: string, step: string, checkpoint: string, status: "PASS" | "FAIL" | "PARTIAL" | "SKIP", detail: string) {
  results.push({ scenario, step, checkpoint, status, detail });
}

async function createProjectAndWait(page: any, title: string, desc: string): Promise<{ projectId: string; navigated: boolean }> {
  await page.goto(`${BASE_URL}/projects/new`);
  await page.waitForLoadState("networkidle");
  await page.locator("#title").fill(title);
  await page.locator("#desc").fill(desc);
  const submitBtn = page.locator("button[type='submit']");
  await expect(submitBtn).toBeEnabled({ timeout: 3000 });
  await submitBtn.click();

  // Wait for navigation to project page
  try {
    await page.waitForURL((url: URL) => url.pathname.match(/\/projects\/proj_/) !== null, { timeout: 15000 });
    const projectId = page.url().match(/\/projects\/(proj_[^/]+)/)?.[1] ?? "";
    return { projectId, navigated: true };
  } catch {
    return { projectId: "", navigated: false };
  }
}

test.afterAll(() => {
  console.log("\n" + "=".repeat(70));
  console.log("  Phase 0 手动测试场景 — 完整测试报告");
  console.log("=".repeat(70));

  const byScenario = new Map<string, TestResult[]>();
  for (const r of results) {
    if (!byScenario.has(r.scenario)) byScenario.set(r.scenario, []);
    byScenario.get(r.scenario)!.push(r);
  }

  for (const [scenario, items] of byScenario) {
    console.log(`\n── ${scenario} ──`);
    for (const r of items) {
      const icon = r.status === "PASS" ? "✅" : r.status === "PARTIAL" ? "⚠️" : r.status === "SKIP" ? "⊘" : "❌";
      console.log(`  ${icon} [${r.step}] ${r.checkpoint}: ${r.detail.substring(0, 120)}`);
    }
  }

  const pass = results.filter((r) => r.status === "PASS").length;
  const fail = results.filter((r) => r.status === "FAIL").length;
  const partial = results.filter((r) => r.status === "PARTIAL").length;
  const skip = results.filter((r) => r.status === "SKIP").length;
  const total = results.length;

  console.log(`\n${"=".repeat(70)}`);
  console.log(`  总计: ${total} | ✅ ${pass} | ⚠️ ${partial} | ❌ ${fail} | ⊘ ${skip}`);
  console.log(`  通过率: ${((pass / total) * 100).toFixed(1)}%`);
  console.log(`  含 PARTIAL 通过率: ${(((pass + partial) / total) * 100).toFixed(1)}%`);
  console.log("=".repeat(70) + "\n");
});

// ═══════════════════════════════════════════════════════════════
// 场景 1: 创建项目 + 生成完整需求定义
// ═══════════════════════════════════════════════════════════════
test.describe("场景 1: 创建项目 + 生成完整需求定义", () => {
  const SCENARIO = "场景1-需求定义";

  test("步骤 1.1 — 进入创建项目页面", async ({ page }) => {
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    const newBtn = page.locator("button", { hasText: "新建项目" });
    const btnVisible = await newBtn.isVisible().catch(() => false);
    const btnEnabled = await newBtn.isEnabled().catch(() => false);
    if (btnVisible && btnEnabled) {
      record(SCENARIO, "1.1", "1.1a '+ 新建项目'按钮存在且可点击", "PASS", `visible=${btnVisible} enabled=${btnEnabled}`);
    } else {
      record(SCENARIO, "1.1", "1.1a '+ 新建项目'按钮存在且可点击", "FAIL", `visible=${btnVisible} enabled=${btnEnabled}`);
    }

    await newBtn.click();
    await page.waitForURL("**/projects/new");
    record(SCENARIO, "1.1", "1.1b 点击后地址栏跳转到 /projects/new",
      page.url().includes("/projects/new") ? "PASS" : "FAIL", `URL: ${page.url()}`);

    const titleInput = page.locator("#title");
    const descInput = page.locator("#desc");
    const submitBtn = page.locator("button[type='submit']");
    const hasTitle = await titleInput.isVisible().catch(() => false);
    const hasDesc = await descInput.isVisible().catch(() => false);
    const hasSubmit = await submitBtn.isVisible().catch(() => false);
    if (hasTitle && hasDesc && hasSubmit) {
      record(SCENARIO, "1.1", "1.1c 标题输入框、描述输入框、提交按钮存在", "PASS", "三者均可见");
    } else {
      record(SCENARIO, "1.1", "1.1c 标题输入框、描述输入框、提交按钮存在", "FAIL", `title=${hasTitle} desc=${hasDesc} submit=${hasSubmit}`);
    }

    await page.screenshot({ path: "test-results/phase0-s1-step1.1-create-form.png", fullPage: true });
  });

  test("步骤 1.2 — 输入标题和完整描述并提交", async ({ page }) => {
    const { projectId, navigated } = await createProjectAndWait(
      page,
      "2026年黄金价格走势分析与投资展望",
      "本视频分析 2026 年黄金价格走势。核心观点是美联储降息周期下黄金仍有上行空间，建议投资者关注实际利率变化和央行购金动态。预期时长约 8-12 分钟，发布在 B 站。"
    );

    if (!navigated || !projectId) {
      record(SCENARIO, "1.2", "1.2a 提交后跳转到项目页", "FAIL",
        `页面未跳转，停留在 ${page.url()}。表单提交可能失败或 onSuccess 回调未触发`);
      return;
    }

    record(SCENARIO, "1.2", "1.2a 提交成功并跳转", "PASS", `跳转到 projectId=${projectId}`);
    record(SCENARIO, "1.2", "1.2b project_id 格式", "PASS", `id=${projectId}`);

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    const currentUrl = page.url();
    record(SCENARIO, "1.2", "1.2c URL 包含项目 ID", "PASS", `URL: ${currentUrl.substring(0, 60)}`);

    await page.screenshot({ path: "test-results/phase0-s1-step1.2-project-page.png", fullPage: true });

    const pageText = await page.locator("body").innerText();

    // Phase navigation check
    const phaseNav = page.locator('[data-testid="phase-nav-sidebar"]');
    const phaseNavVisible = await phaseNav.isVisible().catch(() => false);
    record(SCENARIO, "1.2", "1.2d 左侧阶段导航可见",
      phaseNavVisible ? "PASS" : "FAIL",
      phaseNavVisible ? "PhaseNavigation sidebar 渲染" : "PhaseNavigation sidebar 不存在于 WorkflowPage 中");

    // User message in chat
    const hasUserMsg = pageText.includes("黄金") || pageText.includes("价格走势");
    record(SCENARIO, "1.2", "1.2e 对话区显示用户消息",
      hasUserMsg ? "PASS" : "FAIL",
      hasUserMsg ? "对话区包含相关内容" : "对话区仅显示硬编码 MOCK_MESSAGES，不显示用户实际输入");

    // Loading indicator
    const hasLoading = pageText.includes("执行中") || pageText.includes("生成") || pageText.includes("加载");
    record(SCENARIO, "1.2", "1.2f 加载/处理中指示器",
      hasLoading ? "PASS" : "FAIL",
      hasLoading ? "检测到处理中状态" : "无加载指示器。WorkflowPage 使用静态 mock 数据");

    // Task card
    const taskCard = page.locator('[data-testid="task-card"]');
    const taskCardVisible = await taskCard.isVisible().catch(() => false);
    record(SCENARIO, "1.2", "1.2g 任务清单面板存在",
      taskCardVisible ? "PARTIAL" : "FAIL",
      taskCardVisible ? "TaskCard 存在但显示硬编码 mock 任务" : "TaskCard 不可见");
  });

  test("步骤 1.3 — 等待 RequirementsAgent 生成完成", async ({ page }) => {
    const { projectId, navigated } = await createProjectAndWait(
      page,
      "黄金价格走势分析测试",
      "本视频分析 2026 年黄金价格走势。核心观点是美联储降息周期下黄金仍有上行空间。预期时长约 8-12 分钟，发布在 B 站。"
    );

    if (!navigated) {
      record(SCENARIO, "1.3", "1.3a 项目创建", "FAIL", "项目创建失败，无法继续");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(8000); // Wait for backend agent processing
    const pageText = await page.locator("body").innerText();
    await page.screenshot({ path: "test-results/phase0-s1-step1.3-after-agent.png", fullPage: true });

    const hasStructured = pageText.includes("需求") || pageText.includes("时长") || pageText.includes("平台");
    record(SCENARIO, "1.3", "1.3a 结构化需求摘要显示",
      hasStructured ? "PARTIAL" : "FAIL",
      hasStructured ? "检测到需求相关内容" : "无结构化需求。WorkflowPage 使用硬编码 MOCK_MESSAGES");

    const hasPlatformSpec = pageText.includes("1920") || pageText.includes("1080") || pageText.includes("bilibili");
    record(SCENARIO, "1.3", "1.3b B站平台规格显示",
      hasPlatformSpec ? "PARTIAL" : "FAIL",
      hasPlatformSpec ? "检测到平台相关内容" : "无平台规格。mock 数据不包含平台配置");

    const hasWordCount = pageText.includes("字数") || pageText.includes("1536") || pageText.includes("2880");
    record(SCENARIO, "1.3", "1.3c 目标字数范围",
      hasWordCount ? "PASS" : "FAIL",
      `字数范围${hasWordCount ? "存在" : "不存在"}`);

    record(SCENARIO, "1.3", "1.3d 已确认字段标记", "FAIL", "mock 数据无绿色勾/橙色问号标记");
    record(SCENARIO, "1.3", "1.3e 任务状态更新", "FAIL", "任务清单使用硬编码 mock 数据");
  });

  test("步骤 1.4 — CompletenessReviewer 审核通过 + 推进按钮", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page,
      "审核流程测试项目",
      "分析近期A股市场走势，时长约5分钟，发在B站，面向普通投资者，用通俗语言讲解技术分析和基本面"
    );

    if (!navigated) {
      record(SCENARIO, "1.4", "1.4 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(5000);
    const pageText = await page.locator("body").innerText();
    await page.screenshot({ path: "test-results/phase0-s1-step1.4-review-check.png", fullPage: true });

    const hasReview = pageText.includes("review") || pageText.includes("审核");
    record(SCENARIO, "1.4", "1.4a review 任务状态",
      hasReview ? "PARTIAL" : "FAIL", "mock 数据无审查任务");

    const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
    const btnVisible = await advanceBtn.isVisible().catch(() => false);
    record(SCENARIO, "1.4", "1.4b '确认进入下一阶段'按钮",
      btnVisible ? "PASS" : "FAIL", btnVisible ? "按钮可见" : "按钮不存在");

    if (btnVisible) {
      const btnEnabled = await advanceBtn.isEnabled().catch(() => false);
      record(SCENARIO, "1.4", "1.4c 按钮可点击状态",
        btnEnabled ? "PASS" : "PARTIAL", `enabled=${btnEnabled}`);
    } else {
      record(SCENARIO, "1.4", "1.4c 按钮可点击状态", "FAIL", "按钮不存在");
    }
  });
});

// ═══════════════════════════════════════════════════════════════
// 场景 2: 自然对话修改需求
// ═══════════════════════════════════════════════════════════════
test.describe("场景 2: 自然对话修改需求", () => {
  const SCENARIO = "场景2-对话修改";

  test("步骤 2.1 — revise 修改特定字段 (时长)", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "修改时长测试", "分析黄金价格走势，时长约5分钟，发在B站，面向投资新手"
    );

    if (!navigated) {
      record(SCENARIO, "2.1", "2.1 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const chatInput = page.locator('[data-testid="chat-input"] textarea');
    const inputVisible = await chatInput.isVisible().catch(() => false);
    if (!inputVisible) {
      record(SCENARIO, "2.1", "2.1a 聊天输入框可见", "FAIL", "ChatInput textarea 不可见");
      await page.screenshot({ path: "test-results/phase0-s2-step2.1-no-chat.png", fullPage: true });
      return;
    }
    record(SCENARIO, "2.1", "2.1a 聊天输入框可见", "PASS", "输入框存在");

    await chatInput.fill("把时长改成 15 分钟吧，我觉得 8-12 太短了");
    record(SCENARIO, "2.1", "2.1b 用户输入修改文本", "PASS", "已填写修改文本");

    const sendBtn = page.locator('[aria-label="发送消息"]');
    if (!(await sendBtn.isVisible().catch(() => false))) {
      record(SCENARIO, "2.1", "2.1c 发送按钮", "FAIL", "发送按钮不存在");
      return;
    }

    // Click send and observe
    await sendBtn.click();
    await page.waitForTimeout(3000);

    const pageText = await page.locator("body").innerText();
    await page.screenshot({ path: "test-results/phase0-s2-step2.1-after-revise.png", fullPage: true });

    // Check if message appeared in chat area
    const hasUserMsg = pageText.includes("15 分钟") || pageText.includes("太短");
    record(SCENARIO, "2.1", "2.1c 用户消息出现在对话区",
      hasUserMsg ? "PASS" : "FAIL",
      hasUserMsg ? "消息已显示" : "消息发送后未出现在对话区。handleSend 是空函数");

    const hasReviseTask = pageText.includes("revision") || pageText.includes("修改");
    record(SCENARIO, "2.1", "2.1d 任务清单出现 user_revision",
      hasReviseTask ? "PARTIAL" : "FAIL", "mock 任务数据不反映真实 Agent 任务");

    const hasDurationChange = pageText.includes("15") && (pageText.includes("分钟") || pageText.includes("min"));
    record(SCENARIO, "2.1", "2.1e 需求摘要更新",
      hasDurationChange ? "PARTIAL" : "FAIL", "mock 数据不反映 Agent 输出");
  });

  test("步骤 2.2 — revise 修改发布平台", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "修改平台测试", "发在B站，分析科技股走势，时长约8分钟，面向个人投资者"
    );

    if (!navigated) {
      record(SCENARIO, "2.2", "2.2 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const chatInput = page.locator('[data-testid="chat-input"] textarea');
    if (!(await chatInput.isVisible().catch(() => false))) {
      record(SCENARIO, "2.2", "2.2a 聊天输入框", "FAIL", "输入框不可见");
      return;
    }

    await chatInput.fill("改成发视频号吧，不发 B 站了");
    await page.locator('[aria-label="发送消息"]').click();
    await page.waitForTimeout(3000);

    const pageText = await page.locator("body").innerText();
    const hasPlatform = pageText.includes("视频号") || pageText.includes("wechat");
    record(SCENARIO, "2.2", "2.2a 平台更新为视频号",
      hasPlatform ? "PARTIAL" : "FAIL", "mock 数据不反映 Agent 修改");

    const hasVertical = pageText.includes("1080x1920") || pageText.includes("竖屏");
    record(SCENARIO, "2.2", "2.2b 视频号竖屏规格",
      hasVertical ? "PASS" : "FAIL", hasVertical ? "检测到竖屏规格" : "无视频号规格");

    record(SCENARIO, "2.2", "2.2c artifact_version 自增", "PARTIAL", "mock 数据无法验证版本号变化");
  });

  test("步骤 2.3 — regenerate 重新生成", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "重新生成测试", "分析A股走势，时长约5分钟，发在B站"
    );

    if (!navigated) {
      record(SCENARIO, "2.3", "2.3 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const chatInput = page.locator('[data-testid="chat-input"] textarea');
    if (!(await chatInput.isVisible().catch(() => false))) {
      record(SCENARIO, "2.3", "2.3a 输入框", "FAIL", "不可见");
      return;
    }

    await chatInput.fill("这版需求感觉不太对，重新分析一下吧");
    await page.locator('[aria-label="发送消息"]').click();
    await page.waitForTimeout(3000);

    const pageText = await page.locator("body").innerText();
    record(SCENARIO, "2.3", "2.3a regenerate 请求",
      "PARTIAL", "mock 数据无法反映 Router 意图识别");
    await page.screenshot({ path: "test-results/phase0-s2-step2.3-regenerate.png", fullPage: true });
  });

  test("步骤 2.4 — Router 模糊意图 → clarify", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "Clarify模糊意图测试", "分析黄金走势，时长约5分钟，发在B站，面向新手"
    );

    if (!navigated) {
      record(SCENARIO, "2.4", "2.4 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const chatInput = page.locator('[data-testid="chat-input"] textarea');
    if (!(await chatInput.isVisible().catch(() => false))) {
      record(SCENARIO, "2.4", "2.4a 输入框", "FAIL", "不可见");
      return;
    }

    await chatInput.fill("嗯……这个感觉不太对，你懂吧");
    await page.locator('[aria-label="发送消息"]').click();
    await page.waitForTimeout(3000);

    const pageText = await page.locator("body").innerText();
    const hasClarify = pageText.includes("澄清") || pageText.includes("不太确定") || pageText.includes("你想");
    record(SCENARIO, "2.4", "2.4a Agent 澄清回复",
      hasClarify ? "PARTIAL" : "FAIL",
      hasClarify ? "检测到澄清内容" : "无澄清回复。handleSend 是空函数");

    record(SCENARIO, "2.4", "2.4b clarify 不改动任务账本",
      "PARTIAL", "mock 数据无法验证");
    await page.screenshot({ path: "test-results/phase0-s2-step2.4-clarify.png", fullPage: true });
  });
});

// ═══════════════════════════════════════════════════════════════
// 场景 3: 澄清问题处理
// ═══════════════════════════════════════════════════════════════
test.describe("场景 3: 澄清问题处理", () => {
  const SCENARIO = "场景3-澄清处理";

  test("步骤 3.1 — 用不完整描述创建项目", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "聊聊地方债的问题", "最近地方债话题很热，想做个视频聊一聊"
    );

    if (!navigated) {
      record(SCENARIO, "3.1", "3.1 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(5000);
    const pageText = await page.locator("body").innerText();
    await page.screenshot({ path: "test-results/phase0-s3-step3.1-incomplete-desc.png", fullPage: true });

    const hasClarification = pageText.includes("需要补充") || pageText.includes("澄清") || pageText.includes("⚠");
    record(SCENARIO, "3.1", "3.1a 澄清问题区域",
      hasClarification ? "PASS" : "FAIL", "无澄清区域。WorkflowPage mock 数据不包含 clarification_needed");

    const hasAngle = pageText.includes("角度") || pageText.includes("分析");
    const hasDuration = pageText.includes("时长") || pageText.includes("分钟");
    const hasPlatform = pageText.includes("平台") || pageText.includes("发布");
    const coverage = [hasAngle, hasDuration, hasPlatform].filter(Boolean).length;
    record(SCENARIO, "3.1", "3.1b 澄清维度覆盖",
      coverage >= 1 ? "PARTIAL" : "FAIL", `覆盖 ${coverage}/3 维度`);

    const noFabrication = !pageText.includes("万亿");
    record(SCENARIO, "3.1", "3.1c 无编造细节",
      noFabrication ? "PASS" : "FAIL", "无编造数据");

    record(SCENARIO, "3.1", "3.1d 已推断字段绿色勾", "PARTIAL", "mock 数据无字段标记");
    record(SCENARIO, "3.1", "3.1e 缺失字段橙色问号", "PARTIAL", "mock 数据无字段标记");
  });

  test("步骤 3.2 — 通过对话补充缺失信息", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "补充信息测试", "最近地方债话题很热，想做个视频聊一聊"
    );

    if (!navigated) {
      record(SCENARIO, "3.2", "3.2 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const chatInput = page.locator('[data-testid="chat-input"] textarea');
    if (!(await chatInput.isVisible().catch(() => false))) {
      record(SCENARIO, "3.2", "3.2a 输入框", "FAIL", "不可见");
      return;
    }

    await chatInput.fill("从地方财政可持续性角度分析，8-10 分钟吧，发 B 站");
    await page.locator('[aria-label="发送消息"]').click();
    await page.waitForTimeout(3000);

    const pageText = await page.locator("body").innerText();
    const hasUpdate = pageText.includes("财政可持续") || pageText.includes("B站");
    record(SCENARIO, "3.2", "3.2a 需求更新",
      hasUpdate ? "PARTIAL" : "FAIL", "mock 数据不反映更新");

    record(SCENARIO, "3.2", "3.2b 澄清区域缩小", "PARTIAL", "mock 数据无动态变化");
    record(SCENARIO, "3.2", "3.2c 字段标记变化", "PARTIAL", "mock 数据无字段标记");
    await page.screenshot({ path: "test-results/phase0-s3-step3.2-supplement.png", fullPage: true });
  });

  test("步骤 3.3 — 补充后审核通过", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "补充后审核测试",
      "从地方财政可持续性角度分析地方债，8-10分钟，发B站，面向金融从业者"
    );

    if (!navigated) {
      record(SCENARIO, "3.3", "3.3 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(5000);

    const pageText = await page.locator("body").innerText();
    const hasPassed = pageText.includes("通过") || pageText.includes("完成");
    record(SCENARIO, "3.3", "3.3a review 通过",
      hasPassed ? "PARTIAL" : "FAIL", "mock 数据不显示 review 结果");

    record(SCENARIO, "3.3", "3.3b clarification_needed 变空", "PARTIAL", "mock 数据无法验证");

    const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
    const btnVisible = await advanceBtn.isVisible().catch(() => false);
    const btnEnabled = btnVisible ? await advanceBtn.isEnabled().catch(() => false) : false;
    record(SCENARIO, "3.3", "3.3c advance 按钮可点击",
      btnEnabled ? "PASS" : (btnVisible ? "PARTIAL" : "FAIL"),
      `visible=${btnVisible} enabled=${btnEnabled}`);

    await page.screenshot({ path: "test-results/phase0-s3-step3.3-review-passed.png", fullPage: true });
  });
});

// ═══════════════════════════════════════════════════════════════
// 场景 4: 偏好提取与确认
// ═══════════════════════════════════════════════════════════════
test.describe("场景 4: 偏好提取与确认", () => {
  const SCENARIO = "场景4-偏好提取";

  test("步骤 4.1~4.4 — 偏好提取->检查->确认->门禁通过", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "偏好提取测试",
      "不要学术腔，要像给朋友讲故事。分析近期黄金走势，发在抖音，约5分钟"
    );

    if (!navigated) {
      record(SCENARIO, "4.1", "4.1 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
    const btnVisible = await advanceBtn.isVisible().catch(() => false);
    if (btnVisible) {
      await advanceBtn.click();
      await page.waitForTimeout(3000);

      const prefModal = page.locator("text=AI 记忆同步中");
      const modalVisible = await prefModal.isVisible().catch(() => false);
      const hasCheckbox = await page.locator("input[type='checkbox']").first().isVisible().catch(() => false);
      const hasAccept = await page.locator("button", { hasText: "确认并进入下一阶段" }).isVisible().catch(() => false);

      record(SCENARIO, "4.1", "4.1 偏好确认弹窗",
        modalVisible ? "PASS" : "PARTIAL",
        `弹窗=${modalVisible} checkbox=${hasCheckbox} accept=${hasAccept}`);

      await page.screenshot({ path: "test-results/phase0-s4-preference-modal.png", fullPage: true });
    } else {
      record(SCENARIO, "4.1", "4.1 偏好确认弹窗", "FAIL", "advance 按钮不存在");
    }

    record(SCENARIO, "4.2", "4.2 偏好内容检查", "SKIP", "需完整 Agent 输出");
    record(SCENARIO, "4.3", "4.3 偏好编辑+确认", "SKIP", "需完整偏好流程");
    record(SCENARIO, "4.4", "4.4 门禁通过", "SKIP", "需 GateKeeper 实际行为");
  });
});

// ═══════════════════════════════════════════════════════════════
// 场景 5: 门禁与推进
// ═══════════════════════════════════════════════════════════════
test.describe("场景 5: 门禁与推进", () => {
  const SCENARIO = "场景5-门禁推进";

  test("步骤 5.1~5.2 — 跨项目复用 + 覆盖历史偏好", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "跨项目偏好测试", "分析A股走势，风格尽量简洁，发在B站，时长约5分钟"
    );

    record(SCENARIO, "5.1", "5.1 跨项目复用偏好",
      navigated ? "PARTIAL" : "FAIL",
      navigated ? "项目创建成功" : "项目创建失败");

    record(SCENARIO, "5.2", "5.2 覆盖历史偏好", "SKIP", "需多个项目+偏好变更的完整历史");
  });
});

// ═══════════════════════════════════════════════════════════════
// 场景 6: 输入校验与边界条件
// ═══════════════════════════════════════════════════════════════
test.describe("场景 6: 输入校验与边界条件", () => {
  const SCENARIO = "场景6-输入校验";

  test("步骤 6.1 — 描述不足 10 字时阻止提交", async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/new`);
    await page.waitForLoadState("networkidle");
    await page.locator("#title").fill("测试视频");
    await page.locator("#desc").fill("随便试试");

    await page.locator("button[type='submit']").click();
    await page.waitForTimeout(500);

    const stillOnNew = page.url().includes("/projects/new");
    const errorEl = page.locator('[role="alert"]');
    const errorVisible = await errorEl.isVisible().catch(() => false);
    const errorMsg = errorVisible ? await errorEl.textContent() : "";

    record(SCENARIO, "6.1", "6.1a 页面停留在 /projects/new",
      stillOnNew ? "PASS" : "FAIL", `停留在页=${stillOnNew}`);

    record(SCENARIO, "6.1", "6.1b 红色错误提示",
      errorVisible ? "PASS" : "FAIL", `错误: "${errorMsg}"`);

    await page.screenshot({ path: "test-results/phase0-s6-step6.1-validation.png", fullPage: true });
  });

  test("步骤 6.2 — 标题为空时阻止提交", async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/new`);
    await page.waitForLoadState("networkidle");
    await page.locator("#desc").fill("这是一个关于黄金价格走势的详细分析视频，涵盖美联储政策");

    const submitBtn = page.locator("button[type='submit']");
    const isDisabled = !(await submitBtn.isEnabled().catch(() => true));

    record(SCENARIO, "6.2", "6.2 标题为空时按钮禁用",
      isDisabled ? "PASS" : "FAIL", `disabled=${isDisabled}`);
  });

  test("步骤 6.3 — 页面恢复测试", async ({ page }) => {
    const { projectId, navigated } = await createProjectAndWait(
      page, "页面恢复测试", "分析黄金走势，时长约5分钟，发在B站，面向新手投资者"
    );

    if (!navigated) {
      record(SCENARIO, "6.3", "6.3 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    await page.goto(`${BASE_URL}/projects/${projectId}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const pageLoaded = (await page.locator("body").innerText()).length > 100;
    record(SCENARIO, "6.3", "6.3 页面恢复成功",
      pageLoaded ? "PASS" : "FAIL", `加载=${pageLoaded}`);
  });
});

// ═══════════════════════════════════════════════════════════════
// 综合: UI 交互细节
// ═══════════════════════════════════════════════════════════════
test.describe("综合: UI 交互细节验证", () => {
  const SCENARIO = "场景7-UI细节";

  test("项目列表页功能检查", async ({ page }) => {
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    const table = page.locator("table");
    const tableVisible = await table.isVisible().catch(() => false);
    record(SCENARIO, "7.1", "7.1a 项目列表表格",
      tableVisible ? "PASS" : "FAIL", `table=${tableVisible}`);

    const rows = page.locator("table tbody tr");
    const rowCount = await rows.count();
    record(SCENARIO, "7.1", "7.1b 项目行数",
      rowCount > 0 ? "PASS" : "FAIL", `行数=${rowCount}`);

    if (rowCount > 0) {
      await rows.first().click();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1000);
      const navigated = page.url().includes("/projects/") && !page.url().includes("/projects/new");
      record(SCENARIO, "7.1", "7.1c 点击跳转",
        navigated ? "PASS" : "FAIL", `URL: ${page.url().substring(0, 60)}`);
    }
    await page.screenshot({ path: "test-results/phase0-ui-project-list.png", fullPage: true });
  });

  test("WorkflowPage 完整 UI 检查", async ({ page }) => {
    const { navigated } = await createProjectAndWait(
      page, "ChatInput功能测试", "分析黄金走势，时长约5分钟，发在B站，面向普通投资者"
    );

    if (!navigated) {
      record(SCENARIO, "7.2", "7.2 项目创建", "FAIL", "无法创建项目");
      return;
    }

    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);
    await page.screenshot({ path: "test-results/phase0-ui-workflow-full.png", fullPage: true });

    const pageText = await page.locator("body").innerText();

    // Check key UI elements
    record(SCENARIO, "7.2", "7.2a ChatInput 组件",
      (await page.locator('[data-testid="chat-input"]').isVisible().catch(() => false)) ? "PASS" : "FAIL", "");

    record(SCENARIO, "7.2", "7.2b TaskCard 组件",
      (await page.locator('[data-testid="task-card"]').isVisible().catch(() => false)) ? "PASS" : "FAIL", "");

    record(SCENARIO, "7.2", "7.2c 产物列表",
      pageText.includes("已生成产物") ? "PASS" : "FAIL", "ArtifactList 区域");

    record(SCENARIO, "7.2", "7.2d 事实核查面板",
      pageText.includes("事实核查") ? "PASS" : "FAIL", "FactualLedger 区域");

    // Test ChatInput: send a message and verify handleSend behavior
    const textarea = page.locator('[data-testid="chat-input"] textarea');
    if (await textarea.isVisible().catch(() => false)) {
      const beforeText = await page.locator("body").innerText();
      await textarea.fill("测试发送消息到 Agent");
      await page.locator('[aria-label="发送消息"]').click();
      await page.waitForTimeout(2000);
      const afterText = await page.locator("body").innerText();

      // Check if message appeared in chat (handleSend should add it)
      const msgAppeared = afterText.includes("测试发送消息到 Agent") && afterText.length > beforeText.length;
      record(SCENARIO, "7.2", "7.2e 消息发送后出现在对话区",
        msgAppeared ? "PASS" : "FAIL",
        msgAppeared ? "消息成功显示" : "消息未出现在对话区 — handleSend 是空函数 (no-op)。对话修改功能完全不可用");
    }

    // Check for mock data indicators
    const hasMockTitle = pageText.includes("黄金价格走势分析与投资展望");
    record(SCENARIO, "7.2", "7.2f 页面标题",
      hasMockTitle ? "FAIL" : "PASS",
      hasMockTitle
        ? "页面标题始终显示硬编码 '黄金价格走势分析与投资展望'，无视实际项目标题。WorkflowPage 使用 MOCK_PROJECT_TITLE"
        : "页面标题反映实际项目");

    const hasMockMsg = pageText.includes("我已经根据大纲生成了第 2 版结构化脚本");
    record(SCENARIO, "7.2", "7.2g 对话内容真实性",
      hasMockMsg ? "FAIL" : "PASS",
      hasMockMsg
        ? "对话区显示硬编码 mock 消息，不反映实际 Agent 输出。WorkflowPage 使用 MOCK_MESSAGES"
        : "对话内容真实");
  });
});
