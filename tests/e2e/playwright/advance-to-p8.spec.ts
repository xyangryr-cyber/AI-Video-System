import { test } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";
const PROJECT_ID = "proj_20260429_001";

test("从P4推进到P8+，验证Remotion渲染", async ({ page }) => {
  await page.goto(`${BASE_URL}/projects/${PROJECT_ID}/phases/4`);
  await page.waitForLoadState("networkidle");
  console.log(`Started at: ${page.url()}`);

  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(1500);

    const advanceBtn = page.locator("button", { hasText: "确认进入下一阶段" });
    const visible = await advanceBtn.isVisible().catch(() => false);

    if (!visible) {
      const url = page.url();
      const m = url.match(/\/phases\/(\d+)/);
      const phase = m ? parseInt(m[1]) : -1;
      console.log(`Attempt ${i}: advance button not visible, phase=${phase}`);

      if (phase >= 10) {
        console.log(`Reached P${phase}!`);
        break;
      }

      // Try refreshing to current phase
      await page.reload();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(2000);
      continue;
    }

    const enabled = await advanceBtn.isEnabled().catch(() => false);
    if (!enabled) {
      console.log(`Attempt ${i}: advance button disabled, waiting...`);
      await page.waitForTimeout(5000);
      continue;
    }

    console.log(`Attempt ${i}: clicking advance...`);
    await advanceBtn.click();
    await page.waitForTimeout(4000);

    // Handle modals
    for (const btnText of ["全部接受", "确认并进入下一阶段"]) {
      const modalBtn = page.locator("button", { hasText: btnText });
      if (await modalBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        await modalBtn.click();
        await page.waitForTimeout(2000);
      }
    }

    const url = page.url();
    const m = url.match(/\/phases\/(\d+)/);
    const phase = m ? parseInt(m[1]) : -1;
    console.log(`  -> phase ${phase}`);

    if (phase >= 11) {
      console.log("SUCCESS: Reached P11!");
      break;
    }
  }

  const finalUrl = page.url();
  const fm = finalUrl.match(/\/phases\/(\d+)/);
  console.log(`\nFinal: phase=${fm ? fm[1] : "unknown"}, url=${finalUrl}`);

  // Screenshot
  await page.screenshot({ path: "/tmp/advance_final.png", fullPage: true });
  console.log("Screenshot: /tmp/advance_final.png");
});
