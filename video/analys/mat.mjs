// Mät: det som går att mäta direkt ur filen, utan modell. Samma metod som hagen-uis Mät-steg
// (ffprobe för längd, ffmpeg-filtret select=gt(scene,…) för klipp), men här sparas varje
// kandidats styrka, så att svaga klipp kan bedömas i stället för att kastas.
import path from 'node:path'
import fs from 'node:fs'
import { verktyg, kor } from './verktyg.mjs'

const r3 = v => Math.round(v * 1000) / 1000

export async function probe(fil) {
  const out = JSON.parse(await kor(verktyg.ffprobe, ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'json', path.basename(fil)], path.dirname(fil)))
  const v = out.streams?.find(s => s.codec_type === 'video')
  const [a, b] = (v?.r_frame_rate ?? '').split('/').map(Number)
  return {
    langd: r3(Number(out.format?.duration)),
    bredd: v?.width ?? null,
    hojd: v?.height ?? null,
    fps: a && b ? r3(a / b) : null,
    ljud: Boolean(out.streams?.some(s => s.codec_type === 'audio')),
  }
}

// Klippkandidater med styrka (0–1). Tröskeln är låg med flit: allt över 0,3 räknas som klipp i
// hagen-ui, men här vill vi också se snabba zoomar och blixtar som ligger under.
export const KANDIDAT_TROSKEL = 0.12
export async function klippkandidater(fil, troskel = KANDIDAT_TROSKEL) {
  // movie= tål inte Windows-sökvägar, så filen anges relativt sin katalog (samma som hagen-ui).
  const out = await kor(verktyg.ffprobe, [
    '-v', 'error', '-f', 'lavfi', '-i', `movie=${path.basename(fil)},select=gt(scene\\,${troskel})`,
    '-show_entries', 'frame=pts_time:frame_tags=lavfi.scene_score', '-of', 'csv=p=0',
  ], path.dirname(fil))
  return out.split(/\r?\n/).map(l => l.trim()).filter(Boolean).map(l => {
    const [t, s] = l.split(',').map(Number)
    return { t: r3(t), styrka: r3(s) }
  }).filter(k => Number.isFinite(k.t) && k.t > 0.05)
}
// Kandidater precis vid slutet (sista rutan, uttoning) är inga klipp mellan två bilder.
export const utanSlut = (kand, langd) => kand.filter(k => k.t < langd - 0.15)

// Bildrutor för analysen: fast takt, nedskalade. Rutan n (1-baserad) ligger vid t = (n-1)/takt.
export const ANALYS_FPS = 10
export const ANALYS_BREDD = 360
export async function bildrutor(fil, dir, fps = ANALYS_FPS) {
  fs.mkdirSync(dir, { recursive: true })
  await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-i', path.basename(fil), '-vf', `fps=${fps},scale=${ANALYS_BREDD}:-2`, '-q:v', '4', path.join(dir, '%05d.jpg')], path.dirname(fil))
  return fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).sort()
}

// Två rutor runt varje klippkandidat i full takt, för att jämföra före och efter.
export async function rutorRunt(fil, dir, tider, fps) {
  fs.mkdirSync(dir, { recursive: true })
  const ut = []
  for (const [n, t] of tider.entries()) {
    const fore = Math.max(0, t - 1.5 / fps)
    const efter = t + 0.5 / fps
    // a/b: grannrutorna runt klippet. c/d: en halv sekund före och efter, för övergångar.
    const vidFore = Math.max(0, t - 0.5)
    const vidEfter = t + 0.5
    for (const [namn, tt] of [['a', fore], ['b', efter], ['c', vidFore], ['d', vidEfter]]) {
      const f = path.join(dir, `k${String(n).padStart(3, '0')}${namn}.jpg`)
      await kor(verktyg.ffmpeg, ['-v', 'error', '-y', '-ss', String(tt), '-i', path.basename(fil), '-frames:v', '1', '-vf', `scale=${ANALYS_BREDD}:-2`, '-q:v', '4', f], path.dirname(fil))
    }
    const f = x => `k${String(n).padStart(3, '0')}${x}.jpg`
    ut.push({ t, a: f('a'), b: f('b'), ...(fs.existsSync(path.join(dir, f('c'))) && fs.existsSync(path.join(dir, f('d'))) ? { c: f('c'), d: f('d') } : {}) })
  }
  return ut
}
