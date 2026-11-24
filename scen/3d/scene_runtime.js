import * as THREE from 'three';
export const role=a=>a.semantic?.role||a.id;
export const key=o=>o.semantic?.key||(o.semantic?.owner?`${o.semantic.owner}:${o.semantic.label}`:o.id);
export function actorFor(spec,ref){return spec.actors.find(a=>a.id===ref||role(a)===ref);}
export function objectFor(spec,ref){return [...spec.set,...spec.props].find(o=>o.id===ref||key(o)===ref);}
export function shotFor(spec,ref){return spec.shots.find(s=>s.id===ref||s.semantic?.key===ref);}
export function merge(a,b){if(!b)return structuredClone(a);const c=structuredClone(a);for(const [k,v]of Object.entries(b))c[k]=v&&typeof v==='object'&&!Array.isArray(v)?merge(c[k]||{},v):structuredClone(v);return c;}
export function shotAt(spec,time){let start=0;for(const shot of spec.shots){if(time<start+shot.duration-1e-7)return {shot,start,local:Math.max(0,time-start)};start+=shot.duration;}const shot=spec.shots.at(-1);return {shot,start:start-shot.duration,local:Math.max(0,Math.min(shot.duration-1e-5,time-start+shot.duration))};}
const v=a=>new THREE.Vector3(...a);
export function cameraState(shot,time){
 const keys=shot.camera.keyframes;let a=keys[0],b=a;
 for(const k of keys){if(k.t<=time)a=k;if(k.t>time){b=k;break;}b=a;}
 const f=a===b?0:THREE.MathUtils.clamp((time-a.t)/(b.t-a.t),0,1);
 let pos=v(a.pos).lerp(v(b.pos),f);const target=v(a.target).lerp(v(b.target),f),up=v(a.up||[0,1,0]).lerp(v(b.up||[0,1,0]),f);
 const orbit=shot.camera.orbit;if(orbit){const t=THREE.MathUtils.clamp((time-orbit.start)/(orbit.end-orbit.start),0,1);pos=v(orbit.startPos).sub(v(orbit.pivot)).applyAxisAngle(v([0,1,0]),THREE.MathUtils.degToRad(orbit.degrees)*t).add(v(orbit.pivot));}
 return {pos,target,up,fov:THREE.MathUtils.lerp(a.fov,b.fov,f)};
}
export function applyCamera(camera,shot,time){const c=cameraState(shot,time);camera.position.copy(c.pos);camera.up.copy(c.up);camera.lookAt(c.target);camera.fov=c.fov;camera.updateProjectionMatrix();camera.updateMatrixWorld(true);return c.target;}
export function placementAt(actor,entry,time){
 const p=merge(actor.transform,entry.transform),keys=entry.transformKeyframes;if(!keys?.length)return p;
 let a=keys[0],b=a;for(const k of keys){if(k.t<=time)a=k;if(k.t>time){b=k;break;}b=a;}
 const f=a===b?0:THREE.MathUtils.clamp((time-a.t)/(b.t-a.t),0,1);if(a.position)p.position=v(a.position).lerp(v(b.position||a.position),f).toArray();
 if(a.yaw!==undefined){const delta=((b.yaw-a.yaw+540)%360)-180;p.yaw=a.yaw+f*delta;}return p;
}
export function animateFrame(raw,track,settings){
 const f=structuredClone(raw);if(settings.handAnchor==='imageRayAtPoseDepth'&&f.poseFused)f.pose=f.poseFused;
 const intensity=settings.intensity??1,base=track.neutralPoses?.[f.shot];if(intensity!==1&&base)f.pose=f.pose.map((p,i)=>p.map((x,j)=>base[i][j]+(x-base[i][j])*intensity));
 if(settings.mirror){
  const pairs=[[1,4],[2,5],[3,6],[7,8],[9,10],...Array.from({length:11},(_,i)=>[11+i*2,12+i*2])];
  for(const [a,b]of pairs){[f.pose[a],f.pose[b]]=[f.pose[b],f.pose[a]];[f.image[a],f.image[b]]=[f.image[b],f.image[a]];}
  f.pose.forEach(p=>p[0]*=-1);f.image.forEach(p=>p[0]=1-p[0]);
  f.hands.forEach(h=>{h.side=h.side==='Left'?'Right':'Left';h.world.forEach(p=>p[0]*=-1);h.image.forEach(p=>p[0]=1-p[0]);});
  const q=f.face.quaternion;q[1]*=-1;q[2]*=-1;const b=f.face.blendshapes;
  for(const k of Object.keys(b).filter(k=>k.endsWith('Left'))){const other=k.replace(/Left$/,'Right');[b[k],b[other]]=[b[other],b[k]];}
 }
 const mood=settings.mood||{},amount=mood.amount??1,b=f.face.blendshapes;
 const presets={stressed:{browInnerUp:.65,browDownLeft:.28,browDownRight:.28,mouthPressLeft:.25,mouthPressRight:.25},happy:{mouthSmileLeft:.8,mouthSmileRight:.8,browInnerUp:.15},angry:{browDownLeft:.8,browDownRight:.8},sad:{browInnerUp:.6,mouthFrownLeft:.5,mouthFrownRight:.5},neutral:{}};
 const values=mood.values||presets[mood.name]||{};for(const [k,val]of Object.entries(values))b[k]=THREE.MathUtils.clamp((b[k]||0)*(1-amount)+val*amount,0,1);
 return f;
}
