import * as THREE from 'three';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
import {VRMLoaderPlugin,VRMUtils} from './vendor/three-vrm.module.js';
import * as Kalidokit from './vendor/kalidokit.js';

// A real, offline VRM/Kalidokit baseline. No image-space warping or per-frame IK fit.
export async function createRigged(spec,reference){
 const loader=new GLTFLoader();loader.register(parser=>new VRMLoaderPlugin(parser));
 const gltf=await loader.loadAsync(`./modeller/base_${spec.id==='A'?'female':'male'}.vrm`),vrm=gltf.userData.vrm;
 VRMUtils.rotateVRM0(vrm);vrm.springBoneManager?.reset();
 const root=new THREE.Group();root.name=spec.id+':vrm';root.userData.actor=spec.id;root.add(vrm.scene);
 const bone=n=>vrm.humanoid.getNormalizedBoneNode(n);
 root.updateMatrixWorld(true);
 const hip=bone('hips').getWorldPosition(new THREE.Vector3()),sh=bone('leftUpperArm').getWorldPosition(new THREE.Vector3()).add(bone('rightUpperArm').getWorldPosition(new THREE.Vector3())).multiplyScalar(.5);
 const targetHeight=-(reference.pose[11][1]+reference.pose[12][1])/2;
 const scale=targetHeight/sh.clone().sub(hip).y;vrm.scene.scale.setScalar(scale);
 const hipsRest=bone('hips').position.clone();vrm.scene.position.y=-hip.y*scale;
 const mapped={11:'leftUpperArm',12:'rightUpperArm',13:'leftLowerArm',14:'rightLowerArm',15:'leftHand',16:'rightHand',17:'leftLittleDistal',18:'rightLittleDistal',19:'leftIndexDistal',20:'rightIndexDistal',21:'leftThumbDistal',22:'rightThumbDistal',23:'leftUpperLeg',24:'rightUpperLeg',25:'leftLowerLeg',26:'rightLowerLeg',27:'leftFoot',28:'rightFoot',29:'leftFoot',30:'rightFoot',31:'leftToes',32:'rightToes'};
 const out={root,vrm,joints:[],mouthOpen:0,scale,update(frame,sourceCamera,placement){
  root.position.fromArray(placement.position);root.rotation.set(0,THREE.MathUtils.degToRad(placement.yaw),0);
  vrm.humanoid.resetNormalizedPose();bone('hips').position.copy(hipsRest);
  const world=frame.pose.map((p,i)=>({x:p[0],y:p[1],z:p[2],visibility:frame.image[i][3]}));
  const img=frame.image.map(p=>({x:p[0],y:p[1],z:p[2],visibility:p[3]}));
  const pose=Kalidokit.Pose.solve(world,img,{runtime:'mediapipe',enableLegs:!spec.seated});
  for(const name of ['Hips','Spine','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm','LeftHand','RightHand','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg']){
   const mode=window.__VRM_RETARGET||'unmirror',mirror=mode.includes('unmirror'),flip=mode.includes('xz');
   const sourceName=mirror?name.replace(/^(Left|Right)/,s=>s==='Left'?'Right':'Left'):name;
   const n=name[0].toLowerCase()+name.slice(1),b=bone(n),rot=name==='Hips'?pose.Hips.rotation:pose[sourceName];
   if(b&&rot)b.rotation.set(rot.x*(flip?-1:1),rot.y*(mirror?-1:1),rot.z*(mirror?-1:1)*(flip?-1:1),'XYZ');
  }
  if(spec.seated){for(const s of ['left','right']){bone(s+'UpperLeg').rotation.set(-Math.PI*.44,0,0);bone(s+'LowerLeg').rotation.set(Math.PI*.46,0,0);}}
  for(const h of frame.hands){const sol=Kalidokit.Hand.solve(h.image.map(p=>({x:p[0],y:p[1],z:p[2]})),h.side);for(const [k,r] of Object.entries(sol||{})){const b=bone(k[0].toLowerCase()+k.slice(1));if(b)b.rotation.set(r.x,r.y,r.z,'XYZ');}}
  // FaceLandmarker's camera-relative rotation is converted to room coordinates.
  root.updateMatrixWorld(true);const head=bone('head');const parentQ=head.parent.getWorldQuaternion(new THREE.Quaternion());
  head.quaternion.copy(parentQ.invert().multiply(sourceCamera.quaternion).multiply(new THREE.Quaternion().fromArray(frame.face.quaternion)).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),Math.PI)));
  const b=frame.face.blendshapes;out.mouthOpen=b.jawOpen;
  for(const [k,v] of Object.entries({aa:b.jawOpen,happy:(b.mouthSmileLeft+b.mouthSmileRight)/2,blinkLeft:b.eyeBlinkLeft,blinkRight:b.eyeBlinkRight,angry:(b.browDownLeft+b.browDownRight)/2,surprised:b.browInnerUp*.4}))vrm.expressionManager?.setValue(k,v);
  vrm.update(0);root.updateMatrixWorld(true);
  out.joints=Array.from({length:33},()=>null);
  for(const [i,n] of Object.entries(mapped)){const b=bone(n);if(b)out.joints[i]=b.getWorldPosition(new THREE.Vector3());}
  // Anatomical points on the rig's head, not copied from the tracking controls.
  out.joints[0]=head.localToWorld(new THREE.Vector3(0,.065,-.075));out.joints[7]=head.localToWorld(new THREE.Vector3(-.07,.08,0));out.joints[8]=head.localToWorld(new THREE.Vector3(.07,.08,0));
 }};
 return out;
}
