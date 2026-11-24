import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const BASE = process.env.ARBETSBORD_URL || 'http://127.0.0.1:5199';
const CHROME_PATH = process.env.CHROME_EXE || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUT_PNG = path.join(ROOT, 'arbetsbord', 'ut', 'ui_check', 'guacamole_bredvid.png');
const OUT_JSON = path.join(ROOT, 'arbetsbord', 'ut', 'ui_check', 'media_check.json');

function assert(cond, msg) {
  if (!cond) throw new Error(`ASSERTION_FAILED: ${msg}`);
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const txt = await res.text();
  let json;
  try { json = JSON.parse(txt); } catch { json = null; }
  return { status: res.status, json, txt };
}

async function checkRange206(url) {
  const res = await fetch(url, { headers: { Range: 'bytes=0-4095' } });
  const buf = new Uint8Array(await res.arrayBuffer());
  const head = Buffer.from(buf.slice(0, 12)).toString('ascii');
  return {
    status: res.status,
    contentRange: res.headers.get('content-range'),
    contentType: res.headers.get('content-type'),
    bytes: buf.length,
    head,
    isRiffWave: head.startsWith('RIFF') && head.slice(8, 12) === 'WAVE',
  };
}

async function main() {
  const resultat = { base: BASE, ladda: {}, range: {}, cacheVideo: {}, browser: null };

  // 1. Verifiera /api/ladda -> non-null tal_url på alla 5 klipp
  for (const nyckel of ['notan', 'guacamole', 'gelato', 'asketch', 'btilltal']) {
    const r = await postJson(`${BASE}/api/ladda`, { klipp: nyckel });
    assert(r.status === 200 && Boolean(r.json?.tillstand), `${nyckel}: /api/ladda fel (${r.status})`);
    const talUrl = r.json?.tillstand?.media?.tal_url || null;
    const vidUrl = r.json?.tillstand?.media?.video_url || null;
    resultat.ladda[nyckel] = { tal_url: talUrl, video_url: vidUrl, har_3d: Boolean(r.json?.tillstand?.scen) };
    assert(Boolean(talUrl), `${nyckel}: media.tal_url är null`);
  }

  // 2. Verifiera /media/tal/<nyckel> med Range: bytes=0-4095 -> 206 + RIFF....WAVE
  for (const nyckel of ['guacamole', 'notan']) {
    const t0 = Date.now();
    const info = await checkRange206(`${BASE}/media/tal/${nyckel}`);
    info.ms = Date.now() - t0;
    resultat.range[nyckel] = info;
    assert(info.status === 206, `/media/tal/${nyckel}: status=${info.status}, väntade 206`);
    assert(info.isRiffWave, `/media/tal/${nyckel}: ogiltigt WAV-huvud '${info.head}'`);
  }

  // 3. Verifiera /media/video/guacamole -> H.264 cache + 206
  const vRes = await fetch(`${BASE}/media/video/guacamole`, { headers: { Range: 'bytes=0-4095' } });
  const vBuf = new Uint8Array(await vRes.arrayBuffer());
  const h264File = path.join(ROOT, 'arbetsbord', 'data', 'cache_video', 'guacamole_h264.mp4');
  resultat.cacheVideo.guacamole = {
    status: vRes.status,
    contentRange: vRes.headers.get('content-range'),
    bytes: vBuf.length,
    h264Exists: fs.existsSync(h264File),
    h264Bytes: fs.existsSync(h264File) ? fs.statSync(h264File).size : 0,
  };
  assert(vRes.status === 206, `/media/video/guacamole status=${vRes.status}`);
  assert(resultat.cacheVideo.guacamole.h264Exists, 'guacamole_h264.mp4 saknas i cache_video');

  // 4. Playwright: guacamole bredvid med riktig videoavkodning + icke-svart originalVideo
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
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
      '--autoplay-policy=no-user-gesture-required',
    ],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('response', (res) => { if (res.status() >= 400) httpErrors.push({ status: res.status(), url: res.url() }); });

  try {
    await page.goto(`${BASE}/?klipp=guacamole`, { waitUntil: 'domcontentloaded', timeout: 25000 });
    await page.waitForFunction(
      () => {
        const dbg = window.__arbetsbordDebug?.getState?.();
        const veil = document.getElementById('loadingVeil');
        return dbg && dbg.klipp?.nyckel === 'guacamole' && (!veil || veil.hidden);
      },
      { timeout: 20000 }
    );
    await page.click('#jamforBtn');
    await page.evaluate(() => window.__arbetsbordDebug.setTime(2.0));
    await page.waitForFunction(
      () => {
        const v = document.getElementById('originalVideo');
        return v && v.readyState >= 2 && !v.seeking && v.videoWidth > 0 && v.videoHeight > 0;
      },
      { timeout: 25000 }
    );
    await page.waitForTimeout(350);

    const videoStats = await page.evaluate(() => {
      const v = document.getElementById('originalVideo');
      const tmp = document.createElement('canvas');
      tmp.width = 72;
      tmp.height = 128;
      const ctx = tmp.getContext('2d');
      ctx.drawImage(v, 0, 0, 72, 128);
      const data = ctx.getImageData(0, 0, 72, 128).data;
      let sum = 0;
      let sumSq = 0;
      const n = 72 * 128;
      for (let i = 0; i < data.length; i += 4) {
        const lum = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        sum += lum;
        sumSq += lum * lum;
      }
      const mean = sum / n;
      const std = Math.sqrt(Math.max(0, sumSq / n - mean * mean));
      return {
        readyState: v.readyState,
        videoWidth: v.videoWidth,
        videoHeight: v.videoHeight,
        currentTime: Number(v.currentTime.toFixed(3)),
        mean: Number(mean.toFixed(2)),
        std: Number(std.toFixed(2)),
      };
    });

    await page.screenshot({ path: OUT_PNG });
    assert(videoStats.std > 10 && videoStats.mean > 15, `originalVideo verkar fortfarande svart: ${JSON.stringify(videoStats)}`);
    assert(consoleErrors.length === 0 && pageErrors.length === 0 && httpErrors.length === 0, 'Webbfel upptäcktes');

    resultat.browser = { videoStats, consoleErrors, pageErrors, httpErrors, outPng: path.relative(ROOT, OUT_PNG) };
    fs.writeFileSync(OUT_JSON, JSON.stringify(resultat, null, 2), 'utf-8');
    console.log('VERIFIERA_MEDIA_VIDEO_OK', JSON.stringify(resultat, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('VERIFIERA_MEDIA_VIDEO_FAIL:', err);
  process.exit(1);
});
