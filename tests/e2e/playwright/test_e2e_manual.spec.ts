import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:3005";

test.describe("E2E - 美联储换届资本市场影响 完整流程测试", () => {
  test("创建项目 → P0需求 → 逐步推进直到视频产出", async ({ page }) => {
    const report: string[] = [];
    let projectId = "";

    // ============================================================
    // Step 1: 项目列表页
    // ============================================================
    console.log("\n=== Step 1: 项目列表页 ===");
    await page.goto(`${BASE_URL}/projects`, { waitUntil: "networkidle", timeout: 15000 });
    await page.waitForTimeout(1000);
    const pageTitle1 = await page.title();
    report.push(`Step 1: 页面标题="${pageTitle1}", URL=${page.url()}`);

    // ============================================================
    // Step 2: 点击"新建项目"按钮
    // ============================================================
    console.log("\n=== Step 2: 新建项目 ===");
    const newProjectBtn = page.locator("button, a").filter({ hasText: /新建项目/ }).first();
    const newProjectVisible = await newProjectBtn.isVisible({ timeout: 5000 }).catch(() => false);
    if (!newProjectVisible) {
      // Try to find it by link
      const bodyText = await page.locator("body").innerText();
      report.push(`Step 2: "新建项目"按钮不可见! Body text: ${bodyText.substring(0, 200)}`);
      // Try navigate directly
      await page.goto(`${BASE_URL}/projects/new`, { waitUntil: "networkidle" });
      report.push(`Step 2: 直接导航到 /projects/new`);
    } else {
      await newProjectBtn.click();
      await page.waitForURL("**/projects/new", { timeout: 10000 });
      report.push(`Step 2: 点击"新建项目", 跳转到 ${page.url()}`);
    }

    // ============================================================
    // Step 3: 输入标题和内容
    // ============================================================
    console.log("\n=== Step 3: 输入内容 ===");
    await page.waitForTimeout(1000);

    // Find input fields - try multiple selectors
    const titleInput = page.locator("input#title, input[name='title'], input[placeholder*='标题']").first();
    const descInput = page.locator("textarea#desc, textarea[name='description'], textarea[placeholder*='描述'], textarea").first();

    const titleVisibility = await titleInput.isVisible({ timeout: 5000 }).catch(() => false);
    const descVisibility = await descInput.isVisible({ timeout: 3000 }).catch(() => false);

    report.push(`Step 3: titleInput可见=${titleVisibility}, descInput可见=${descVisibility}`);

    if (!titleVisibility || !descVisibility) {
      // Dump all input fields for debugging
      const inputs = await page.evaluate(() => {
        return Array.from(document.querySelectorAll("input, textarea")).map(el => ({
          tag: el.tagName,
          id: el.id,
          name: (el as any).name,
          placeholder: (el as any).placeholder,
          type: (el as any).type,
        }));
      });
      report.push(`Step 3: 找到的input元素: ${JSON.stringify(inputs)}`);

      if (!titleVisibility && !descVisibility) {
        report.push("Step 3: 无法找到输入字段，终止测试");
        console.log(report.join("\n"));
        return;
      }
    }

    const testTitle = "美联储换届对于资本市场的影响";
    const testDesc = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响`;

    if (titleVisibility) {
      await titleInput.fill(testTitle);
      report.push("Step 3a: 标题填写完成");
    }
    if (descVisibility) {
      await descInput.fill(testDesc);
      report.push("Step 3b: 描述填写完成");
    }

    // ============================================================
    // Step 4: 提交创建项目
    // ============================================================
    console.log("\n=== Step 4: 创建项目 ===");
    const submitBtn = page.locator("button[type='submit'], button").filter({ hasText: /开始制作|创建|提交|确认/ }).first();
    const submitVisible = await submitBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (!submitVisible) {
      report.push("Step 4: 提交按钮不可见!");
      const buttons = await page.evaluate(() =>
        Array.from(document.querySelectorAll("button")).map(b => b.textContent?.trim())
      );
      report.push(`Step 4: 页面按钮: ${JSON.stringify(buttons)}`);
    } else {
      // Intercept API response
      const responsePromise = page.waitForResponse(
        (resp) => resp.url().includes("/api/projects") && resp.request().method() === "POST",
        { timeout: 15000 }
      ).catch(() => null);

      await submitBtn.click();
      const apiResp = await responsePromise;

      if (apiResp) {
        try {
          const body = await apiResp.json();
          projectId = body.id;
          report.push(`Step 4: POST /api/projects → status=${apiResp.status()}, id=${projectId}`);
        } catch {
          report.push(`Step 4: POST /api/projects → status=${apiResp.status()} (no JSON body)`);
        }
      } else {
        report.push("Step 4: 未捕获到 POST /api/projects 响应");
      }
    }

    // Wait for redirect to project workflow
    await page.waitForTimeout(3000);
    report.push(`Step 4b: 当前URL=${page.url()}`);

    // ============================================================
    // Step 5: Check project state via the page
    // ============================================================
    console.log("\n=== Step 5: 检查项目状态 ===");
    await page.waitForTimeout(2000);

    // Get full page text for analysis
    const bodyText = await page.locator("body").innerText();
    report.push(`Step 5: 页面内容前500字: ${bodyText.substring(0, 500)}`);

    // Check current phase from URL
    const urlPhaseMatch = page.url().match(/\/phases\/(\d+)/);
    const urlPhase = urlPhaseMatch ? parseInt(urlPhaseMatch[1]) : -1;
    report.push(`Step 5: URL中phase=${urlPhase}`);

    // ============================================================
    // Step 6: Try to advance through phases
    // ============================================================
    console.log("\n=== Step 6: 尝试推进阶段 ===");

    for (let attempt = 1; attempt <= 12; attempt++) {
      await page.waitForTimeout(1000);

      const currentUrl = page.url();
      const phaseMatch = currentUrl.match(/\/phases\/(\d+)/);
      const currentPhase = phaseMatch ? parseInt(phaseMatch[1]) : -1;

      // Look for advance/confirm button
      const advanceBtn = page.locator("button").filter({ hasText: /确认进入下一阶段|推进|下一阶段|advance|next phase/i }).first();
      const advanceVisible = await advanceBtn.isVisible({ timeout: 3000 }).catch(() => false);

      if (!advanceVisible) {
        // Try more generic buttons
        const allButtons = await page.evaluate(() =>
          Array.from(document.querySelectorAll("button")).map(b => ({
            text: b.textContent?.trim().substring(0, 60),
            disabled: (b as HTMLButtonElement).disabled,
          }))
        );
        report.push(`Step 6.${attempt}: P${currentPhase} - "确认推进"按钮不可见. 所有按钮: ${JSON.stringify(allButtons.slice(0, 10))}`);

        // Check if we're at a terminal phase
        if (currentPhase >= 11) {
          report.push(`Step 6.${attempt}: 已在P${currentPhase}(最终阶段)!`);
          break;
        }

        // Check page state
        const pageState = bodyText.substring(0, 300);
        if (pageState.includes("已完成") || pageState.includes("completed")) {
          report.push(`Step 6.${attempt}: 项目可能已完成`);
          break;
        }

        // If stuck, try looking for chat input to send message
        const chatInput = page.locator("textarea, input[type='text']").filter({ hasText: "" }).first();
        if (await chatInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          report.push(`Step 6.${attempt}: 发现chat输入框，可能是等待用户交互`);
        }

        break;
      }

      // Click advance
      if (await advanceBtn.isEnabled({ timeout: 2000 }).catch(() => false)) {
        let advanceResult = "unknown";
        const advancePromise = page.waitForResponse(
          (resp) => resp.url().includes("/advance") && resp.request().method() === "POST",
          { timeout: 15000 }
        ).then(async (resp) => {
          try {
            const b = await resp.json();
            advanceResult = `status=${resp.status()}, phase=${b.phase || b.current_phase || '?'}`;
          } catch {
            advanceResult = `status=${resp.status()}`;
          }
        }).catch(() => { advanceResult = "no_api_response"; });

        await advanceBtn.click();
        await page.waitForTimeout(2000);

        // Handle any preference/confirmation modal
        const confirmModalBtn = page.locator("button").filter({ hasText: /确认|接受|保存|跳过|推进/ }).first();
        if (await confirmModalBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmModalBtn.click();
          await page.waitForTimeout(1500);
          report.push(`  -> 处理了确认弹窗`);
        }

        const urlAfter = page.url();
        const newPhaseMatch = urlAfter.match(/\/phases\/(\d+)/);
        const newPhase = newPhaseMatch ? parseInt(newPhaseMatch[1]) : -1;
        report.push(`Step 6.${attempt}: P${currentPhase}→P${newPhase}, advanceResult=${advanceResult}`);

        if (newPhase === currentPhase && advanceResult.includes("gate_failed")) {
          report.push(`Step 6.${attempt}: 门禁失败，无法推进!`);
          break;
        }
      } else {
        report.push(`Step 6.${attempt}: "确认推进"按钮被禁用`);
        break;
      }
    }

    // ============================================================
    // Final Report
    // ============================================================
    const finalUrl = page.url();
    const finalPhaseMatch = finalUrl.match(/\/phases\/(\d+)/);
    const finalPhase = finalPhaseMatch ? parseInt(finalPhaseMatch[1]) : -1;
    const finalBodyText = await page.locator("body").innerText();
    const hasVideoDownload = /下载|download|\.mp4|视频文件/i.test(finalBodyText);

    report.push(`\n=== FINAL ===`);
    report.push(`URL: ${finalUrl}`);
    report.push(`Phase: ${finalPhase}`);
    report.push(`Has video/download: ${hasVideoDownload}`);
    report.push(`Body text (first 500): ${finalBodyText.substring(0, 500)}`);

    // Take final screenshot
    await page.screenshot({ path: "/tmp/test_e2e_final.png", fullPage: true });

    console.log("\n╔══════════════════════════════════════════╗");
    console.log("║  E2E Test Report                         ║");
    console.log("╠══════════════════════════════════════════╣");
    for (const line of report) {
      console.log(`║  ${line}`);
    }
    console.log("╚══════════════════════════════════════════╝");
  });
});
