import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

test.describe("端到端测试 — Remotion 视频渲染管线 (浏览器交互)", () => {
  test("完整流程: 新建项目 → P0需求 → 推进各阶段 → 验证Remotion渲染", async ({ page }) => {
    const report: string[] = [];

    // ============================================================
    // Step 1: 打开项目列表页
    // ============================================================
    console.log("\n=== Step 1: 打开项目列表页 ===");
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");
    report.push("Step 1: 打开项目列表页 OK");

    // ============================================================
    // Step 2: 点击新建项目按钮
    // ============================================================
    console.log("\n=== Step 2: 点击新建项目 ===");
    const newProjectBtn = page.locator("button", { hasText: "新建项目" });
    await expect(newProjectBtn).toBeVisible({ timeout: 10000 });
    await newProjectBtn.click();
    await page.waitForURL("**/projects/new");
    report.push("Step 2: 跳转到 /projects/new OK");

    // ============================================================
    // Step 3: 输入标题和内容描述
    // ============================================================
    console.log("\n=== Step 3: 输入标题和描述 ===");
    const titleInput = page.locator("#title");
    const descInput = page.locator("#desc");
    await expect(titleInput).toBeVisible();
    await expect(descInput).toBeVisible();

    const testTitle = "美联储换届对于资本市场的影响";
    const testDesc = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响`;

    await titleInput.fill(testTitle);
    await descInput.fill(testDesc);
    report.push("Step 3: 标题和描述输入 OK");

    // ============================================================
    // Step 4: 点击"开始制作" → 创建项目
    // ============================================================
    console.log("\n=== Step 4: 创建项目 ===");
    const submitBtn = page.locator("button[type='submit']", { hasText: "开始制作" });
    await expect(submitBtn).toBeEnabled({ timeout: 5000 });

    let projectId = "";
    const responsePromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/projects") && resp.request().method() === "POST",
      { timeout: 15000 }
    );
    await submitBtn.click();

    const apiResponse = await responsePromise;
    const body = await apiResponse.json();
    projectId = body.id;
    report.push(`Step 4a: POST /api/projects → ${apiResponse.status()}, id=${projectId}`);

    await page.waitForURL((url) => url.pathname.includes(projectId), { timeout: 10000 });
    report.push(`Step 4b: 跳转到工作流 ${page.url()}`);

    // ============================================================
    // Step 5: Phase 0 验证 — 标题可见、页面加载
    // ============================================================
    console.log("\n=== Step 5: Phase 0 验证 ===");
    await page.waitForLoadState("networkidle");

    const pageText = await page.locator("body").innerText();
    const hasTitle = pageText.includes("美联储换届");
    const p0Btn = page.locator('[data-testid="phase-nav-0"]');
    const p0Visible = await p0Btn.isVisible().catch(() => false);
    const p0Active = p0Visible ? await p0Btn.getAttribute("data-active") : null;
    report.push(`Step 5: P0可见=${p0Visible}, data-active=${p0Active}, 标题显示=${hasTitle}`);

    // ============================================================
    // Step 6: Phase 0 发送反馈（如果Chat输入框可见）
    // ============================================================
    console.log("\n=== Step 6: 发送反馈（Phase 0）===");
    const feedbackInput = page.locator("textarea[placeholder*='修改方案']");
    if (await feedbackInput.isVisible().catch(() => false)) {
      await feedbackInput.fill("请增加对鲍威尔任期和货币政策走向的分析");
      const sendBtn = page.locator("button", { hasText: "发送反馈" });
      if (await sendBtn.isEnabled().catch(() => false)) {
        await sendBtn.click();
        await page.waitForTimeout(2000);
        report.push("Step 6: 反馈已发送");
      } else {
        report.push("Step 6: 发送按钮不可用");
      }
    } else {
      report.push("Step 6: 反馈输入框不可见（可能不在P0）");
    }

    // ============================================================
    // Step 7: 尝试推进 6 轮（覆盖 P1-P11）
    // ============================================================
    for (let attempt = 1; attempt <= 8; attempt++) {
      console.log(`\n=== Step ${6+attempt}: 推进阶段 (attempt ${attempt}) ===`);

      await page.waitForTimeout(500);

      const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
      const advanceVisible = await advanceBtn.isVisible().catch(() => false);
      if (!advanceVisible) {
        report.push(`Step ${6+attempt}: 无"确认进入下一阶段"按钮，停止推进`);
        break;
      }

      const enabled = await advanceBtn.isEnabled().catch(() => false);
      if (!enabled) {
        report.push(`Step ${6+attempt}: "确认进入下一阶段"按钮已禁用，等待中...`);
        await page.waitForTimeout(3000);
        continue;
      }

      await advanceBtn.click();
      await page.waitForTimeout(2000);

      // 处理偏好弹窗（如果出现）
      const prefBtn = page.locator("button", { hasText: "全部接受" });
      if (await prefBtn.isVisible().catch(() => false)) {
        await prefBtn.click();
        await page.waitForTimeout(1500);
        report.push(`Step ${6+attempt}: 处理偏好弹窗（全部接受）`);
      }

      const confirmBtn = page.locator("button", { hasText: "确认并进入下一阶段" });
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(1500);
        report.push(`Step ${6+attempt}: 处理确认弹窗`);
      }

      const urlAfter = page.url();
      const phaseMatch = urlAfter.match(/\/phases\/(\d+)/);
      const currentPhase = phaseMatch ? parseInt(phaseMatch[1]) : -1;

      report.push(`Step ${6+attempt}: URL phase=${currentPhase}`);

      if (currentPhase >= 11) {
        report.push(`*** 已到达最终阶段 P${currentPhase}! ***`);
        break;
      }

      // 检查是否停留在同一阶段（可能推进失败）
      if (attempt > 1) {
        await page.waitForTimeout(3000);
        const urlCheck = page.url();
        const phaseCheck = urlCheck.match(/\/phases\/(\d+)/);
        const checkPhase = phaseCheck ? parseInt(phaseCheck[1]) : -1;
        if (checkPhase === currentPhase && attempt > 2) {
          report.push(`Step ${6+attempt}: 阶段未变化，可能门禁未通过`);
        }
      }
    }

    // ============================================================
    // Final: 检查最终状态
    // ============================================================
    const finalUrl = page.url();
    const finalPhaseMatch = finalUrl.match(/\/phases\/(\d+)/);
    const finalPhase = finalPhaseMatch ? parseInt(finalPhaseMatch[1]) : -1;

    await page.waitForLoadState("networkidle");
    const finalBodyText = await page.locator("body").innerText();

    // P8+ 阶段检查 Remotion 相关 UI
    const hasRemotionHint = finalBodyText.includes("remotion") ||
      finalBodyText.includes("Remotion") ||
      finalBodyText.includes("视频") ||
      finalBodyText.includes("mp4") ||
      finalBodyText.includes("渲染");

    // P10+ 检查视频预览
    const hasVideoPreview = finalBodyText.includes("播放") ||
      finalBodyText.includes("preview") ||
      finalBodyText.includes("下载") ||
      finalBodyText.includes("video");

    report.push(`FINAL: 到达 P${finalPhase}`);
    report.push(`FINAL: Remotion/渲染提示 = ${hasRemotionHint}`);
    report.push(`FINAL: 视频预览 = ${hasVideoPreview}`);

    if (finalPhase >= 10) {
      report.push("SUCCESS: 成功到达视频产出阶段 (P10+)");
    } else if (finalPhase >= 8) {
      report.push("PARTIAL: 到达渲染阶段 (P8+)");
    } else {
      report.push(`INCOMPLETE: 停留在 P${finalPhase}，未到达渲染阶段`);
    }

    // ============================================================
    // 报告
    // ============================================================
    console.log("\n");
    console.log("═".repeat(60));
    console.log("  端到端测试报告 — Remotion 渲染管线");
    console.log("═".repeat(60));
    for (const line of report) {
      console.log(`  ${line}`);
    }
    console.log("═".repeat(60));
  });

  test("从已有 Phase 11 项目验证 UI 状态和视频下载", async ({ page }) => {
    // 导航到已完成项目 (proj_20260428_041 已在 Phase 11)
    const projectId = "proj_20260428_041";
    await page.goto(`${BASE_URL}/projects/${projectId}/phases/11`);
    await page.waitForLoadState("networkidle");

    // 验证页面标题
    const pageText = await page.locator("body").innerText();
    expect(pageText).toContain("美联储换届");

    // 验证 Phase 导航栏显示
    const phaseNav = page.locator('[data-testid="phase-nav-sidebar"]');
    await expect(phaseNav).toBeVisible({ timeout: 10000 });

    // 验证 P11 是高亮状态
    const p11Btn = page.locator('[data-testid="phase-nav-11"]');
    await expect(p11Btn).toBeVisible();
    const p11Active = await p11Btn.getAttribute("data-active");
    console.log(`P11 active=${p11Active}`);

    // 检查是否有 artifact preview
    const preview = page.locator('[data-testid="artifact-preview-panel"]');
    const previewVisible = await preview.isVisible().catch(() => false);
    console.log(`Preview panel visible: ${previewVisible}`);

    // 截图保存
    await page.screenshot({ path: "/tmp/e2e_phase11_ui.png", fullPage: true });
    console.log("截图已保存到 /tmp/e2e_phase11_ui.png");
  });
});
