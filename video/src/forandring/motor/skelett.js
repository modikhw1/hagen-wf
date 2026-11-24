// Skelettet: samma 22 leder och samma ordning som SMPL/SMPL-H (body). Det är vad GVHMR, WATCH,
// HY-Motion och Kimodo (via SMPL-X) ger ut, så riktig rörelsedata kan läggas in utan översättning.
// Y uppåt, figuren tittar mot +Z, vänster sida är +X. Viloläget är T-pose, precis som i SMPL.
// Mått i meter, ungefär SMPL:s neutrala kropp.

export const JOINTS = [
  'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2',
  'left_ankle', 'right_ankle', 'spine3', 'left_foot', 'right_foot', 'neck',
  'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
  'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist',
]

export const PARENT = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19]

// Förskjutning från föräldern i viloläget.
export const OFFSET = {
  pelvis: [0, 0.93, 0],
  left_hip: [0.07, -0.09, 0],
  right_hip: [-0.07, -0.09, 0],
  spine1: [0, 0.11, -0.02],
  left_knee: [0.03, -0.39, 0.01],
  right_knee: [-0.03, -0.39, 0.01],
  spine2: [0, 0.13, 0.01],
  left_ankle: [0, -0.4, -0.04],
  right_ankle: [0, -0.4, -0.04],
  spine3: [0, 0.06, 0],
  left_foot: [0, -0.05, 0.12],
  right_foot: [0, -0.05, 0.12],
  neck: [0, 0.21, -0.03],
  left_collar: [0.07, 0.11, -0.01],
  right_collar: [-0.07, 0.11, -0.01],
  head: [0, 0.08, 0.04],
  left_shoulder: [0.11, 0.04, -0.01],
  right_shoulder: [-0.11, 0.04, -0.01],
  left_elbow: [0.26, 0, 0],
  right_elbow: [-0.26, 0, 0],
  left_wrist: [0.25, 0, 0],
  right_wrist: [-0.25, 0, 0],
}

export const INDEX = Object.fromEntries(JOINTS.map((j, i) => [j, i]))
export const CHILDREN = JOINTS.map((_, i) => PARENT.flatMap((p, k) => (p === i ? [k] : [])))
