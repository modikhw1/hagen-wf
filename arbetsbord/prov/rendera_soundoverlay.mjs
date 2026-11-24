import { chromium } from 'playwright-core';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const UT_DIR = path.join(ROOT, 'arbetsbord', 'ut');
fs.mkdirSync(UT_DIR, { recursive: true });

const BASE = process.env.ARBETSBORD_URL || 'http://127.0.0.1:5199';
const CHROME_PATH =
  process.env.CHROME_EXE ||
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

const JOBS = [
  {
    namn: 'notan',
    klipp: 'notan',
    video: path.join(ROOT, 'scen', 'klipp', 'd-dialog-notan.mp4'),
    ops: [],
  },
  {
    namn: 'guacamole_orig',
    klipp: 'guacamole',
    video: path.join(ROOT, 'scen', 'klipp', 'e-dialog-guacamole.mp4'),
    ops: [],
  },
  {
    namn: 'guacamole_kok',
    klipp: 'guacamole',
    video: path.join(ROOT, 'scen', 'klipp', 'e-dialog-guacamole.mp4'),
    ops: [
      { op: 'byt_miljo', params: { tema: 'kok' } },
      { op: 'objekt_lagg_till', params: { typ: 'spis', etikett: 'Stekbord', pos: [0.0, 0.2, 0.0], matt: [1.1, 0.65, 0.88] } },
      { op: 'objekt_lagg_till', params: { typ: 'bank', etikett: 'Burgare & tillbehor', pos: [-0.95, 0.35, 0.0], matt: [0.9, 0.6, 0.9] } },
    ],
  },
];

function runFfmpeg(args, label) {
  const res = spawnSync('ffmpeg', args, { encoding: 'utf-8', maxBuffer: 20 * 1024 * 1024 });
  if (res.status !== 0) {
    throw new Error(`ffmpeg (${label}) misslyckades (${res.status}):\n${res.stderr}`);
  }
}

function buildContactIndices(st) {
  const fps = st.fps || 30;
  const totalFrames = Math.max(1, Math.round(st.langd_s * fps));
  const tagningar = st.tillstand?.tagningar || [];
  const pts = new Set([0, Math.min(totalFrames - 1, 2)]);
  for (const t of tagningar) {
    const f0 = Math.max(0, Math.round((t.ny_fran_s ?? t.orig_fran_s ?? 0) * fps));
    const f1 = Math.min(totalFrames - 1, Math.round(((t.ny_till_s ?? t.orig_till_s ?? st.langd_s) * fps)) - 1);
    const mid = Math.round((f0 + f1) / 2);
    pts.add(f0);
    if (f0 + 1 < totalFrames) pts.add(f0 + 1);
    pts.add(mid);
    if (f1 > f0) pts.add(f1);
    if (f1 - 1 > f0) pts.add(f1 - 1);
  }
  const sorted = [...pts].filter((f) => f >= 0 && f < totalFrames).sort((a, b) => a - b);
  // Begränsa till max 16 rutor jämnt fördelade över unika nyckelpunkter + tagningar
  if (sorted.length <= 16) return sorted;
  const picked = [];
  for (let i = 0; i < 16; i++) {
    picked.push(sorted[Math.round((i * (sorted.length - 1)) / 15)]);
  }
  return [...new Set(picked)];
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
    viewport: { width: 1200, height: 1120 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  const summary = [];
  try {
    await page.goto(`${BASE}/?klipp=notan`, { waitUntil: 'domcontentloaded', timeout: 25000 });
    await page.addStyleTag({
      content: `
        .topbar, .stage-toolbar, .transport-panel, .work-col, #originalFrame { display: none !important; }
        .workspace, .stage-col, .stage-viewports { display: block !important; padding: 0 !important; margin: 0 !important; width: 576px !important; height: 1024px !important; }
        #forvarldFrame { width: 576px !important; height: 1024px !important; border: none !important; border-radius: 0 !important; }
      `,
    });

    for (const job of JOBS) {
      await page.evaluate(async (k) => {
        await window.__arbetsbordDebug.loadClip(k, null);
      }, job.klipp);
      for (const op of job.ops) {
        await page.evaluate(async (o) => {
          await window.__arbetsbordDebug.runOperation(o.op, o.params);
        }, op);
      }
      await page.evaluate(() => {
        window.__arbetsbordDebug.setCompareMode('av');
        window.__arbetsbordDebug.setCameraMode('las');
        window.__arbetsbordDebug.setHudHidden(false);
      });
      await page.waitForTimeout(300);

      const st = await page.evaluate(() => window.__arbetsbordDebug.getState());
      const renderFps = 30;
      const totalFrames = Math.max(1, Math.round(st.langd_s * renderFps));

      const frameDir = path.join(UT_DIR, `_tmp_frames_${job.namn}`);
      fs.rmSync(frameDir, { recursive: true, force: true });
      fs.mkdirSync(frameDir, { recursive: true });

      const frameEl = page.locator('#forvarldFrame');
      const tStart = Date.now();
      for (let f = 0; f < totalFrames; f++) {
        const t = f / renderFps;
        await page.evaluate((ts) => window.__arbetsbordDebug.setTime(ts), t);
        const pngPath = path.join(frameDir, `f_${String(f).padStart(5, '0')}.png`);
        await frameEl.screenshot({ path: pngPath, type: 'png' });
      }
      const captureSec = ((Date.now() - tStart) / 1000).toFixed(1);

      const outMp4 = path.join(UT_DIR, `soundoverlay_${job.namn}.mp4`);
      runFfmpeg(
        [
          '-y',
          '-i', job.video,
          '-framerate', String(renderFps),
          '-i', path.join(frameDir, 'f_%05d.png'),
          '-filter_complex', '[0:v]fps=30,scale=576:1024[v0];[1:v]scale=576:1024[v1];[v0][v1]hstack=inputs=2[v]',
          '-map', '[v]',
          '-map', '0:a:0?',
          '-c:v', 'libx264',
          '-pix_fmt', 'yuv420p',
          '-crf', '20',
          '-c:a', 'aac',
          '-b:a', '128k',
          '-shortest',
          outMp4,
        ],
        `mux_${job.namn}`
      );

      // Skapa kontaktkarta med utvalda nyckelrutor + övergångar
      const idxs = buildContactIndices(st);
      const expr = idxs.map((n) => `eq(n\\,${n})`).join('+');
      const cols = Math.min(4, idxs.length);
      const rows = Math.ceil(idxs.length / cols);
      const outContact = path.join(UT_DIR, `kontakt_${job.namn}.png`);
      runFfmpeg(
        [
          '-y',
          '-i', outMp4,
          '-vf', `select='${expr}',scale=576:-1,drawtext=text='f%{frame_num} %{pts\\:hms}':x=10:y=10:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.65,tile=${cols}x${rows}`,
          '-frames:v', '1',
          outContact,
        ],
        `kontakt_${job.namn}`
      );

      fs.rmSync(frameDir, { recursive: true, force: true });
      summary.push({
        namn: job.namn,
        frames: totalFrames,
        capture_s: Number(captureSec),
        mp4: path.relative(ROOT, outMp4),
        contact: path.relative(ROOT, outContact),
        contact_frames: idxs,
      });
      console.log('SOUNDOVERLAY_OK', job.namn, `${totalFrames} frames in ${captureSec}s`);
    }

    fs.writeFileSync(
      path.join(UT_DIR, 'soundoverlay_rapport.json'),
      JSON.stringify(summary, null, 2),
      'utf-8'
    );
    console.log('ALL_SOUNDOVERLAY_OK');
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('SOUNDOVERLAY_FAIL:', err);
  process.exit(1);
});
