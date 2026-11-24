// Teknisk bildfångst av original/A/B(/C) vid givna rutor. Skriver bara i ut/qa. Inte ägardom.
const { chromium } = require('../../../arbetsbord/prov/node_modules/playwright-core');
const fs = require('node:fs'), path = require('node:path');
const out = path.join(__dirname, 'ut', process.argv[2], 'qa'); fs.mkdirSync(out, { recursive: true });
const KLIPP = process.argv[2]; let RUTOR = null;
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--enable-unsafe-swiftshader'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1500, height: 1100 } }), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:5206/?klipp=' + KLIPP, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForFunction(() => window.experiment?.ready && window.experiment.vantar === 0, { timeout: 60000 });
    const rep = [];
    RUTOR = await page.evaluate(() => { const v = window.experiment.views.find(v => v.id.startsWith('L')); return v.data.package.tagningar.map(t => Math.floor((t.ut[0] + t.ut[1]) / 2)); });
    const fpsKlipp = await page.evaluate(() => window.experiment.views.find(v => v.id.startsWith('L')).data.package.tidsbas.fps);
    for (const f of RUTOR) {
      const t = (f + 0.5) / fpsKlipp;
      await page.evaluate(t => { document.querySelector('video').currentTime = t; }, t);
      await page.waitForFunction(t => !document.querySelector('video').seeking && Math.abs(window.experiment.renderedTime - t) < 0.01, t, { timeout: 10000 });
      await page.waitForFunction(() => window.experiment.vantar === 0, null, { timeout: 20000 }); await page.waitForTimeout(150);
      await page.locator('#views').screenshot({ path: path.join(out, `ruta-${String(f).padStart(3, '0')}.png`) });
      rep.push({ ruta: f, snap: await page.evaluate(() => window.experiment.views.map(v => ({ id: v.id, s: v.r.getSnapshot() }))) });
    }
    fs.writeFileSync(path.join(out, 'fangst.json'), JSON.stringify({ errors, rep }, null, 1));
    console.log(JSON.stringify({ ok: errors.length === 0, rutor: RUTOR.length, errors }));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
