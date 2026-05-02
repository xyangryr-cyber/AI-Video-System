import { test, expect } from "@playwright/test";

const BASE_URL = process.env.TEST_BASE_URL || "http://localhost:3005";

test("P11 验证: 视频播放和下载", async ({ page }) => {
  await page.goto(`${BASE_URL}/projects/proj_20260429_001/phases/11`);
  await page.waitForLoadState("networkidle");

  const bodyText = await page.locator("body").innerText();

  // Check for video-related UI elements
  console.log("=== P11 UI Content ===");
  const relevantLines = bodyText.split("\n").filter(line =>
    /视频|播放|下载|final|mp4|remotion|Remotion|渲染|output|delivery/i.test(line)
  );
  for (const line of relevantLines.slice(0, 20)) {
    console.log(`  ${line}`);
  }

  // Check artifact preview
  const preview = page.locator('[data-testid="artifact-preview-panel"]');
  const previewText = await preview.innerText().catch(() => "(not found)");
  console.log(`\nPreview panel: ${previewText.substring(0, 500)}`);

  // Check for links
  const links = page.locator("a");
  const linkCount = await links.count();
  console.log(`\nLinks found: ${linkCount}`);
  for (let i = 0; i < Math.min(linkCount, 5); i++) {
    const href = await links.nth(i).getAttribute("href");
    const text = await links.nth(i).innerText();
    console.log(`  [${i}] ${href} "${text.substring(0, 80)}"`);
  }

  // Phase nav check
  const p11Nav = page.locator('[data-testid="phase-nav-11"]');
  const isActive = await p11Nav.getAttribute("data-active");
  console.log(`\nP11 nav active: ${isActive}`);

  // Veritas button
  const veritasBtn = page.locator('button[title="事实清单 (Veritas)"]');
  console.log(`Veritas button visible: ${await veritasBtn.isVisible().catch(() => false)}`);

  // Bottom bar
  const bottomBar = await page.locator("body").innerText();
  const hasGateKeeper = bottomBar.includes("准入审核");
  console.log(`GateKeeper status visible: ${hasGateKeeper}`);

  await page.screenshot({ path: "/tmp/p11_final_ui.png", fullPage: true });
});
