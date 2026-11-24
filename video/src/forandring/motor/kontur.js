import * as THREE from 'three'

// Kontur som i en tecknad bild: varje form får en mörk "baksida" som trycks ut en fast bredd
// i skärmplanet (normalen projiceras till bilden). Ritas i samma pass som allt annat.

export const KONTUR = new THREE.ShaderMaterial({
  uniforms: {
    thickness: { value: 0.005 }, // andel av bildens höjd
    aspect: { value: 9 / 16 },
    color: { value: new THREE.Color(0.012, 0.012, 0.012) },
  },
  vertexShader: `
    uniform float thickness;
    uniform float aspect;
    void main() {
      vec4 pos = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      vec3 nv = normalize(normalMatrix * normal);
      vec2 dir = (projectionMatrix * vec4(nv, 0.0)).xy;
      float len = length(dir);
      if (len > 1e-5) dir /= len;
      pos.xy += vec2(dir.x / aspect, dir.y) * thickness * 2.0 * pos.w;
      gl_Position = pos;
    }`,
  fragmentShader: `
    uniform vec3 color;
    void main() { gl_FragColor = vec4(color, 1.0); }`,
  side: THREE.BackSide,
})

export function kontur(root, { skip = () => false } = {}) {
  const meshes = []
  root.traverse(o => { if (o.isMesh && !o.userData.kontur && !skip(o)) meshes.push(o) })
  for (const m of meshes) {
    const k = new THREE.Mesh(m.geometry, KONTUR)
    k.userData.kontur = true
    k.castShadow = false
    k.receiveShadow = false
    m.add(k)
  }
  return root
}
