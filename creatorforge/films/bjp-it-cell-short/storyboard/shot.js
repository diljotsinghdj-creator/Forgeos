const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  for (let i = 1; i <= 12; i++) { const n = String(i).padStart(2, '0'); await p.goto('file://' + process.cwd() + `/f${n}.html`); await p.evaluate(() => document.fonts.ready); await p.screenshot({ path: `f${n}.png` }); }
  await b.close(); })();
