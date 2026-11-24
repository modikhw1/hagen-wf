import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const UT_DIR = path.join(ROOT, 'arbetsbord', 'ut', 'ui_check');
const UT_ROOT = path.join(ROOT, 'arbetsbord', 'ut');
fs.mkdirSync(UT_DIR, { recursive: true });

const BASE = process.env.ARBETSBORD_URL || 'http://127.0.0.1:5199';
const CHROME_PATH =
  process.env.CHROME_EXE ||
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

function assert(cond, msg) {
  if (!cond) throw new Error(`ASSERTION_FAILED: ${msg}`);
}

async function sampleCanvasStats(page) {
  return await page.evaluate(() => {
    const src = document.getElementById('scenCanvas');
    if (!src || src.width === 0 || src.height === 0) {
      return { ok: false, width: 0, height: 0, mean: 0, std: 0, nonZeroFrac: 0 };
    }
    const tmp = document.createElement('canvas');
    const w = 72;
    const h = 128;
    tmp.width = w;
    tmp.height = h;
    const ctx = tmp.getContext('2d');
    ctx.drawImage(src, 0, 0, w, h);
    const data = ctx.getImageData(0, 0, w, h).data;
    const n = w * h;
    let sum = 0;
    let sumSq = 0;
    let nonBg = 0;
    const bgR = data[0];
    const bgG = data[1];
    const bgB = data[2];
    for (let i = 0; i < data.length; i += 4) {
      const lum = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      sum += lum;
      sumSq += lum * lum;
      const diff =
        Math.abs(data[i] - bgR) +
        Math.abs(data[i + 1] - bgG) +
        Math.abs(data[i + 2] - bgB);
      if (diff > 18) nonBg++;
    }
    const mean = sum / n;
    const variance = Math.max(0, sumSq / n - mean * mean);
    return {
      ok: true,
      width: src.width,
      height: src.height,
      aspect: Number((src.clientWidth / Math.max(1, src.clientHeight)).toFixed(4)),
      mean: Number(mean.toFixed(2)),
      std: Number(Math.sqrt(variance).toFixed(2)),
      nonBgFrac: Number((nonBg / n).toFixed(4)),
    };
  });
}

async function waitForClipLoaded(page, nyckel) {
  await page.waitForFunction(
    (k) => {
      const dbg = window.__arbetsbordDebug?.getState?.();
      const veil = document.getElementById('loadingVeil');
      return dbg && dbg.klipp?.nyckel === k && (!veil || veil.hidden);
    },
    nyckel,
    { timeout: 20000 }
  );
  await page.waitForTimeout(250);
}

async function loadClipViaUI(page, nyckel, kund = '') {
  await page.selectOption('#klippSelect', nyckel);
  await page.selectOption('#kundSelect', kund);
  await page.click('#laddaBtn');
  await waitForClipLoaded(page, nyckel);
}

async function runLiveRegi(page, text, avsikt, outPng) {
  if (avsikt !== null && avsikt !== undefined) {
    await page.fill('#avsiktInput', avsikt);
    await page.press('#avsiktInput', 'Enter');
    await page.waitForTimeout(200);
  }
  const prevCards = await page.locator('#regiLogg .llm-card').count();
  await page.fill('#regiInput', text);
  await page.click('#regiSendBtn');
  await page.waitForFunction(
    (expected) => document.querySelectorAll('#regiLogg .llm-card').length >= expected,
    prevCards + 1,
    { timeout: 90000 }
  );
  await page.waitForTimeout(400);

  const lastCard = page.locator('#regiLogg .llm-card').last();
  const cardText = await lastCard.innerText();
  const stateAfter = await page.evaluate(() => window.__arbetsbordDebug.getState());

  await page.screenshot({ path: outPng });

  // Testa feedback-knapp på kortet
  const fbBtn = lastCard.locator('button[data-dom="kanns_ratt"]');
  if ((await fbBtn.count()) > 0) {
    const commentInp = lastCard.locator('.fb-comment-row input');
    await commentInp.fill(`Verifierad via UI (${stateAfter.klipp?.nyckel})`);
    await fbBtn.click();
    await page.waitForTimeout(300);
  }
  return { cardText, stateAfter };
}

async function main() {
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

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    pageErrors.push(String(err));
  });
  page.on('response', (res) => {
    if (res.status() >= 400) {
      httpErrors.push({ status: res.status(), url: res.url() });
    }
  });

  const rapport = { base: BASE, clips: {}, quickOps: null, regi: [], k7: {}, feedbackCount: 0 };

  try {
    await page.goto(`${BASE}/?klipp=notan`, { waitUntil: 'domcontentloaded', timeout: 25000 });
    await waitForClipLoaded(page, 'notan');

    // 1. Verifiera alla 5 dev-klipp
    for (const nyckel of ['notan', 'guacamole', 'gelato', 'asketch', 'btilltal']) {
      await loadClipViaUI(page, nyckel, '');
      const st = await page.evaluate(() => window.__arbetsbordDebug.getState());
      let stats = null;

      if (st.klipp.har_3d) {
        const midT = Math.min(Math.max(0.4, st.langd_s * 0.45), Math.max(0.4, st.langd_s - 0.1));
        await page.evaluate((t) => window.__arbetsbordDebug.setTime(t), midT);
        await page.waitForTimeout(250);
        stats = await sampleCanvasStats(page);
        assert(stats.ok && stats.std > 4 && stats.nonBgFrac > 0.02, `${nyckel}: 3D canvas tom (${JSON.stringify(stats)})`);
        assert(Math.abs(stats.aspect - 9 / 16) < 0.05, `${nyckel}: fel 9:16 aspekt ${stats.aspect}`);

        if (nyckel === 'notan' || nyckel === 'guacamole') {
          await page.click('#jamforBtn');
          await page.waitForFunction(
            () => {
              const v = document.getElementById('originalVideo');
              return v && v.readyState >= 2 && !v.seeking;
            },
            { timeout: 10000 }
          ).catch(() => {});
          await page.waitForTimeout(250);
          await page.screenshot({ path: path.join(UT_DIR, `${nyckel}_bredvid.png`) });
          await page.click('#jamforBtn');
          await page.waitForTimeout(200);
        } else {
          await page.screenshot({ path: path.join(UT_DIR, `${nyckel}_orig.png`) });
        }
      } else {
        const bannerHidden = await page.locator('#no3dBanner').evaluate((n) => n.hidden);
        assert(!bannerHidden, `${nyckel}: no3dBanner ej synlig för klipp utan 3D`);
        await page.screenshot({ path: path.join(UT_DIR, `${nyckel}_no3d.png`) });
      }

      rapport.clips[nyckel] = {
        har_3d: st.klipp.har_3d,
        langd_s: st.langd_s,
        fps: st.fps,
        antal_tagningar: st.tillstand?.tagningar?.length || 0,
        har_tal_url: Boolean(st.tillstand?.media?.tal_url),
        canvas: stats,
      };
    }

    // 2. Testa deterministiska snabbkontroller (<50 ms) + Ångra på guacamole
    await loadClipViaUI(page, 'guacamole', '');
    await page.click('.tab-btn[data-tab="snabb"]');
    await page.waitForTimeout(150);
    const t0Quick = Date.now();
    await page.evaluate(async () => {
      await window.__arbetsbordDebug.runOperation('byt_miljo', { tema: 'kok' });
      await window.__arbetsbordDebug.runOperation('objekt_lagg_till', { typ: 'spis', etikett: 'Stekbord' });
    });
    const quickMs = Date.now() - t0Quick;
    const afterQuick = await page.evaluate(() => window.__arbetsbordDebug.getState());
    assert(afterQuick.tillstand.scen.miljo_tema.id === 'kok', 'byt_miljo kok slog ej igenom');
    await page.click('#angraBtn');
    await page.waitForTimeout(250);
    await page.click('#aterstallBtn');
    await page.waitForTimeout(250);
    rapport.quickOps = { ok: true, elapsed_ms: quickMs, andringar_fore_angra: afterQuick.tillstand.andringar.length };

    // 3. Tre skarpa live Kontext-LLM-regikörningar via /api/regi
    await page.click('.tab-btn[data-tab="regi"]');

    // a) guacamole: flytt till kök + burgarprop
    await loadClipViaUI(page, 'guacamole', '');
    const regiA = await runLiveRegi(
      page,
      'Flytta scenen till ett trångt restaurangkök med rostfri bänk och vår signaturburgare som prop, men behåll samma tajming, blickar och vändning.',
      'Köksmiljö med bevarad humor och rörelsepacing',
      path.join(UT_DIR, 'regi_guacamole_kok.png')
    );
    await page.click('.tab-btn[data-tab="manus"]');
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(UT_DIR, 'manus_guacamole_kok.png') });
    await page.click('.tab-btn[data-tab="regi"]');
    rapport.regi.push({
      klipp: 'guacamole',
      version: regiA.stateAfter.tillstand.version,
      miljo: regiA.stateAfter.tillstand.scen?.miljo_tema?.id,
      tidal_waves: regiA.stateAfter.tillstand.tidal_waves?.length || 0,
      andringar: regiA.stateAfter.tillstand.andringar?.length || 0,
    });

    // b) notan: korta inledning 0.8s + skärmtext kafé Göteborg + paus
    await loadClipViaUI(page, 'notan', '');
    const notanOrigLen = (await page.evaluate(() => window.__arbetsbordDebug.getState())).langd_s;
    const regiB = await runLiveRegi(
      page,
      'Anpassa för ett kafé i Göteborg: byt miljö till kafé, korta inledningen med 0.8 sekunder, lägg till en skärmtext "Fika i Haga" och lägg en 0.5 sekunders paus före sista repliken.',
      'Kafékänsla med snärtigare krok',
      path.join(UT_DIR, 'regi_notan_kafe.png')
    );
    rapport.regi.push({
      klipp: 'notan',
      langd_orig_s: notanOrigLen,
      langd_ny_s: regiB.stateAfter.langd_s,
      tidsavbildning_antal: regiB.stateAfter.tillstand.tidsavbildning?.length || 0,
      skarmtext_antal: regiB.stateAfter.tillstand.media?.skarmtext?.length || 0,
      andringar: regiB.stateAfter.tillstand.andringar?.length || 0,
    });

    // c) gelato: byt till modern burgerbar + tryffelburgare + zooma in tagning 1
    await loadClipViaUI(page, 'gelato', 'kennysgelato2.0');
    const regiC = await runLiveRegi(
      page,
      'Byt miljö till en modern burgerbar, lägg till en skylt eller prop för vår tryffelburgare och tajta in kameran cirka 15 procent i första tagningen med bibehållen energi.',
      'Burgerbar-anpassning med tajtare inledande tagning',
      path.join(UT_DIR, 'regi_gelato_burger.png')
    );
    rapport.regi.push({
      klipp: 'gelato',
      miljo: regiC.stateAfter.tillstand.scen?.miljo_tema?.id,
      andringar: regiC.stateAfter.tillstand.andringar?.length || 0,
      k5_varningar: regiC.stateAfter.tillstand.k5?.varningar?.length || 0,
    });

    // 4. Verifiera k7_logg.jsonl och feedback_logg.jsonl
    const k7Path = path.join(UT_ROOT, 'k7_logg.jsonl');
    const fbPath = path.join(UT_ROOT, 'feedback_logg.jsonl');
    assert(fs.existsSync(k7Path), 'arbetsbord/ut/k7_logg.jsonl saknas');
    assert(fs.existsSync(fbPath), 'arbetsbord/ut/feedback_logg.jsonl saknas');

    const k7Lines = fs.readFileSync(k7Path, 'utf-8').trim().split(/\r?\n/).filter(Boolean).map((l) => JSON.parse(l));
    const fbLines = fs.readFileSync(fbPath, 'utf-8').trim().split(/\r?\n/).filter(Boolean).map((l) => JSON.parse(l));
    const k7Violations = k7Lines.filter(
      (r) =>
        r.generativt === true ||
        r.spegling === true ||
        (r.ok === false && r.typ !== 'blockerad') ||
        (r.ok !== false && ['byt_hand', 'spegla', 'generera_video', 'generera_bild'].includes(r.op))
    );
    assert(k7Lines.length >= 3, `För få poster i k7_logg.jsonl: ${k7Lines.length}`);
    assert(fbLines.length >= 3, `För få poster i feedback_logg.jsonl: ${fbLines.length}`);
    assert(k7Violations.length === 0, `K7-brott i k7_logg.jsonl: ${JSON.stringify(k7Violations)}`);

    rapport.k7 = { entries: k7Lines.length, violations: k7Violations.length };
    rapport.feedbackCount = fbLines.length;
    rapport.errors = {
      consoleErrors,
      pageErrors,
      httpErrors,
    };

    assert(consoleErrors.length === 0, `Console errors: ${consoleErrors.join(' | ')}`);
    assert(pageErrors.length === 0, `Page errors: ${pageErrors.join(' | ')}`);
    assert(httpErrors.length === 0, `HTTP >=400 errors: ${JSON.stringify(httpErrors)}`);

    fs.writeFileSync(path.join(UT_DIR, 'rapport.json'), JSON.stringify(rapport, null, 2), 'utf-8');
    console.log('VERIFIERA_UI_OK', JSON.stringify(rapport, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('VERIFIERA_UI_FAIL:', err);
  process.exit(1);
});
