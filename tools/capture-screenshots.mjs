import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const outDir = path.join(root, 'docs', 'screenshots');

const screens = [
  {
    html: 'feed_unified_refined_code.html',
    output: '01-news-feed.png',
    label: '뉴스 피드',
  },
  {
    html: 'my_pick_code.html',
    output: '02-my-pick.png',
    label: '마이 픽',
  },
  {
    html: '_2_code.html',
    output: '03-home.png',
    label: '홈',
  },
  {
    html: 'ranking_code.html',
    output: '04-ranking.png',
    label: '랭킹',
  },
  {
    html: 'settings_unified_code.html',
    output: '05-settings.png',
    label: '설정',
  },
];

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 393, height: 852 },
  deviceScaleFactor: 2,
});

for (const screen of screens) {
  const filePath = path.join(root, 'design-ref', screen.html);
  await page.goto(`file:///${filePath.replace(/\\/g, '/')}`, {
    waitUntil: 'networkidle',
  });
  await page.waitForTimeout(1200);
  await page.screenshot({
    path: path.join(outDir, screen.output),
    fullPage: false,
  });
  console.log(`saved ${screen.output} (${screen.label})`);
}

await browser.close();
