import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
import path from 'path';
const html = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
await page.goto('file://' + html);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);
const n = await page.locator('.slide').count();
for (let i = 0; i < n; i++) {
  const el = page.locator('.slide').nth(i);
  await el.screenshot({ path: path.join(out, `slide-${String(i + 1).padStart(2, '0')}.png`), type: 'png' });
}
console.log('rendered', n, 'slides to', out);
await browser.close();
