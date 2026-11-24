// Rörelseordboken: det personerna kan göra. Varje klipp är en rörelse, inte en scen.
// Här är de handgjorda nyckelposer (källa: 'hand'). I biblioteket ersätts de av riktiga rörelser
// ur riktiga klipp (källa: 'gvhmr:<klipp>#<scen>') eller genererade (källa: 'kimodo:<prompt>'),
// i ledformat. Manuset pekar bara på id, så bytet syns inte för resten av motorn.
//
// Vinklar i grader, se NEUTRAL i pose.js. Bara det som avviker från neutral hållning skrivs ut.

const C = (id, langd, loop, nycklar, om) => ({ id, typ: 'semantisk', kalla: 'hand', langd, loop, nycklar, om })

export const ORDBOK = Object.fromEntries([
  C('sta', 4, true, [
    { t: 0, p: {} },
    { t: 2, p: { hips: [0, 2, 0], spine: [3, -1.5, 0], lLeg: [0, 4], rLeg: [1, 2], rKnee: 6 } },
  ], 'står, flyttar vikten lite'),

  C('knada', 1.1, true, [
    { t: 0, p: { spine: [20, 0, 0], neck: [24, 0, 0], lArm: [16, 42, 45], rArm: [16, 42, 45], lElbow: 62, rElbow: 62, lWrist: [20, 0], rWrist: [20, 0] } },
    { t: 0.55, p: { spine: [27, 0, 0], neck: [20, 0, 0], lArm: [14, 58, 45], rArm: [14, 58, 45], lElbow: 30, rElbow: 30, lWrist: [30, 0], rWrist: [30, 0], lift: -0.015 } },
  ], 'knådar deg på bänken'),

  C('ga', 1.05, true, [
    { t: 0, p: { spine: [5, 0, 0], lLeg: [24, 3], lKnee: 4, rLeg: [-17, 3], rKnee: 14, lArm: [8, -16, 0], rArm: [8, 18, 0], lift: -0.02 } },
    { t: 0.26, p: { spine: [5, 0, 0], lLeg: [4, 3], lKnee: 10, rLeg: [12, 3], rKnee: 55, lAnkle: 0, rAnkle: 10, lift: 0.012 } },
    { t: 0.525, p: { spine: [5, 0, 0], rLeg: [24, 3], rKnee: 4, lLeg: [-17, 3], lKnee: 14, rArm: [8, -16, 0], lArm: [8, 18, 0], lift: -0.02 } },
    { t: 0.79, p: { spine: [5, 0, 0], rLeg: [4, 3], rKnee: 10, lLeg: [12, 3], lKnee: 55, lAnkle: 10, lift: 0.012 } },
  ], 'går'),

  C('armar_i_kors', 1.4, false, [
    { t: 0, p: {} },
    { t: 0.7, p: { spine: [-4, 0, 0], neck: [-6, 8, 0], lArm: [22, 30, 75], rArm: [22, 30, 75], lElbow: 116, rElbow: 122 } },
    { t: 1.4, p: { spine: [-5, 0, 0], neck: [-4, 10, -6], lArm: [22, 30, 75], rArm: [22, 30, 75], lElbow: 116, rElbow: 122 } },
  ], 'armarna i kors, skeptisk'),

  C('racka_fram', 1.6, false, [
    { t: 0, p: { rArm: [18, 30, 0], rElbow: 80 } },
    { t: 0.6, p: { spine: [10, 0, -3], neck: [6, 0, 0], rArm: [8, 70, 0], rElbow: 14, rWrist: [-10, 0] } },
    { t: 1.6, p: { spine: [12, 0, -3], neck: [8, 0, 0], rArm: [8, 72, 0], rElbow: 12, rWrist: [-10, 0] } },
  ], 'räcker fram något med höger hand'),

  C('smaka', 2.2, false, [
    { t: 0, p: { rArm: [14, 35, 40], rElbow: 95 } },
    { t: 0.55, p: { neck: [-8, 0, 0], rArm: [14, 50, 70], rElbow: 140, rWrist: [10, 0] } },
    { t: 0.95, p: { neck: [4, 0, 0], rArm: [14, 35, 45], rElbow: 110 } },
    { t: 1.3, p: { neck: [-3, 4, 0], rArm: [14, 35, 45], rElbow: 110 } },
    { t: 1.7, p: { neck: [5, -4, 0], rArm: [14, 35, 45], rElbow: 110 } },
    { t: 2.2, p: { neck: [-2, 0, 0], rArm: [14, 35, 45], rElbow: 110 } },
  ], 'tar en tugga och tuggar'),

  C('tummen_upp', 1.3, false, [
    { t: 0, p: {} },
    { t: 0.45, p: { spine: [-4, 0, 6], neck: [4, 0, 12], rArm: [24, 28, 15], rElbow: 105 } },
    { t: 0.8, p: { spine: [-5, 0, 6], neck: [8, 0, 12], rArm: [24, 32, 15], rElbow: 100, lift: 0.012 } },
    { t: 1.3, p: { spine: [-4, 0, 6], neck: [4, 0, 12], rArm: [24, 28, 15], rElbow: 105 } },
  ], 'tummen upp'),

  C('jubla', 0.8, true, [
    { t: 0, p: { spine: [-6, 0, 0], neck: [-10, 0, 0], lArm: [160, 8, 0], rArm: [160, 8, 0], lElbow: 18, rElbow: 18 } },
    { t: 0.4, p: { spine: [-3, 0, 0], neck: [-6, 0, 0], lArm: [148, 14, 0], rArm: [148, 14, 0], lElbow: 34, rElbow: 34, lift: 0.03, lKnee: 12, rKnee: 12 } },
  ], 'jublar med armarna uppe'),

  C('nicka', 1, true, [
    { t: 0, p: { neck: [12, 0, 0] } },
    { t: 0.5, p: { neck: [-4, 0, 0] } },
  ], 'nickar'),
].map(c => [c.id, c]))

// Namn att visa för människor. Id:t är det manuset använder.
export const NAMN = { sta: 'står', knada: 'knådar', ga: 'går', armar_i_kors: 'armar i kors', racka_fram: 'räcker fram', smaka: 'smakar', tummen_upp: 'tummen upp', jubla: 'jublar', nicka: 'nickar' }
