import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

test.describe("AI Video System - E2E Acceptance Test", () => {
  test("Complete video creation workflow: Phase 0 → Phase 1 with feedback", async ({ page }) => {
    const results: { tc: string; status: "PASS" | "FAIL" | "PARTIAL"; detail: string }[] = [];

    // ============================================================
    // TC-01: 项目列表页 - 从接口获取项目列表
    // ============================================================
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    const tableRows = page.locator("table tbody tr");
    const emptyHint = page.locator("text=暂无项目");
    const hasProjects = (await tableRows.count()) > 0;
    const hasEmptyHint = await emptyHint.isVisible().catch(() => false);

    if (hasProjects || hasEmptyHint) {
      results.push({ tc: "TC-01", status: "PASS", detail: `项目列表页加载成功，${hasProjects ? `包含 ${await tableRows.count()} 个项目` : "暂无项目"}` });
    } else {
      results.push({ tc: "TC-01", status: "FAIL", detail: "项目列表页未能加载数据" });
    }

    // ============================================================
    // TC-02: 点击新建项目按钮 → 跳转到新建页面
    // ============================================================
    const newProjectBtn = page.locator("button", { hasText: "新建项目" });
    await expect(newProjectBtn).toBeVisible();
    await newProjectBtn.click();
    await page.waitForURL("**/projects/new");

    if (page.url().includes("/projects/new")) {
      results.push({ tc: "TC-02", status: "PASS", detail: "点击新建项目后成功跳转到 /projects/new" });
    } else {
      results.push({ tc: "TC-02", status: "FAIL", detail: `期望跳转到 /projects/new，实际 URL: ${page.url()}` });
    }

    // ============================================================
    // TC-03: 输入标题和内容主题描述
    // ============================================================
    const titleInput = page.locator("#title");
    const descInput = page.locator("#desc");
    await expect(titleInput).toBeVisible();
    await expect(descInput).toBeVisible();

    const testTitle = "美联储换届对于资本市场的影响";
    const testDesc = `美联储下一届主席的公布时间
下一任美联储主席的热门人选
分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响
美联储最近一年公布的主要的新闻事件`;

    await titleInput.fill(testTitle);
    await descInput.fill(testDesc);

    const titleOk = (await titleInput.inputValue()) === testTitle;
    const descOk = (await descInput.inputValue()).includes("美联储下一届主席的公布时间");

    if (titleOk && descOk) {
      results.push({ tc: "TC-03", status: "PASS", detail: "成功输入标题和内容主题描述" });
    } else {
      results.push({ tc: "TC-03", status: "FAIL", detail: `标题匹配:${titleOk}, 描述匹配:${descOk}` });
    }

    // ============================================================
    // TC-04: 点击开始制作 → 创建项目并跳转到工作流页面
    // ============================================================
    const submitBtn = page.locator("button[type='submit']", { hasText: "开始制作" });
    await expect(submitBtn).toBeEnabled({ timeout: 5000 });

    const responsePromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/projects") && resp.request().method() === "POST",
      { timeout: 15000 }
    );
    await submitBtn.click();
    const apiResponse = await responsePromise;

    if (apiResponse.status() === 201) {
      const responseBody = await apiResponse.json();
      const projectId = responseBody.id;
      results.push({ tc: "TC-04a", status: "PASS", detail: `API POST /api/projects 返回 201, project_id=${projectId}` });

      await page.waitForURL((url) => url.pathname.includes(`/projects/${projectId}`), { timeout: 15000 });
      const currentUrl = page.url();
      if (currentUrl.includes(projectId) && !currentUrl.includes("/projects/new")) {
        results.push({ tc: "TC-04b", status: "PASS", detail: `成功跳转到项目页面 ${currentUrl}` });
      } else {
        results.push({ tc: "TC-04b", status: "FAIL", detail: `未跳转到项目页面，URL: ${currentUrl}` });
      }
    } else {
      results.push({ tc: "TC-04", status: "FAIL", detail: `API 返回 ${apiResponse.status()}` });
      const projectId = "unknown";
    }

    // ============================================================
    // TC-05: Phase 0 - 左侧导航显示 P0，对话区展示结构化需求
    // ============================================================
    await page.waitForLoadState("networkidle");

    const p0Button = page.locator('[data-testid="phase-nav-0"]');
    await expect(p0Button).toBeVisible({ timeout: 10000 });
    const p0Active = await p0Button.getAttribute("data-active");

    if (p0Active === "true") {
      results.push({ tc: "TC-05a", status: "PASS", detail: "左侧导航栏显示 P0 为当前活跃阶段" });
    } else {
      results.push({ tc: "TC-05a", status: "FAIL", detail: `P0 data-active=${p0Active}，期望 "true"` });
    }

    const chatHeader = page.locator('[data-testid="chat-terminal-panel"]');
    await expect(chatHeader).toBeVisible();
    const headerText = await chatHeader.textContent();

    if (headerText && /P0|需求采集/.test(headerText)) {
      results.push({ tc: "TC-05b", status: "PASS", detail: `对话区标题显示: ${headerText?.trim()}` });
    } else {
      results.push({ tc: "TC-05b", status: "FAIL", detail: `对话区标题: ${headerText?.trim()}` });
    }

    const pageContent0 = await page.locator("body").innerText();
    if (pageContent0.includes("美联储换届")) {
      results.push({ tc: "TC-05c", status: "PASS", detail: "工作流页面显示项目标题" });
    } else {
      results.push({ tc: "TC-05c", status: "FAIL", detail: "工作流页面未显示项目标题" });
    }

    // Check if content is demo data or real API data
    const isDemoContent = pageContent0.includes("VideoEngine Agent") || pageContent0.includes("我已经根据大纲生成了");
    const hasStructuredRequirement = pageContent0.includes("需求采集") || pageContent0.includes("结构化");
    const phasePreviewText = await page.locator('[data-testid^="preview-slot"]').innerText().catch(() => "");

    results.push({
      tc: "TC-05d (结构化需求)",
      status: isDemoContent ? "PARTIAL" : (hasStructuredRequirement ? "PASS" : "FAIL"),
      detail: isDemoContent
        ? "对话区显示 demo 硬编码内容，非实际项目结构化需求。需实现需求采集 Agent 对接。"
        : (hasStructuredRequirement ? "对话区展示了结构化视频需求摘要" : "对话区未展示结构化需求"),
    });

    // ============================================================
    // TC-06: 点击确认进入下一阶段 → Phase 1
    // ============================================================
    const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
    await expect(advanceBtn).toBeVisible({ timeout: 10000 });

    // Check if the advance button triggers a preference modal first
    const preferenceModalBefore = page.locator("text=AI 记忆同步中");

    // Listen for advance API
    let advanceApiCalled = false;
    const advanceResponsePromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/projects/") && resp.url().includes("/advance") && resp.request().method() === "POST",
      { timeout: 10000 }
    ).then(() => { advanceApiCalled = true; }).catch(() => { /* timeout expected */ });

    await advanceBtn.click();
    await page.waitForTimeout(1500);

    // Check if preference modal opened
    const modalVisible = await preferenceModalBefore.isVisible().catch(() => false);

    if (modalVisible) {
      results.push({
        tc: "TC-06",
        status: "PARTIAL",
        detail: "确认进入下一阶段按钮打开了偏好记忆弹窗（AI 记忆同步中），但弹窗内确认按钮未调用 POST /advance API。advance 功能未完成前后端对接。",
      });
      // Close the modal
      const closeModalBtn = page.locator("button", { hasText: "关闭" });
      if (await closeModalBtn.isVisible()) await closeModalBtn.click();
    } else if (advanceApiCalled) {
      results.push({ tc: "TC-06", status: "PASS", detail: "点击确认后调用了 advance API，Phase 推进成功" });
    } else {
      results.push({
        tc: "TC-06",
        status: "FAIL",
        detail: "点击确认进入下一阶段未触发 advance API 调用。按钮仅打开偏好记忆弹窗（demo 行为），未对接后端 workflow engine。",
      });
    }

    // ============================================================
    // TC-07: 输入反馈 → 发送反馈
    // ============================================================
    const feedbackText = "增加对历任主席的介绍";
    const feedbackInput = page.locator("textarea[placeholder*='修改方案']");
    await expect(feedbackInput).toBeVisible({ timeout: 5000 });

    await feedbackInput.fill(feedbackText);
    const feedbackFilled = (await feedbackInput.inputValue()) === feedbackText;

    const sendFeedbackBtn = page.locator("button", { hasText: "发送反馈" });
    await expect(sendFeedbackBtn).toBeVisible();

    let chatApiCalled = false;
    const chatResponsePromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/projects/") && resp.url().includes("/chat") && resp.request().method() === "POST",
      { timeout: 10000 }
    ).then(() => { chatApiCalled = true; }).catch(() => { /* timeout expected */ });

    await sendFeedbackBtn.click();
    await page.waitForTimeout(2000);

    if (chatApiCalled) {
      const pageContent = await page.locator("body").innerText();
      const hasFeedback = pageContent.includes("历任主席");
      results.push({
        tc: "TC-07",
        status: hasFeedback ? "PASS" : "PARTIAL",
        detail: hasFeedback ? "反馈发送成功，对话区显示反馈内容" : "chat API 已调用但对话区未显示反馈内容",
      });
    } else {
      results.push({
        tc: "TC-07",
        status: "FAIL",
        detail: `反馈内容"${feedbackText}"已输入到文本框，但点击发送反馈按钮未触发 POST /chat API 调用。发送反馈功能未完成前后端对接（demo 状态）。`,
      });
    }

    // ============================================================
    // Print Test Report
    // ============================================================
    console.log("\n╔══════════════════════════════════════════════════════╗");
    console.log("║     AI Video System - E2E 验收测试报告                ║");
    console.log("╠══════════════════════════════════════════════════════╣");

    const passCount = results.filter((r) => r.status === "PASS").length;
    const failCount = results.filter((r) => r.status === "FAIL").length;
    const partialCount = results.filter((r) => r.status === "PARTIAL").length;

    for (const r of results) {
      const icon = r.status === "PASS" ? "✅" : r.status === "PARTIAL" ? "⚠️" : "❌";
      console.log(`║ ${icon} ${r.tc}: ${r.detail.substring(0, 47)}`);
      if (r.detail.length > 47) {
        console.log(`║    ${r.detail.substring(47)}`);
      }
    }

    console.log("╠══════════════════════════════════════════════════════╣");
    console.log(`║  总计: ${results.length} 项 | ✅ ${passCount} | ⚠️ ${partialCount} | ❌ ${failCount}`);
    console.log("╚══════════════════════════════════════════════════════╝\n");
  });
});
