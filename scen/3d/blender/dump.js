// Read-only export of the evaluated player. Never updates poses, materials or visibility.
import * as THREE from '../vendor/three.module.js';

const trs = o => ({position:o.position.toArray(), quaternion:o.quaternion.toArray(), scale:o.scale.toArray(), visible:o.visible});
const world = o => {
  const p=new THREE.Vector3(), q=new THREE.Quaternion(), s=new THREE.Vector3();
  o.matrixWorld.decompose(p,q,s);
  return {position:p.toArray(),quaternion:q.toArray(),scale:s.toArray(),matrix:o.matrixWorld.toArray(),visible:o.visible};
};
const geometry = g => ({positions:Array.from(g.attributes.position.array),
  indices:g.index?Array.from(g.index.array):Array.from({length:g.attributes.position.count},(_,i)=>i),
  colors:g.attributes.color?Array.from(g.attributes.color.array):null});
const faces = c => ({eyeL:c.eyes[0],eyeR:c.eyes[1],browL:c.brows[0],browR:c.brows[1],mouth:c.mouth});

export function dumpPlayer({xbots,objects,camera,spec,shotAt}, options={}) {
  if(options.assets) {
    return {actors:Object.fromEntries(Object.entries(xbots).map(([id,c])=>[id,{
      bones:Object.fromEntries(Object.entries(c.bones).map(([n,b])=>[n,{name:b.name,parent:b.parent.isBone?b.parent.name.replace(/^mixamorig:?/,''):null}])),
      meshes:c.meshes.map((m,i)=>({...geometry(m.geometry),name:m.name||`hair-${i}`,
        bindMatrix:m.bindMatrix.toArray(),boneNames:m.skeleton.bones.map(b=>b.name.replace(/^mixamorig:?/,'')),
        boneInverses:m.skeleton.boneInverses.map(m=>m.toArray()),
        skinIndices:Array.from(m.geometry.attributes.skinIndex.array),skinWeights:Array.from(m.geometry.attributes.skinWeight.array),
        color:m.material.color.toArray()})),
      faceGeometry:geometry(c.mouth.geometry),faceColors:Object.fromEntries(Object.entries(faces(c)).map(([n,o])=>[n,o.material.color.toArray()])),
      faceLandmarks:{nose:c.näsa.toArray(),earL:c.öron[0].toArray(),earR:c.öron[1].toArray()}
    }])),
    // Verification-only occluders: the import function deliberately does not create a set or props.
    occluders:Object.fromEntries(Object.entries(objects).map(([id,o])=>{
      const meshes=[];o.traverse(m=>{if(m.isMesh)meshes.push({...geometry(m.geometry),matrix:o.matrixWorld.clone().invert().multiply(m.matrixWorld).toArray()});});
      return [id,{...world(o),meshes}];
    }))};
  }
  if(options.timeline) return {shots:spec.shots.map(s=>({id:s.id,duration:s.duration,source:s.source,audioRange:s.audioRange,tyst:!!s.tyst})),
    shotAt:options.timeline.map(t=>({t,shot:shotAt(t).shot.id,start:shotAt(t).start}))};
  return {t:window.__frame.t,shot:window.__frame.shot,sourceT:window.__frame.sourceT,audioTime:window.__frame.audioTime,
    audioMode:window.__frame.audioMode,sourceIndex:window.__frame.index,mainActor:(window.__frame.mouthByActor&&Object.keys(window.__frame.mouthByActor)[0]),
    actors:Object.fromEntries(Object.entries(xbots).map(([id,c])=>[id,c.root.visible?{
      visible:true,root:world(c.root),bones:Object.fromEntries(Object.entries(c.bones).map(([n,b])=>[n,{...trs(b),world:b.matrixWorld.toArray()}])),
      face:{...trs(c.face),parent:'Head',parts:Object.fromEntries(Object.entries(faces(c)).map(([n,o])=>[n,trs(o)]))},
      jointsWorld:c.joints.map(p=>p?.toArray()??null),mouthOpen:c.mouthOpen
    }:{visible:false}])),
    props:Object.fromEntries(spec.props.map(p=>[p.id,world(objects[p.id])])),
    camera:{...world(camera),fov:camera.fov,aspect:camera.aspect,near:camera.near,far:camera.far},
    joints:window.__frame.joints,mouthOpen:window.__frame.mouthOpen,mouthAperture_m:window.__frame.mouthAperture_m,
    errors:[...window.__frame.errors]};
}
