// E13: Vertex tar högst 10 videofiler per anrop. Kundens historik (24 klipp) sätts därför ihop till band om fyra
// klipp, med klippnumret inbränt i bildens hörn ("KLIPP 7") så att modellen kan hänvisa till enskilda klipp.
// v2 (16 nov kväll): 1 bild/s (Gemini samplar ändå 1 bild/s), crf 35 och 24k ljud, eftersom uppladdningen härifrån
// inte orkade 13 MB per anrop. Första versionen hade 2 bilder/s, crf 33, 32k.
// Banden cachas i Downloads/letrend-e13/band/ och byggs om när urvalet av klipp ändras.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { verktyg, kor } from '../analys/verktyg.mjs'

const LITEN = path.join(os.homedir(), 'Downloads', 'letrend-e13'), BAND = path.join(LITEN, 'band')
const PER_BAND = 4
const litenFil = id => path.join(LITEN, `${id}.mp4`)
const langd = async f => Number((await kor(verktyg.ffprobe, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f])).trim())
const harLjud = async f => (await kor(verktyg.ffprobe, ['-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', f])).trim() !== ''

// klipp: [{ id, datum, visningar, text }] i den ordning de ska visas. Svarar [{ fil, klipp: [{ nr, ..., start }] }].
export async function byggBand(konto, klipp) {
  fs.mkdirSync(BAND, { recursive: true })
  const finns = klipp.filter(k => fs.existsSync(litenFil(k.id)))
  const manifest = path.join(BAND, `${konto}.json`), nyckel = 'v2:' + finns.map(k => k.id).join(',')
  if (fs.existsSync(manifest)) { const m = JSON.parse(fs.readFileSync(manifest, 'utf8')); if (m.nyckel === nyckel && m.band.every(b => fs.existsSync(b.fil))) return m.band }
  const band = []
  for (let b = 0; b * PER_BAND < finns.length; b++) {
    const del = finns.slice(b * PER_BAND, (b + 1) * PER_BAND), delar = []
    let t = 0
    for (const [i, k] of del.entries()) {
      const nr = b * PER_BAND + i + 1, ut = path.join(BAND, `${konto}-nr${nr}.mp4`), ljud = await harLjud(litenFil(k.id))
      // cwd = Windows-typsnittsmappen, så att drawtext slipper en sökväg med kolon
      await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-i', litenFil(k.id), ...(ljud ? [] : ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono']), '-vf', `drawtext=fontfile=arialbd.ttf:text='KLIPP ${nr}':x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=4`, '-r', '1', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '35', '-pix_fmt', 'yuv420p', '-map', '0:v', '-map', ljud ? '0:a' : '1:a', '-c:a', 'aac', '-ar', '44100', '-ac', '1', '-b:a', '24k', ...(ljud ? [] : ['-shortest']), ut], 'C:/Windows/Fonts')
      const d = await langd(ut)
      delar.push({ nr, id: k.id, datum: k.datum, visningar: k.visningar, text: k.text, start: Math.round(t), fil: ut }); t += d
    }
    const lista = path.join(BAND, `${konto}-band${b + 1}.txt`), fil = path.join(BAND, `${konto}-band${b + 1}.mp4`)
    fs.writeFileSync(lista, delar.map(d => `file '${d.fil.replaceAll('\\', '/')}'`).join('\n'))
    await kor(verktyg.ffmpeg, ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', fil])
    for (const d of delar) { fs.rmSync(d.fil); delete d.fil }
    fs.rmSync(lista)
    band.push({ fil, sekunder: Math.round(t), klipp: delar })
  }
  fs.writeFileSync(manifest, JSON.stringify({ konto, nyckel, band }, null, 1))
  return band
}

const tid = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
// Delar till beaconDelar: text som förklarar bandet, sedan bandet.
export function bandDelar(band) {
  const delar = []
  for (const [i, b] of band.entries()) {
    delar.push({ text: `Band ${i + 1} av ${band.length} (${tid(b.sekunder)}), klippnumret står i bildens övre vänstra hörn:\n${b.klipp.map(k => `Klipp ${k.nr} börjar vid ${tid(k.start)}. Publicerat ${k.datum}, ${k.visningar ?? '?'} visningar. Bildtext: ${(k.text || '').replace(/\s+/g, ' ').slice(0, 140)}`).join('\n')}` })
    delar.push({ fil: b.fil })
  }
  return delar
}
