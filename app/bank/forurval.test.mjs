// node --test bank/forurval.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { setTimeout as paus } from 'node:timers/promises'
import { lasProfillista, kandidater, losHandtag, losProfiler, tolkaSokSvar } from './profiler.mjs'
import { forurvalProfil, listaProfil, hamtaValda } from './forurval.mjs'

const idag = new Date('2026-10-31T00:00:00Z')
const DYGN = 86_400_000
const profil = text => lasProfillista(text)[0]
const klipp = (id, extra = {}) => ({ id: String(id), langd: 20, datum: '2026-10-01', text: `Egen början ${id}`, ...extra })
const valda = lista => lista.filter(k => k.valt)
function tillfalligMapp(t) {
  const mapp = fs.mkdtempSync(path.join(os.tmpdir(), 'bank-forurval-'))
  t.after(() => {
    assert.equal(path.dirname(path.resolve(mapp)), path.resolve(os.tmpdir()))
    assert.ok(path.basename(mapp).startsWith('bank-forurval-'))
    fs.rmSync(mapp, { recursive: true, force: true })
  })
  return mapp
}

test('läser ett verkligt utdrag ur bulktik.txt och skiljer handtag från visningsnamn', () => {
  const text = `https://bulktik.com/
Bild 3
 * @fratelliörebro (Fratelli Örebro)
 * @berseaujkpg (Berseau)
 * @fratellibistro... (Fratelli Bistro Jönköping)
 * @scandiclaholmen (Scandic Laholmen)
Bild 7
 * @blackstonesteakhousej... (Blackstone Steakhouse)
Bild 11
 * @coknajs / Cok Najs (Turkisk gatumat)
 * @blackstonesteakhouse / Blackstone Steakhouse`
  const lista = lasProfillista(text)
  assert.equal(lista.length, 7)
  assert.equal(lista[0].handtag, 'fratelliörebro')
  assert.equal(lista[0].namn, 'Fratelli Örebro')
  assert.equal(lista[0].ogiltigt, true)
  assert.deepEqual(kandidater(lista[0]), ['fratelliorebro'])
  assert.equal(lista[4].handtag, 'blackstonesteakhousej...')
  assert.equal(lista[4].avkortat, true)
  assert.deepEqual(kandidater(lista[4]), [])
  assert.equal(lista[5].handtag, 'coknajs')
  assert.equal(lista[5].namn, 'Cok Najs')
  assert.equal(profil('@coknajs / Cok Najs').namn, 'Cok Najs')
  assert.equal(lista[1].rad, '* @berseaujkpg (Berseau)')
})

test('kandidater bevarar giltiga handtag, viker accenter och hoppar över avkortningar', () => {
  assert.deepEqual(kandidater(profil('@b.b_kebab')), ['b.b_kebab'])
  assert.deepEqual(kandidater(profil('@Café Rønnes ÅÄÖ')), ['caferonnesaao'])
  assert.deepEqual(kandidater(profil('@fratelli…')), [])
  assert.deepEqual(kandidater(profil('@fel-handtag')), [])
  assert.equal(profil('@ensamt').namn, null)
  assert.equal(profil('https://www.tiktok.com/@kappabar').handtag, 'kappabar')
  assert.deepEqual(lasProfillista('# @kommentar\r\nBild 1\r\n'), [])
})

test('losHandtag löser direkt utan sökning', async () => {
  const p = profil('@coknajs')
  const svar = await losHandtag(p, {
    prova: async h => {
      assert.equal(h, 'coknajs')
      return { ok: true, antal: 1 }
    },
    sok: async () => assert.fail('Direkt träff ska inte sökas'),
  })
  assert.deepEqual(svar, { handtag: 'coknajs', hur: 'direkt', provade: ['coknajs'] })
})

test('losHandtag löser ogiltig stavning med ASCII', async () => {
  const svar = await losHandtag(profil('@fratelliörebro'), {
    prova: async h => {
      assert.equal(h, 'fratelliorebro')
      return { ok: true, antal: 1 }
    },
    sok: async () => assert.fail('ASCII-träff ska inte sökas'),
  })
  assert.deepEqual(svar, { handtag: 'fratelliorebro', hur: 'ascii', provade: ['fratelliorebro'] })
})

test('losHandtag söker avkortade handtag och verifierar varje kandidat', async () => {
  const anrop = []
  const p = profil('@blackstonesteakhousej... (Blackstone Steakhouse)')
  const svar = await losHandtag(p, {
    prova: async h => {
      anrop.push(h)
      return { ok: true, antal: h === 'blackstonesteakhousejkpg' ? 1 : 0 }
    },
    sok: async indata => {
      assert.equal(indata, p)
      return ['@blackstone_fel', 'blackstone_fel', 'https://www.tiktok.com/@blackstonesteakhousejkpg/']
    },
  })
  assert.deepEqual(anrop, ['blackstone_fel', 'blackstonesteakhousejkpg'])
  assert.deepEqual(svar, { handtag: 'blackstonesteakhousejkpg', hur: 'sokning', provade: anrop })
})

test('losHandtag redovisar misslyckanden, avvisar tomma konton och provar inte dubletter', async () => {
  const svar = await losHandtag(profil('@fel'), {
    prova: async h => {
      if (h === 'fel') throw new Error('Nätfel')
      return { ok: true, antal: 0 }
    },
    sok: async () => ['fel', 'ogiltig å', 'tomt', 'annat'],
  })
  assert.deepEqual(svar, { handtag: null, hur: 'misslyckad', provade: ['fel', 'tomt', 'annat'] })
  assert.equal((await losHandtag(profil('@fel...'), {
    prova: async () => assert.fail('Avkortningen får inte provas'),
    sok: async () => { throw new Error('Sökfel') },
  })).hur, 'misslyckad')
})

test('losHandtag går från giltig men felaktig stavning till sökning, med högst tre förslag', async () => {
  const svar = await losHandtag(profil('@fel'), {
    prova: async h => ({ ok: h === 'ratt', antal: 1 }),
    sok: async () => ['ratt'],
  })
  assert.deepEqual(svar, { handtag: 'ratt', hur: 'sokning', provade: ['fel', 'ratt'] })
  const begransat = await losHandtag(profil('@fel...'), {
    prova: async h => ({ ok: h === 'fjarde', antal: 1 }),
    sok: async () => ['forsta', 'andra', 'tredje', 'fjarde'],
  })
  assert.deepEqual(begransat.provade, ['forsta', 'andra', 'tredje'])
  assert.equal(begransat.handtag, null)
})

test('söksvar kan innehålla kodstaket, källor och inledande emoji', () => {
  assert.deepEqual(tolkaSokSvar('🔎 Svaret:\n```json\n{"kandidater":["@coknajs","coknajs","https://www.tiktok.com/@kappabar/","fratelliörebro"]}\n```\nKällor: [1]'), ['coknajs', 'kappabar'])
  assert.deepEqual(tolkaSokSvar('["a","b","c","d"]'), ['a', 'b', 'c'])
  assert.deepEqual(tolkaSokSvar('Se källa [1]. Svaret: {"kandidater":["coknajs"]}'), ['coknajs'])
  assert.deepEqual(tolkaSokSvar('{"kandidater":[]}'), [])
  assert.throws(() => tolkaSokSvar('Inget strukturerat svar'), /JSON-lista/)
})

test('profilkörningen har högst tre samtidiga profiler och återanvänder lösta profiler', async t => {
  const fil = path.join(tillfalligMapp(t), 'profiler.json')
  const profiler = lasProfillista(Array.from({ length: 7 }, (_, i) => `@konto${i}`).join('\n'))
  let aktiva = 0
  let hogst = 0
  let anrop = []
  const prova = async h => {
    anrop.push(h)
    aktiva++
    hogst = Math.max(hogst, aktiva)
    await paus(5)
    aktiva--
    return { ok: h !== 'konto6', antal: h === 'konto6' ? 0 : 1 }
  }
  const alternativ = { fil, prova, sok: async () => [], skriv: () => {} }
  const forsta = await losProfiler(profiler, alternativ)
  assert.equal(hogst, 3)
  assert.equal(anrop.length, 7)
  assert.equal(forsta.filter(p => p.handtag).length, 6)
  assert.deepEqual(JSON.parse(fs.readFileSync(fil, 'utf8')), forsta)
  anrop = []
  assert.deepEqual(await losProfiler(profiler, alternativ), forsta)
  assert.deepEqual(anrop, ['konto6'])
})

test('förurval respekterar längd- och åldersgränser inklusive exakta gränsvärden', () => {
  const datum = dagar => new Date(idag.getTime() - dagar * DYGN).toISOString()
  const lista = [
    klipp('saknad', { langd: undefined }),
    klipp('null', { langd: null }),
    klipp('kort', { langd: 4.99 }),
    klipp('min', { langd: 5 }),
    klipp('max', { langd: 90 }),
    klipp('lang', { langd: 90.01 }),
    klipp('gammal', { datum: datum(901) }),
    klipp('aldersgrans', { datum: datum(900) }),
    klipp('tva-fel', { langd: 1, datum: datum(901) }),
  ]
  const resultat = forurvalProfil(lista, { idag })
  assert.deepEqual(valda(resultat).map(k => k.id), ['min', 'max', 'aldersgrans'])
  assert.deepEqual(resultat[0].skal, ['Längd saknas'])
  assert.deepEqual(resultat[1].skal, ['Längd saknas'])
  assert.deepEqual(resultat[2].skal, ['För kort'])
  assert.deepEqual(resultat[5].skal, ['För långt'])
  assert.deepEqual(resultat[6].skal, ['För gammalt'])
  assert.deepEqual(resultat[8].skal, ['För kort', 'För gammalt'])
  assert.ok(resultat.filter(k => !k.valt).every(k => k.poang === 0))
  assert.equal(valda(forurvalProfil([klipp(1, { langd: 4 })], { idag, minLangd: 4, maxLangd: 4 })).length, 1)
})

test('poängen följer 60/40 och percentilerna är relativa till profilen', () => {
  const lista = [40, 60, 60, 40, 0].map((gillanden, i) => klipp(i, { visningar: (i + 1) * 100, gillanden }))
  const liten = forurvalProfil(lista, { idag })
  const stor = forurvalProfil(lista.map(k => ({ ...k, visningar: k.visningar * 10 })), { idag })
  assert.deepEqual(liten.map(k => k.poang), stor.map(k => k.poang))
  for (const [i, poang] of [0.4, 0.45, 0.5, 0.55, 0.6].entries()) assert.ok(Math.abs(liten[i].poang - poang) < 1e-12)
})

test('lika värden får lika percentiler och saknad metadata ger ändliga poäng', () => {
  const lista = Array.from({ length: 5 }, (_, i) => klipp(i, { visningar: 100, gillanden: 10 }))
  const resultat = forurvalProfil([...lista, klipp('utan', { datum: null })], { idag })
  assert.ok(resultat.slice(0, 5).every(k => k.poang === 0.5))
  assert.equal(resultat[5].poang, 0)
  assert.ok(resultat.every(k => Number.isFinite(k.poang)))
})

test('mångfaldsregeln tar högst 40 procent med samma första 25 tecken', () => {
  const serie = Array.from({ length: 12 }, (_, i) => klipp(i, { text: `${i % 2 ? 'DAGENS LUNCH I RESTAURANGEN' : 'dagens lunch i restaurangen'} del ${i}`, visningar: 10000 + i, gillanden: 1000 + i }))
  const ovriga = Array.from({ length: 8 }, (_, i) => klipp(100 + i, { visningar: 100 + i, gillanden: 1 }))
  const resultat = forurvalProfil([...serie, ...ovriga], { idag, perProfil: 10 })
  assert.equal(valda(resultat).length, 10)
  assert.equal(valda(resultat).filter(k => Number(k.id) < 100).length, 4)
  assert.equal(resultat.filter(k => k.skal.includes('Liknande text: mångfaldstak')).length, 8)
})

test('mångfaldstaket gäller också när färre klipp än perProfil kan väljas', () => {
  const serie = Array.from({ length: 10 }, (_, i) => klipp(i, { text: 'Samma text i varje klipp' }))
  const andra = [klipp(100), klipp(101), klipp(102)]
  const urval = valda(forurvalProfil([...serie, ...andra], { idag, perProfil: 10 }))
  assert.equal(urval.length, 5)
  assert.equal(urval.filter(k => Number(k.id) < 100).length, 2)
  assert.equal(valda(forurvalProfil(serie, { idag })).length, 1)
})

test('perProfil är ett tak och tomma texter räknas inte som en gemensam serie', () => {
  const lista = Array.from({ length: 30 }, (_, i) => klipp(i, { text: '' }))
  assert.equal(valda(forurvalProfil(lista, { idag })).length, 25)
  assert.equal(valda(forurvalProfil(lista, { idag, perProfil: 7 })).length, 7)
  assert.equal(valda(forurvalProfil(lista, { idag, perProfil: 0 })).length, 0)
  assert.deepEqual(forurvalProfil([], { idag }), [])
  assert.throws(() => forurvalProfil(lista, { perProfil: -1 }), /perProfil/)
})

test('utan visningar väljs nyast först, även om listan inte är sorterad', () => {
  const lista = [3, 1, 5, 2, 4].map(i => klipp(i, { datum: `2026-10-0${i}` }))
  const resultat = forurvalProfil(lista, { idag, perProfil: 2 })
  assert.deepEqual(valda(resultat).map(k => k.id).sort(), ['4', '5'])
  assert.equal(resultat.find(k => k.id === '5').poang, 1)
  assert.equal(resultat.find(k => k.id === '1').poang, 0)
  assert.ok(resultat.every(k => k.skal.includes('Nyhet (färre än 5 klipp med visningar)')))
})

test('även fyra klipp med visningar använder nyhet, noll räknas som inga visningar', () => {
  const lista = Array.from({ length: 5 }, (_, i) => klipp(i, { datum: `2026-10-0${i + 1}`, visningar: i === 4 ? 0 : 1000 - i, gillanden: 10 }))
  const resultat = forurvalProfil(lista, { idag, perProfil: 1 })
  assert.equal(valda(resultat)[0].id, '4')
})

test('förurval bevarar indata och övrig metadata', () => {
  const indata = Object.freeze([Object.freeze(klipp(1, { extra: 'bevaras' }))])
  const resultat = forurvalProfil(indata, { idag })
  assert.equal(resultat[0].extra, 'bevaras')
  assert.notEqual(resultat[0], indata[0])
  assert.equal(indata[0].poang, undefined)
})

test('listning normaliserar metadata, cachar 24 timmar och förnyar vid gränsen', async t => {
  const bank = tillfalligMapp(t)
  let anrop = 0
  const anropa = async args => {
    anrop++
    assert.deepEqual(args, ['--flat-playlist', '-J', '--playlist-end', '300', 'https://www.tiktok.com/@konto'])
    return JSON.stringify({ entries: [{ id: '123', duration: 12, view_count: 90, like_count: 9, comment_count: 2, repost_count: 1, timestamp: 1790812800, title: 'En text' }] })
  }
  const lista = await listaProfil('konto', { bank, nu: idag, anropa })
  assert.deepEqual(lista, [{ id: '123', url: 'https://www.tiktok.com/@konto/video/123', langd: 12, visningar: 90, gillanden: 9, kommentarer: 2, delningar: 1, datum: '2026-10-01', text: 'En text' }])
  assert.deepEqual(await listaProfil('konto', { bank, nu: new Date(idag.getTime() + DYGN - 1), anropa }), lista)
  assert.equal(anrop, 1)
  await listaProfil('konto', { bank, nu: new Date(idag.getTime() + DYGN), anropa })
  assert.equal(anrop, 2)
})

test('listfel förstör inte en tidigare cache', async t => {
  const bank = tillfalligMapp(t)
  const fil = path.join(bank, 'konto', 'lista.json')
  fs.mkdirSync(path.dirname(fil))
  const gammal = JSON.stringify({ konto: 'konto', hamtad: '2020-01-01', klipp: [klipp(1)] })
  fs.writeFileSync(fil, gammal)
  await assert.rejects(listaProfil('konto', { bank, nu: idag, anropa: async () => '{}' }), /saknar klipplista/)
  assert.equal(fs.readFileSync(fil, 'utf8'), gammal)
})

test('hämtning använder samma flaggor, hoppar över befintliga och registrerar med metadata', async t => {
  const data = tillfalligMapp(t)
  const ut = path.join(data, 'klipp')
  const utDir = path.join(ut, 'konto')
  fs.mkdirSync(utDir, { recursive: true })
  fs.writeFileSync(path.join(utDir, '1.mp4'), '')
  fs.writeFileSync(path.join(data, 'kallor.json'), JSON.stringify({ tidigare: { fil: 'bevaras.mp4' } }))
  const lista = [1, 2, 3].map(i => ({ ...klipp(i), handtag: 'konto', url: `https://www.tiktok.com/@konto/video/${i}`, valt: i !== 3, visningar: 50, gillanden: 5, kommentarer: 1, delningar: 0 }))
  let anrop = 0
  const alternativ = { data, ut, skriv: () => {}, anropa: async args => {
    anrop++
    assert.deepEqual(args, ['-f', 'bv*[height<=1280][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b', '--merge-output-format', 'mp4', '--write-info-json', '--no-write-comments', '--sleep-requests', '1', '--sleep-interval', '2', '--max-sleep-interval', '5', '-o', path.join(utDir, '%(id)s.%(ext)s'), lista[1].url])
    fs.writeFileSync(path.join(utDir, '2.mp4'), '')
    fs.writeFileSync(path.join(utDir, '2.info.json'), JSON.stringify({ duration: 21, view_count: 500, like_count: 50, comment_count: 12, repost_count: 3, upload_date: '20261002', description: 'Ny beskrivning', track: 'Ljudet' }))
  } }
  assert.deepEqual(await hamtaValda(lista, alternativ), { nya: 1, befintliga: 1, fel: 0 })
  assert.equal(anrop, 1)
  const kallor = JSON.parse(fs.readFileSync(path.join(data, 'kallor.json'), 'utf8'))
  assert.equal(kallor.tidigare.fil, 'bevaras.mp4')
  assert.equal(kallor['konto-1'].visningar, 50)
  assert.deepEqual(kallor['konto-2'], { fil: path.join(utDir, '2.mp4').replaceAll('\\', '/'), konto: 'konto', kalla: 'bank', video: '2', url: lista[1].url, langd: 21, visningar: 500, gillanden: 50, kommentarer: 12, delningar: 3, datum: '2026-10-02', text: 'Ny beskrivning', ljud: 'Ljudet' })
  assert.equal(kallor['konto-3'], undefined)
  assert.deepEqual(await hamtaValda(lista, alternativ), { nya: 0, befintliga: 2, fel: 0 })
  assert.equal(anrop, 1)
  assert.match(fs.readFileSync(path.join(data, 'bank', 'hamta-logg.txt'), 'utf8'), /hämtat och registrerat/)
})

test('hämtfel loggas utan att registrera saknade filer', async t => {
  const data = tillfalligMapp(t)
  const resultat = await hamtaValda([{ ...klipp(1), handtag: 'konto', valt: true, url: 'https://www.tiktok.com/@konto/video/1' }], {
    data, ut: path.join(data, 'klipp'), skriv: () => {}, anropa: async () => { throw new Error('Provfel') },
  })
  assert.deepEqual(resultat, { nya: 0, befintliga: 0, fel: 1 })
  assert.equal(fs.existsSync(path.join(data, 'kallor.json')), false)
  assert.match(fs.readFileSync(path.join(data, 'bank', 'hamta-logg.txt'), 'utf8'), /Provfel/)
})
