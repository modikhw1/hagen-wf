// Lyft bildrutor till enkla kroppar i scenens värld, där golvet ligger på y = 0.
import { Quaternion as Kvaternion } from 'three/src/math/Quaternion.js'
import { Vector3 as Vektor } from 'three/src/math/Vector3.js'
import { ASPEKT, F, iKamera } from './geometri.mjs'

const LITET = 1e-8
const MARGINAL = 0.03
const COCO = new Map([
  ['disk', 'dining table'],
  ['bord', 'dining table'],
  ['stol', 'chair'],
  ['flaska', 'bottle'],
  ['skarm', 'tv'],
  ['vaxt', 'potted plant'],
])
const begransa = (tal, min, max) => Math.max(min, Math.min(max, tal))
const matt = tal => begransa(Number.isFinite(tal) ? tal : 0.1, 0.02, 12)

export function lyftScen(scen2d, kamera, { personer = [] } = {}) {
  const antaget = []
  const origo = new Vektor(...kamera.pos)
  const vridning = new Kvaternion(...kamera.q).normalize()
  const blick = new Vektor(0, 0, -1).applyQuaternion(vridning)
  const framat = blick.clone().setY(0)
  if (framat.lengthSq() < LITET) {
    framat.set(0, 0, -1)
    antaget.push('Kameran tittar lodrätt, väggens riktning antas vara längs −z.')
  }
  framat.normalize()
  const gir = Math.atan2(-framat.x, -framat.z) * 180 / Math.PI || 0
  if (Math.abs(gir) > 1) {
    antaget.push(`Kamerans gir är ${gir.toFixed(1)} grader. Väggplanet används vid lyftet, men lokalformatet återger bara väggens z.`)
  }

  const djupast = personer.reduce((djup, person) => Math.max(djup, Number.isFinite(person.djup) ? person.djup : 0), 0)
  const angivetAvstand = scen2d.vagg?.avstand
  const onskatAvstand = Number.isFinite(angivetAvstand) ? angivetAvstand : 4
  const vaggavstand = begransa(Math.max(onskatAvstand, djupast + 0.8), 0.3, 15)
  if (vaggavstand !== angivetAvstand) {
    antaget.push(`Väggens avstånd antas vara ${vaggavstand.toFixed(2)} m efter hänsyn till personer och avståndsgränser.`)
  }
  const vaggpunkt = origo.clone().addScaledVector(framat, vaggavstand)
  const upp = new Vektor(0, 1, 0)
  const ursprung = scen2d.element ?? []
  const lyfta = new Array(ursprung.length)
  const besok = new Array(ursprung.length).fill(0)
  const kedja = []
  const cykliska = new Set()

  const strale = (u, v) => iKamera(u, v, 1).normalize().applyQuaternion(vridning)
  const skarning = (u, v, punkt, normal) => {
    const riktning = strale(u, v)
    const namnare = riktning.dot(normal)
    if (Math.abs(namnare) < LITET) return null
    const langd = punkt.clone().sub(origo).dot(normal) / namnare
    return langd > 0 ? origo.clone().addScaledVector(riktning, langd) : null
  }
  const urStorlek = (u, v, djup) => {
    const riktning = strale(u, v)
    // F ger djup längs kameraaxeln, inte strållängd. Punkten ska stanna på sin bildstråle.
    return origo.clone().addScaledVector(riktning, djup / riktning.dot(blick))
  }

  function lyft(index) {
    if (besok[index] === 2) return lyfta[index]
    if (besok[index] === 1) {
      for (const deltagare of kedja.slice(kedja.indexOf(index))) cykliska.add(deltagare)
      return null
    }
    besok[index] = 1
    kedja.push(index)
    const e = ursprung[index]
    const namn = e.namn ?? `Element ${index + 1}`
    let placering = e.placering
    let underlag
    if (placering === 'pa_element') {
      if (Number.isInteger(e.pa) && e.pa >= 0 && e.pa < ursprung.length) underlag = lyft(e.pa)
      if (!underlag || cykliska.has(index)) {
        placering = 'fritt'
        antaget.push(`${namn}: okänt eller cykliskt pa, behandlas som fritt.`)
      }
    }

    const [ymin, xmin, ymax, xmax] = e.ruta.map(tal => begransa(Number.isFinite(tal) ? tal : 500, 0, 1000))
    const rutbredd = Math.max(LITET, (xmax - xmin) / 1000)
    const ruthojd = Math.max(LITET, (ymax - ymin) / 1000)
    const u = (xmin + xmax) / 2000
    const v = (ymin + ymax) / 2000
    const [angivenBredd, angivenHojd, angivetDjup] = e.storlek.map(matt)
    let djup = begransa(F * angivenHojd / ruthojd, 0.3, 15)
    let form = e.form
    let kroppsDjup = angivetDjup
    let botten = null
    let pos

    if (placering === 'golv' || placering === 'pa_element') {
      botten = placering === 'golv' ? 0 : underlag.pos[1] + underlag.storlek[1] / 2
      const traff = ymax > 985 ? null : skarning(u, ymax / 1000, new Vektor(0, botten, 0), upp)
      const markdjup = traff?.clone().sub(origo).dot(framat)
      if (traff && markdjup > LITET) {
        // Måtten skattas vid framkanten i golvets riktning, före kroppens djupförskjutning.
        djup = begransa(markdjup, 0.3, 15)
        pos = traff
        if (djup !== markdjup) {
          pos.x = origo.x + (pos.x - origo.x) * djup / markdjup
          pos.z = origo.z + (pos.z - origo.z) * djup / markdjup
          antaget.push(`${namn}: avståndet till stödytan begränsades till ${djup.toFixed(2)} m.`)
        }
      } else {
        pos = urStorlek(u, v, djup)
        antaget.push(`${namn}: djup ur storleken eftersom nederkanten är avskuren eller strålen inte når stödytan framför kameran.`)
      }
    } else if (placering === 'vagg') {
      pos = skarning(u, v, vaggpunkt, framat)
      if (!pos) {
        pos = urStorlek(u, v, djup)
        pos.addScaledVector(framat, vaggavstand - pos.clone().sub(origo).dot(framat))
        antaget.push(`${namn}: bildstrålen når inte väggen, läget på väggplanet är antaget.`)
      }
      djup = begransa(pos.clone().sub(origo).dot(blick), 0.3, 15)
      pos.addScaledVector(framat, -MARGINAL)
      form = form === 'lada' ? 'lada' : 'platta'
      kroppsDjup = Math.min(angivetDjup, 0.05)
    } else {
      pos = urStorlek(u, v, djup)
      antaget.push(`${namn}: djup ur storleken för placering ${placering ?? 'fritt'}.`)
    }

    const synligBredd = rutbredd * ASPEKT * djup / F
    const bredd = matt(xmin < 15 || xmax > 985 ? Math.max(synligBredd, angivenBredd) : synligBredd)
    const hojd = matt(ymin < 15 || ymax > 985 ? angivenHojd : ruthojd * djup / F)
    if (botten !== null) {
      pos.addScaledVector(framat, kroppsDjup / 2)
      pos.y = botten + hojd / 2
    }

    const rotY = placering === 'vagg' && form === 'platta' ? gir : 0
    const vinkel = rotY * Math.PI / 180
    const halvBredd = Math.abs(framat.x * Math.cos(vinkel) - framat.z * Math.sin(vinkel)) * bredd / 2
    const halvDjup = Math.abs(framat.x * Math.sin(vinkel) + framat.z * Math.cos(vinkel)) * kroppsDjup / 2
    const utstrackning = halvBredd + (form === 'platta' ? 0 : halvDjup)
    const grans = vaggavstand - Math.max(MARGINAL, utstrackning)
    const mittdjup = pos.clone().sub(origo).dot(framat)
    if (mittdjup > grans) {
      pos.addScaledVector(framat, grans - mittdjup)
      antaget.push(`${namn}: flyttat framför väggen.`)
    }

    const resultat = {
      namn,
      form,
      pos: pos.toArray(),
      storlek: [bredd, hojd, kroppsDjup],
      rotY,
      farg: e.farg,
      material: e.material,
      lyser: Boolean(e.lyser),
      ...(COCO.has(e.kategori) ? { coco: COCO.get(e.kategori) } : {}),
      skymmer: Boolean(e.framfor_personer || e.kategori === 'disk'),
    }
    lyfta[index] = resultat
    besok[index] = 2
    kedja.pop()
    return resultat
  }

  for (const index of ursprung.keys()) lyft(index)
  return {
    golv: { farg: scen2d.golv?.farg, material: scen2d.golv?.material },
    vagg: { z: vaggpunkt.z, farg: scen2d.vagg?.farg, material: scen2d.vagg?.material },
    element: lyfta,
    antaget,
  }
}
