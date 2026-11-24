// Verifiering av texturerade bitar i 3D: original-pose, vriden kamera, färgade bitar. Skriver ut/<klipp>/qa/orbit-<ruta>.png
const { chromium } = require('../../../arbetsbord/prov/node_modules/playwright-core');
const path = require('node:path');
const [klipp, ...rutor] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args: ['--enable-unsafe-swiftshader'] });
  try {
    const page = await b.newPage({ viewport: { width: 1500, height: 1000 } }); const errs = []; page.on('pageerror', e => errs.push(e.message));
    await page.goto('http://127.0.0.1:5206/?klipp=' + klipp, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.experiment?.ready && window.experiment.vantar === 0, { timeout: 60000 });
    if (process.env.VY) await page.evaluate(vy => { window.__vy = vy; }, process.env.VY);
    for (const f of rutor.map(Number)) {
      await page.evaluate(t => { document.querySelector('video').currentTime = t; }, (f + 0.5) / 30);
      await page.waitForFunction(t => !document.querySelector('video').seeking && Math.abs(window.experiment.renderedTime - t) < 0.01, (f + 0.5) / 30);
      const shots = [];
      for (const [vrid, farg, hela] of [[0, false, false], [35, false, false], [35, true, false], [50, false, true]]) {
        await page.evaluate(([vrid, farg, hela]) => {
          document.getElementById('helarum').checked = hela;
          const v = window.experiment.views.find(v => v.nat && v.id === (window.__vy || v.id)); const r = v.r;
          document.getElementById('bitfarg').checked = farg; document.getElementById('bitfarg').dispatchEvent(new Event('change'));
          window.experiment.orbit(vrid !== 0);
          if (vrid) { const c = r.camera, t = r.controls.target; const d = c.position.clone().sub(t); const a = vrid * Math.PI / 180;
            const x = d.x * Math.cos(a) - d.y * Math.sin(a), y = d.x * Math.sin(a) + d.y * Math.cos(a); c.position.set(t.x + x, t.y + y, c.position.z + 0.3); c.lookAt(t); }
          window.experiment.draw(document.querySelector('video').currentTime); r.renderFrame();
        }, [vrid, farg, hela]);
        await page.waitForTimeout(200);
        const box = await page.evaluate(() => window.experiment.views.find(v => v.nat && v.id === (window.__vy || v.id)).sec.querySelector('.viewport').getBoundingClientRect().toJSON());
        const p = path.join(__dirname, 'ut', klipp, 'qa', `orbit${process.env.VY ? '-' + process.env.VY : ''}-${f}-${vrid}${farg ? 'f' : ''}${hela ? 'h' : ''}.png`); shots.push(p);
        await page.screenshot({ path: p, clip: box });
      }
      await page.evaluate(() => { const v = window.experiment.views.find(v => v.nat && v.id === (window.__vy || v.id)); window.experiment.orbit(false); document.getElementById('bitfarg').checked = false; document.getElementById('bitfarg').dispatchEvent(new Event('change')); });
    }
    console.log(JSON.stringify({ ok: errs.length === 0, errs }));
  } finally { await b.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
