import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'path';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
await p.goto('file://' + path.resolve('carousel.html'));
await p.evaluate(() => document.fonts.ready);
await p.addStyleTag({ content: '.strip{display:block;padding:0;gap:0} .slide{page-break-after:always;break-after:page} html,body{background:#0D1A16}' });
await p.pdf({ path: 'export/the-prophet-as-a-husband-carousel.pdf', width: '1080px', height: '1350px', printBackground: true, margin: {top:0,right:0,bottom:0,left:0} });
await b.close(); console.log('pdf ok');
