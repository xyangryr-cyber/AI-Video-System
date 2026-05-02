import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

const TEST_TITLE = "美联储换届对于资本市场的影响";
const TEST_DESC = `a. 美联储下一届主席的公布时间
b. 下一任美联储主席的热门人选
c. 分析这些热门人选的了解 并且给出他们当选的当选后对于市场的影响`;

interface PhaseResult {
  phase: number;
  status: "advanced" | "stuck" | "skipped";
  detail: string;
}

const allResults: PhaseResult[] = [];

test.describe("完整12阶段端到端流程测试", () => {
  test.setTimeout(600_000); // 10 minutes

  test("创建项目并推进至P11产出视频", async ({ page }) => {
    // ============================================================
    // Step 1: 打开项目列表页
    // ============================================================
    console.log("\n=== Step 1: 打开项目列表页 ===");
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState("networkidle");

    // ============================================================
    // Step 2: 点击新建项目按钮
    // ============================================================
    console.log("\n=== Step 2: 新建项目 ===");
    const newProjectBtn = page.locator("button", { hasText: "新建项目" });
    await expect(newProjectBtn).toBeVisible({ timeout: 10000 });
    await newProjectBtn.click();
    await page.waitForURL("**/projects/new");
    console.log("  -> 已跳转到 /projects/new");

    // ============================================================
    // Step 3: 输入标题和内容描述
    // ============================================================
    console.log("\n=== Step 3: 输入表单 ===");
    const titleInput = page.locator("#title");
    const descInput = page.locator("#desc");
    await expect(titleInput).toBeVisible();
    await expect(descInput).toBeVisible();

    await titleInput.fill(TEST_TITLE);
    await descInput.fill(TEST_DESC);
    console.log("  -> 标题和描述已输入");

    // ============================================================
    // Step 4: 提交创建项目
    // ============================================================
    console.log("\n=== Step 4: 提交创建 ===");
    const submitBtn = page.locator("button[type='submit']", { hasText: "开始制作" });
    await expect(submitBtn).toBeEnabled({ timeout: 5000 });

    const responsePromise = page.waitForResponse(
      (resp) => resp.url().includes("/api/projects") && resp.request().method() === "POST",
      { timeout: 15000 }
    );
    await submitBtn.click();
    const apiResponse = await responsePromise;
    const body = await apiResponse.json();
    const projectId = body.id;
    console.log(`  -> 项目创建成功: ${projectId}`);

    // Wait for redirect to workflow page
    await page.waitForURL((url) => url.pathname.includes(projectId), { timeout: 15000 });
    await page.waitForLoadState("networkidle");
    console.log(`  -> 当前URL: ${page.url()}`);

    // ============================================================
    // Step 5: 逐阶段推进 (Phase 0 -> Phase 11)
    // ============================================================
    // First, let's wait for Phase 0 agent to do initial work
    console.log("\n=== Step 5: 等待Phase 0 Agent工作完成 ===");
    await page.waitForTimeout(3000);

    // Helper: extract current phase from URL
    function getCurrentPhase(url: string): number {
      const match = url.match(/\/phases\/(\d+)/);
      return match ? parseInt(match[1]) : 0;
    }

    // Helper: wait for tasks to settle
    async function waitForAgentWork(timeoutMs: number = 15000) {
      console.log(`  -> 等待Agent工作完成 (最多 ${timeoutMs/1000}s)...`);
      const startTime = Date.now();
      let hasRunning = true;
      while (hasRunning && (Date.now() - startTime) < timeoutMs) {
        await page.waitForTimeout(2000);
        const bodyText = await page.locator("body").innerText();
        // Check if there are running tasks (check task monitor area)
        hasRunning = bodyText.includes("执行中") || bodyText.includes("running");
        if (!hasRunning) {
          // Also wait a bit to make sure
          await page.waitForTimeout(2000);
          const recheck = await page.locator("body").innerText();
          hasRunning = recheck.includes("执行中") || recheck.includes("running");
        }
      }
      const elapsed = Date.now() - startTime;
      console.log(`  -> 等待完成 (${elapsed}ms), hasRunning=${hasRunning}`);
    }

    // Main loop: keep trying to advance through phases
    for (let targetPhase = 0; targetPhase <= 11; targetPhase++) {
      console.log(`\n${"=".repeat(60)}`);
      console.log(`=== 推进到 Phase ${targetPhase + 1} ===`);
      console.log(`${"=".repeat(60)}`);

      // Ensure we're on the right project page
      const currentUrl = page.url();
      if (!currentUrl.includes(projectId)) {
        console.log(`  -> 导航到项目 ${projectId}`);
        await page.goto(`${BASE_URL}/projects/${projectId}`);
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000);
      }

      // Check if we need to switch to the current active phase
      const currentPhase = getCurrentPhase(page.url());
      console.log(`  -> 当前URL phase: ${currentPhase}, 目标: 尝试推进到 phase ${targetPhase + 1}`);

      // Wait for agent work to complete
      await waitForAgentWork(20000);

      // Check page state
      const pageText = await page.locator("body").innerText();
      console.log(`  -> 页面关键文本片段: ${pageText.substring(0, 200)}`);

      // Find the advance button
      const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
      const btnVisible = await advanceBtn.isVisible().catch(() => false);
      const btnEnabled = btnVisible ? await advanceBtn.isEnabled().catch(() => false) : false;

      if (!btnVisible) {
        console.log(`  -> [阻塞] 未找到"确认进入下一阶段"按钮`);
        allResults.push({
          phase: targetPhase,
          status: "stuck",
          detail: "advance button not visible"
        });
        break;
      }

      if (!btnEnabled) {
        console.log(`  -> [阻塞] "确认进入下一阶段"按钮被禁用`);
        // Check gate status
        const gatePassed = pageText.includes("已通过") || pageText.includes("审核通过");
        const hasRunning = pageText.includes("执行中") || pageText.includes("running");
        console.log(`  -> GateKeeper状态: gatePassed=${gatePassed}, hasRunning=${hasRunning}`);
        allResults.push({
          phase: targetPhase,
          status: "stuck",
          detail: `advance button disabled, gatePassed=${gatePassed}, hasRunning=${hasRunning}`
        });

        if (hasRunning) {
          console.log(`  -> 还有运行中的任务，继续等待...`);
          await waitForAgentWork(60000);

          // Recheck
          const recheckEnabled = await advanceBtn.isEnabled().catch(() => false);
          if (!recheckEnabled) {
            console.log(`  -> 等待后仍无法推进，停止`);
            break;
          }
        } else {
          // Try interacting with chat to see if agent needs user input
          console.log(`  -> 尝试发送聊天消息触发Agent工作...`);
          const chatInput = page.locator("textarea[placeholder='对当前产物提出修改方案...']");
          if (await chatInput.isVisible().catch(() => false)) {
            await chatInput.fill("确认当前方案，准备进入下一阶段");
            const sendBtn = page.locator("button", { hasText: "发送反馈" });
            if (await sendBtn.isEnabled().catch(() => false)) {
              await sendBtn.click();
              await page.waitForTimeout(5000);

              // Wait for agent to process
              await waitForAgentWork(30000);

              // Check advance button again
              const afterChatEnabled = await advanceBtn.isEnabled().catch(() => false);
              if (!afterChatEnabled) {
                console.log(`  -> 聊天后仍无法推进，停止`);
                break;
              }
            }
          } else {
            break;
          }
        }
      }

      // Click advance
      console.log(`  -> 点击"确认进入下一阶段"...`);

      // Watch for the advance API response
      let advanceStatus = "unknown";
      const advancePromise = page.waitForResponse(
        (resp) => resp.url().includes("/advance") && resp.request().method() === "POST",
        { timeout: 30000 }
      ).then(async (resp) => {
        try {
          const b = await resp.json();
          advanceStatus = b.status || `HTTP ${resp.status()}`;
          console.log(`  -> advance API响应: status=${advanceStatus}`);
        } catch {
          advanceStatus = `HTTP ${resp.status()}`;
        }
      }).catch(() => {
        advanceStatus = "no_response";
        console.log(`  -> advance API 无响应`);
      });

      await advanceBtn.click();
      await page.waitForTimeout(3000);

      // Handle preference modal if it appears
      let modalHandled = false;

      // Check for "AI 记忆同步中" modal
      const prefModal = page.locator("text=AI 记忆同步中");
      if (await prefModal.isVisible().catch(() => false)) {
        console.log(`  -> 偏好确认弹窗出现`);
        modalHandled = true;

        // Try clicking "确认并进入下一阶段" first
        const confirmBtn = page.locator("button", { hasText: "确认并进入下一阶段" });
        if (await confirmBtn.isVisible().catch(() => false)) {
          await confirmBtn.click();
          console.log(`  -> 点击"确认并进入下一阶段"`);
          await page.waitForTimeout(3000);
        } else {
          // Try "跳过"
          const skipBtn = page.locator("button", { hasText: "跳过" });
          if (await skipBtn.isVisible().catch(() => false)) {
            await skipBtn.click();
            console.log(`  -> 点击"跳过"偏好确认`);
            await page.waitForTimeout(3000);

            // After skipping, might need to click advance again
            const advanceBtn2 = page.locator("button", { hasText: "确认进入下一阶段" });
            if (await advanceBtn2.isVisible().catch(() => false)) {
              await advanceBtn2.click();
              console.log(`  -> 跳过偏好后再次点击推进`);
              await page.waitForTimeout(3000);
            }
          } else {
            // Try "全部接受"
            const acceptAllBtn = page.locator("button", { hasText: "全部接受" });
            if (await acceptAllBtn.isVisible().catch(() => false)) {
              await acceptAllBtn.click();
              console.log(`  -> 点击"全部接受"`);
              await page.waitForTimeout(3000);
            } else {
              // Try "关闭"
              const closeBtn = page.locator("button", { hasText: "关闭" });
              if (await closeBtn.isVisible().catch(() => false)) {
                await closeBtn.click();
                console.log(`  -> 点击"关闭"偏好弹窗`);
                await page.waitForTimeout(1000);
              }
            }
          }
        }
      }

      // Check for "门禁条件未满足" error
      const gateFailedText = await page.locator("body").innerText();
      if (gateFailedText.includes("门禁条件未满足")) {
        console.log(`  -> [阻塞] GateKeeper返回: 门禁条件未满足`);
        await advancePromise;
        allResults.push({
          phase: targetPhase,
          status: "stuck",
          detail: `GateKeeper blocked: ${advanceStatus}`
        });
        break;
      }

      // Wait for advance to complete
      await advancePromise;
      await page.waitForTimeout(3000);

      // Check if we advanced
      const newUrl = page.url();
      const newPhase = getCurrentPhase(newUrl);

      if (newPhase > targetPhase) {
        console.log(`  -> 推进成功: Phase ${targetPhase} -> Phase ${newPhase}`);
        allResults.push({
          phase: targetPhase,
          status: "advanced",
          detail: `advanced to phase ${newPhase}`
        });
        targetPhase = newPhase - 1; // Loop will increment
      } else if (newPhase === targetPhase && advanceStatus.includes("gate_failed")) {
        console.log(`  -> [阻塞] 推进失败，仍在 Phase ${targetPhase}`);
        allResults.push({
          phase: targetPhase,
          status: "stuck",
          detail: `advance returned: ${advanceStatus}`
        });
        break;
      } else if (newPhase === targetPhase) {
        console.log(`  -> 仍在 Phase ${targetPhase}，advanceStatus=${advanceStatus}`);
        // Might need user interaction - try chat
        const chatInput = page.locator("textarea[placeholder='对当前产物提出修改方案...']");
        if (await chatInput.isVisible().catch(() => false)) {
          await chatInput.fill("确认无误，继续下一阶段");
          const sendBtn = page.locator("button", { hasText: "发送反馈" });
          if (await sendBtn.isEnabled().catch(() => false)) {
            await sendBtn.click();
            await page.waitForTimeout(3000);
            await waitForAgentWork(15000);
          }
        }

        // One more try
        const advanceBtn3 = page.locator("button", { hasText: "确认进入下一阶段" });
        if (await advanceBtn3.isEnabled().catch(() => false)) {
          console.log(`  -> 重试推进...`);
          await advanceBtn3.click();
          await page.waitForTimeout(3000);

          const retryUrl = page.url();
          const retryPhase = getCurrentPhase(retryUrl);
          if (retryPhase > targetPhase) {
            console.log(`  -> 重试成功: Phase ${targetPhase} -> Phase ${retryPhase}`);
            allResults.push({
              phase: targetPhase,
              status: "advanced",
              detail: `advanced to phase ${retryPhase} (retry)`
            });
            targetPhase = retryPhase - 1;
          } else {
            console.log(`  -> 重试后仍在 Phase ${targetPhase}`);
            allResults.push({
              phase: targetPhase,
              status: "stuck",
              detail: `stuck at phase ${targetPhase} after retry`
            });
            break;
          }
        } else {
          allResults.push({
            phase: targetPhase,
            status: "stuck",
            detail: `stuck at phase ${targetPhase}`
          });
          break;
        }
      }

      // If we've reached P10/P11, check for video output
      let hasVideoContent = false;
      if (newPhase >= 10) {
        console.log(`\n=== 已到达视频产出阶段 Phase ${newPhase}! ===`);

        // Check page for video-related content
        const finalText = await page.locator("body").innerText();
        hasVideoContent = finalText.includes("视频") || finalText.includes("mp4") || finalText.includes("播放");
        const hasDownload = finalText.includes("下载");
        console.log(`  -> 视频相关内容: ${hasVideoContent}, 下载按钮: ${hasDownload}`);
      }

      if (newPhase >= 11) {
        console.log(`\n=== 已到达最终阶段 Phase 11! ===`);
        allResults.push({
          phase: 11,
          status: "advanced",
          detail: `reached final phase 11`
        });
        break;
      }
    }

    // ============================================================
    // Final: Print report
    // ============================================================
    console.log("\n");
    console.log("╔══════════════════════════════════════════════════════╗");
    console.log("║   完整流水线端到端测试报告                              ║");
    console.log("╠══════════════════════════════════════════════════════╣");
    console.log(`║  项目ID: ${projectId}`);
    console.log(`║  最终URL: ${page.url()}`);
    for (const r of allResults) {
      const icon = r.status === "advanced" ? "✅" : "❌";
      console.log(`║  ${icon} Phase ${r.phase}: ${r.detail}`);
    }

    const finalPhase = getCurrentPhase(page.url());
    const advancedCount = allResults.filter(r => r.status === "advanced").length;
    console.log(`╠══════════════════════════════════════════════════════╣`);
    console.log(`║  推进阶段数: ${advancedCount}/12`);
    console.log(`║  最终Phase: ${finalPhase}`);
    console.log("╚══════════════════════════════════════════════════════╝");

    // Verify: at minimum we should have reached phase 1
    expect(advancedCount).toBeGreaterThan(0);
  });
});
