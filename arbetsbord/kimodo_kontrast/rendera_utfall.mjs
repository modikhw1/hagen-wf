import { chromium } from '../prov/node_modules/playwright-core/index.mjs';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const UT_DIR = path.join(__dirname, 'ut');
fs.mkdirSync(UT_DIR, { recursive: true });

const BASE = process.env.ARBETSBORD_URL || 'http://127.0.0.1:5199';
const CHROME_PATH =
  process.env.CHROME_EXE ||
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const TEMA_KOK = {
  id: 'kok',
  namn: 'Kök (Kimodo)',
  bakgrund: '#1a2029',
  golv: '#575c64',
  vagg: '#cfd6de',
  ljus: {
    nyckel_farg: '#ffffff',
    nyckel_styrka: 2.3,
    fyll_farg: '#cce2ff',
    fyll_styrka: 0.9,
    omgivning_farg: '#e8eff7',
    omgivning_styrka: 0.95,
  },
  dimma: null,
};

const JOBS = [
  {
    id: 'fall1_horn',
    label: 'Fall 1: Hörn + ny bänk (guacamole s4)',
    scenJson: path.join(UT_DIR, 'scen_fall1_horn.json'),
    video: path.join(ROOT, 'scen', 'klipp', 'e-dialog-guacamole.mp4'),
    start_s: 6.3333,
    outMp4: path.join(UT_DIR, 'fall1_horn_soundoverlay.mp4'),
    outContact: path.join(UT_DIR, 'kontakt_fall1.png'),
  },
  {
    id: 'fall2_ny_prop_hand',
    label: 'Fall 2: Vänster hand +15cm (gelato s1)',
    scenJson: path.join(UT_DIR, 'scen_fall2_hand.json'),
    video: path.join(ROOT, 'scen', 'klipp', 'kand-kennysgelato2.0-7596403003901381910.mp4'),
    start_s: 0.0,
    outMp4: path.join(UT_DIR, 'fall2_ny_prop_hand_soundoverlay.mp4'),
    outContact: path.join(UT_DIR, 'kontakt_fall2.png'),
  },
  {
    id: 'fall3_kansla_sdedit',
    label: 'Fall 3: SDEdit s=0.55 Trött (guacamole s4)',
    scenJson: path.join(UT_DIR, 'scen_fall3_sdedit.json'),
    video: path.join(ROOT, 'scen', 'klipp', 'e-dialog-guacamole.mp4'),
    start_s: 6.3333,
    outMp4: path.join(UT_DIR, 'fall3_kansla_sdedit_soundoverlay.mp4'),
    outContact: path.join(UT_DIR, 'kontakt_fall3.png'),
  },
];

function runFfmpeg(args, label) {
  const res = spawnSync('ffmpeg', args, { encoding: 'utf-8', maxBuffer: 25 * 1024 * 1024 });
  if (res.status !== 0) {
    throw new Error(`ffmpeg (${label}) misslyckades (${res.status}):\n${res.stderr}`);
  }
}

async function main() {
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--enable-webgl',
      '--ignore-gpu-blocklist',
      '--no-sandbox',
      '--no-first-run',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 700, height: 1100 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  try {
    // Serva minimalt Three.js-skal under samma origin (${BASE}) så module-imports och /three/* inte blockeras av CORS
    const htmlBody = `
      <!doctype html>
      <html>
      <head>
        <meta charset="utf-8">
        <script type="importmap">
          { "imports": { "three": "/three/three.module.js", "three/": "/three/" } }
        </script>
      </head>
      <body style="margin:0;background:#111;">
        <div id="wrap" style="width:576px;height:1024px;position:relative;overflow:hidden;">
          <canvas id="c" style="width:100%;height:100%;display:block;"></canvas>
        </div>
        <script type="module">
          import { Scen3DRenderer } from '/scen3d.js';
          const c = document.getElementById('c');
          window._kimRenderer = new Scen3DRenderer(c);
          window._kimRenderer.setShowLabels(true);
        </script>
      </body>
      </html>
    `;
    await page.route('**/kimodo_render.html', (route) =>
      route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: htmlBody })
    );
    page.on('pageerror', (err) => console.error('PAGEERROR:', err));
    await page.goto(`${BASE}/kimodo_render.html`, { waitUntil: 'networkidle', timeout: 25000 });
    await page.waitForFunction(() => Boolean(window._kimRenderer), { timeout: 15000 });

    const outLog = [];
    for (const job of JOBS) {
      if (!fs.existsSync(job.scenJson)) {
        throw new Error(`Saknar scenpaket JSON: ${job.scenJson}`);
      }
      const pak = JSON.parse(fs.readFileSync(job.scenJson, 'utf-8'));
      const fps = Number(pak.tidsbas?.fps || 30);
      const nFrames = Number(pak.tidsbas?.antal_rutor || 90);
      const dur = nFrames / fps;

      await page.evaluate(({ p, tema }) => {
        window._kimRenderer.loadScene(p, tema);
        window._kimRenderer.resize();
      }, { p: pak, tema: TEMA_KOK });

      const tmpDir = path.join(UT_DIR, `_tmp_${job.id}`);
      fs.rmSync(tmpDir, { recursive: true, force: true });
      fs.mkdirSync(tmpDir, { recursive: true });

      const t0 = Date.now();
      for (let f = 0; f < nFrames; f++) {
        const ts = f / fps;
        const dataUrl = await page.evaluate((t) => {
          window._kimRenderer.setTime(t);
          return document.getElementById('c').toDataURL('image/png');
        }, ts);
        const b64 = dataUrl.split(',')[1];
        fs.writeFileSync(path.join(tmpDir, `f_${String(f).padStart(5, '0')}.png`), Buffer.from(b64, 'base64'));
      }
      const capS = ((Date.now() - t0) / 1000).toFixed(1);

      const safeLabel = job.label.replace(/[:']/g, ' ');
      runFfmpeg(
        [
          '-y',
          '-ss', String(job.start_s),
          '-t', dur.toFixed(4),
          '-i', job.video,
          '-framerate', String(fps),
          '-i', path.join(tmpDir, 'f_%05d.png'),
          '-filter_complex',
          `[0:v]scale=576:1024,drawtext=text='Original':x=16:y=16:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65[v0];` +
          `[1:v]scale=576:1024,drawtext=text='${safeLabel}':x=16:y=16:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.65[v1];` +
          `[v0][v1]hstack=inputs=2[v]`,
          '-map', '[v]',
          '-map', '0:a:0?',
          '-c:v', 'libx264',
          '-pix_fmt', 'yuv420p',
          '-crf', '20',
          '-c:a', 'aac',
          '-b:a', '128k',
          '-shortest',
          job.outMp4,
        ],
        job.id
      );

      // 8 jämnt fördelade nyckelrutor i 4x2-kontaktkarta
      const pick = Array.from({ length: 8 }, (_, i) => Math.round((i * (nFrames - 1)) / 7));
      const expr = pick.map((n) => `eq(n\\,${n})`).join('+');
      runFfmpeg(
        [
          '-y',
          '-i', job.outMp4,
          '-vf', `select='${expr}',scale=576:-1,drawtext=text='%{pts\\:hms}':x=10:y=48:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.65,tile=4x2`,
          '-frames:v', '1',
          job.outContact,
        ],
        `contact_${job.id}`
      );

      fs.rmSync(tmpDir, { recursive: true, force: true });
      outLog.push({ id: job.id, frames: nFrames, fps, capture_s: Number(capS), mp4: path.relative(ROOT, job.outMp4), contact: path.relative(ROOT, job.outContact) });
      console.log('KIMODO_RENDER_OK', job.id, `${nFrames} frames in ${capS}s`);
    }

    fs.writeFileSync(path.join(UT_DIR, 'render_logg.json'), JSON.stringify(outLog, null, 2), 'utf-8');
    console.log('ALL_KIMODO_RENDER_OK');
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('KIMODO_RENDER_FAIL:', err);
  process.exit(1);
});
