import * as THREE from 'three';
import {RoundedBoxGeometry} from './vendor/RoundedBoxGeometry.js';
export const V=a=>new THREE.Vector3(...a);
const sphere=new THREE.SphereGeometry(1,20,14), box=new RoundedBoxGeometry(1,1,1,3,.12);
export function disposeGeometry(root){const seen=new Set();root.traverse(o=>{if(o.isMesh&&o.geometry!==sphere&&o.geometry!==box&&!seen.has(o.geometry)){seen.add(o.geometry);o.geometry.dispose();}});}
const materials=new Map();
export function mat(color){if(!materials.has(color))materials.set(color,new THREE.MeshStandardMaterial({color,roughness:.78}));return materials.get(color);}
export function mesh(parent,geo,color,pos=[0,0,0],scale=[1,1,1]){const m=new THREE.Mesh(geo,mat(color));m.position.fromArray(pos);m.scale.fromArray(scale);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
export function ellipsoid(p,c,pos,s){return mesh(p,sphere,c,pos,s);}
export function rounded(p,c,pos,s){return mesh(p,box,c,pos,s);}
export function cylinder(p,c,pos,r1,r2,h){return mesh(p,new THREE.CylinderGeometry(r1,r2,h,24),c,pos);}
export function segment(parent,color){const g=new THREE.Group();parent.add(g);g.add(new THREE.Mesh(new THREE.CylinderGeometry(1,1,1,14),mat(color)));g.add(new THREE.Mesh(sphere,mat(color)));g.add(new THREE.Mesh(sphere,mat(color)));return g;}
export function fitSegment(g,a,b,r){const delta=b.clone().sub(a),len=delta.length();g.position.copy(a).add(b).multiplyScalar(.5);g.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());g.children[0].scale.set(r,len,r);g.children[1].position.y=len/2;g.children[2].position.y=-len/2;g.children[1].scale.setScalar(r);g.children[2].scale.setScalar(r);}

export function makeObject(o){
 const g=new THREE.Group();g.name=o.id;g.userData.semantic=o;const [w,h,d]=o.dims,c=o.color||'#25282b';
 if(o.type==='table'){
  rounded(g,c,[0,h/2-.025,0],[w,.05,d]);cylinder(g,'#31363a',[0,-.02,0],.035,.045,h-.07);rounded(g,c,[0,-h/2+.025,0],[Math.min(w,.48),.045,Math.min(d,.48)]);
 }else if(o.type==='chair'){
  rounded(g,c,[0,h/2,0],[w,.055,d]);rounded(g,c,[0,h/2+.23,-d*.43],[w,.42,.045]);
  for(const x of [-1,1])for(const z of [-1,1])cylinder(g,'#33383b',[x*w*.38,-.01,z*d*.38],.015,.015,h);
 }else if(o.type==='window_wall'){
  rounded(g,'#a6bdc1',[0,.15,0],[w,h-.3,.025]);
  for(let x=-w/2;x<=w/2;x+=.8)rounded(g,c,[x,0,-.035],[.055,h,.09]);
  for(const y of [-h/2+.12,.15,h/2])rounded(g,c,[0,y,-.04],[w,.055,.1]);
  // Outside volumes remain real geometry, visible from free orbit too.
  for(let x=-w/2+.2;x<w/2;x+=.75)rounded(g,'#81928b',[x,-.3,.5],[.5,1.6,.3]);
 }else if(o.type==='pendant'){
  cylinder(g,'#282d32',[0,.18,0],.008,.008,.36);cylinder(g,c,[0,-.03,0],w*.25,w/2,h*.45);cylinder(g,'#fff0c8',[0,-.11,0],w*.45,w*.45,.015);
 }else if(o.type==='counter'){
  rounded(g,c,[0,0,0],[w,h,d]);rounded(g,'#ba9d75',[0,h/2,0],[w+.04,.045,d+.05]);
  for(let x=-w*.4;x<w*.5;x+=.16)rounded(g,'#777269',[x,0,-d/2-.005],[.035,h*.85,.02]);
 }else if(['paper_cup','drink_can','burger','pizza_slice','fries_box','food_box','paper_wrap','tray','sauce_cup','card_terminal','fry'].includes(o.type)){
  prop(g,o.type,w,h,d);
 }else rounded(g,c,[0,0,0],[w,h,d]);
 g.position.fromArray(o.transform.position);g.rotation.y=THREE.MathUtils.degToRad(o.transform.yaw||0);g.visible=o.visible!==false;return g;
}
function prop(g,type,w,h,d){
 if(type==='paper_cup'){
  cylinder(g,'#e8ddbd',[0,0,0],w/2,w*.37,h*.92);cylinder(g,'#f5f1e7',[0,h*.47,0],w*.55,w*.55,h*.055);cylinder(g,'#d7d0bf',[0,h*.505,0],w*.39,w*.46,h*.04);
  rounded(g,'#b98b45',[0,0,w*.455],[w*.47,h*.29,.004]);
 }else if(type==='drink_can'){
  cylinder(g,'#a5bed0',[0,0,0],w*.47,w*.47,h*.92);cylinder(g,'#dadfe0',[0,h*.47,0],w*.45,w*.45,h*.03);cylinder(g,'#dbe1e5',[0,-h*.47,0],w*.45,w*.45,h*.035);
  cylinder(g,'#799db8',[0,0,0],w*.476,w*.476,h*.38);rounded(g,'#e8f0ee',[0,0,w*.47],[w*.48,h*.17,.002]);rounded(g,'#6c787d',[0,h*.49,0],[w*.2,.002,w*.33]);
 }else if(type==='burger'){
  // Packaging is a separately addressable object; food swaps preserve it.
  ellipsoid(g,'#c98637',[0,h*.19,0],[w*.5,h*.34,d*.5]);cylinder(g,'#895028',[0,-h*.16,0],w*.48,w*.48,h*.16);
  cylinder(g,'#4f7c36',[0,-h*.01,0],w*.51,w*.50,h*.06);rounded(g,'#e8b94c',[0,-h*.10,0],[w*.94,h*.045,d*.94]);ellipsoid(g,'#d59b51',[0,-h*.36,0],[w*.49,h*.16,d*.49]);
  for(let i=0;i<8;i++){let a=i*2.4;ellipsoid(g,'#eee0b1',[Math.cos(a)*w*.28,h*.45,Math.sin(a)*d*.27],[.004,.0015,.002]);}
 }else if(type==='pizza_slice'){
  const shape=new THREE.Shape();shape.moveTo(-w/2,-d/2);shape.lineTo(w/2,-d/2);shape.lineTo(0,d/2);shape.closePath();
  const m=mesh(g,new THREE.ExtrudeGeometry(shape,{depth:h*.35,bevelEnabled:true,bevelSize:.007,bevelThickness:.005,bevelSegments:2}),'#e4ad4e');m.rotation.x=-Math.PI/2;
  for(let i=0;i<3;i++)cylinder(g,'#aa4934',[(i-1)*w*.18,h*.43,d*.18],w*.09,w*.09,.005);
 }else if(type==='fries_box'){
  rounded(g,'#b89a70',[0,-h*.46,0],[w*.88,.003,d*.74]);
  for(const x of [-1,1]){const m=rounded(g,'#ceaf82',[x*w*.47,-h*.18,0],[.003,h*.6,d*.82]);m.rotation.z=-x*.13;}
  for(const z of [-1,1]){const m=rounded(g,'#d9be94',[0,-h*.19,z*d*.40],[w,h*.58,.003]);m.rotation.x=z*.12;}
  for(let i=0;i<9;i++){const f=rounded(g,'#edbb50',[((i%3)-1)*w*.25,h*.13+(i%2)*h*.08,(Math.floor(i/3)-1)*d*.17],[w*.11,h*.69,d*.10]);f.rotation.z=(i%3-1)*.12;}
 }else if(type==='food_box'){
  rounded(g,'#d5b68c',[0,-h*.47,0],[w,.003,d]);
  for(const x of [-1,1]){const m=rounded(g,'#caa77a',[x*w*.48,-h*.29,0],[.003,h*.38,d]);m.rotation.z=-x*.12;}
  rounded(g,'#e1c99e',[0,-h*.28,d*.49],[w,h*.4,.003]);
  const lid=rounded(g,'#c9a77c',[0,h*.05,-d*.46],[w,h*.95,.003]);lid.rotation.x=-.32;
  for(const x of [-1,1]){const paper=rounded(g,'#f4e7ca',[x*w*.32,-h*.35,0],[w*.4,.001,d*.88]);paper.rotation.z=x*.12;}
 }else if(type==='paper_wrap'){
  const shape=new THREE.CylinderGeometry(w*.20,w*.45,h,7,1,true);const paper=mesh(g,shape,'#ddc39d');paper.scale.z=d/w;paper.rotation.z=-.13;paper.material=mat('#ddc39d').clone();paper.material.side=THREE.DoubleSide;
  for(const s of [-1,1]){const flap=rounded(g,'#eee1bf',[s*w*.24,-h*.3,0],[w*.45,.002,d]);flap.rotation.z=s*.18;}
 }else if(type==='tray'){
  rounded(g,'#5e3430',[0,-h*.3,0],[w,h*.3,d]);for(const x of [-1,1])rounded(g,'#6c4137',[x*w*.48,0,0],[.012,h,d]);for(const z of [-1,1])rounded(g,'#6c4137',[0,0,z*d*.48],[w,h,.012]);
 }else if(type==='sauce_cup'){
  cylinder(g,'#eee5cc',[0,0,0],w/2,w*.4,h);cylinder(g,'#a95832',[0,h*.505,0],w*.43,w*.43,.002);
 }else if(type==='card_terminal'){
  rounded(g,'#30343b',[0,0,0],[w,h,d]);rounded(g,'#99c4ac',[0,h*.52,-d*.2],[w*.77,.003,d*.36]);for(let i=0;i<9;i++)rounded(g,'#b7b8b8',[(i%3-1)*w*.22,h*.52,(Math.floor(i/3)*.15+.03)*d],[w*.15,.004,d*.09]);
 }else rounded(g,'#edbd52',[0,0,0],[w,h,d]);
}

export class Character{
 constructor(spec){
  this.spec=spec;this.root=new THREE.Group();this.root.name=spec.id;this.root.userData.actor=spec.id;
  const l=spec.look;this.torso=ellipsoid(this.root,l.shirt,[0,.2,0],[l.torsoWidth*.55,.23,l.torsoDepth*.6]);this.pelvis=ellipsoid(this.root,l.trousers,[0,0,0],[.18,.11,.13]);
  this.neck=segment(this.root,l.skin);this.arms=[];this.legs=[];
  for(let side=0;side<2;side++){
   this.arms.push([segment(this.root,l.shirt),segment(this.root,spec.id==='A'?l.shirt:l.skin),segment(this.root,l.skin)]);
   this.legs.push([segment(this.root,l.trousers),segment(this.root,l.trousers),ellipsoid(this.root,'#27292c',[0,0,0],[.065,.045,.13])]);
  }
  this.head=new THREE.Group();this.root.add(this.head);ellipsoid(this.head,l.skin,[0,0,0],l.head);
  this.nose=ellipsoid(this.head,l.skin,[0,-.043,l.head[2]*.98],[.016,.019,.025]);
  this.ears=[ellipsoid(this.head,l.skin,[l.head[0]*.87,-.005,-.024],[.023,.035,.018]),ellipsoid(this.head,l.skin,[-l.head[0]*.87,-.005,-.024],[.023,.035,.018])];
  this.eyes=[];this.brows=[];
  for(const sign of [-1,1]){
   ellipsoid(this.head,'#f6eee6',[sign*.041,.008,.091],[.023,.012,.012]);
   this.eyes.push(ellipsoid(this.head,'#353130',[sign*.041,.007,.102],[.008,.009,.004]));
   this.brows.push(rounded(this.head,l.hair,[sign*.041,.054,.095],[.045,.008,.009]));
  }
  this.mouth=ellipsoid(this.head,'#65332f',[0,-.080,.086],[.025,.004,.008]);
  this.lowerLip=ellipsoid(this.head,'#c87e70',[0,-.088,.087],[.026,.004,.008]);
  const scalp=mesh(this.head,new THREE.SphereGeometry(1,20,12,0,Math.PI*2,0,Math.PI*.47),l.hair,[0,.015,-.012],[l.head[0]*1.06,l.head[1]*1.06,l.head[2]*1.06]);
  if(l.hairStyle==='long'){
   ellipsoid(this.head,l.hair,[0,-.07,-.066],[.12,.22,.075]);
   for(const s of [-1,1])ellipsoid(this.head,l.hair,[s*.102,-.115,-.015],[.038,.215,.06]);
   for(let i=0;i<5;i++)ellipsoid(this.torso,'#dfd9c9',[0,-.55+i*.28,.98],[.032,.025,.028]);
  }else if(l.hairStyle==='short'){
   // One swept cap volume with a vertex-color side part, not separate tufts/buns.
   const pos=scalp.geometry.attributes.position,colors=[],color=new THREE.Color(l.hair);
   for(let i=0;i<pos.count;i++){let x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i);const part=Math.abs(x-.28)<.045&&z>-.4;pos.setXYZ(i,x+.10*y*y,y*(1+.08*(1-x)),z);const c=color.clone().multiplyScalar(part?.48:1);colors.push(c.r,c.g,c.b);}
   scalp.geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));scalp.geometry.computeVertexNormals();scalp.material=mat('#ffffff').clone();scalp.material.vertexColors=true;
   this.zip=rounded(this.torso,'#c4c5bd',[0,.6,.83],[.020,.32,.035]);
   for(const s of [-1,1]){const collar=rounded(this.torso,l.shirt,[s*.20,.76,.68],[.28,.23,.08]);collar.rotation.z=s*.5;}
  }else{
   scalp.material=mat('#17191c');scalp.scale.multiplyScalar(1.06);rounded(this.head,'#16181c',[0,.073,-.125],[.18,.018,.13]);rounded(this.head,'#3c3d3b',[0,.083,.096],[.075,.023,.009]);
  }
  this.hands=[];
  for(let s=0;s<2;s++){
   const palm=ellipsoid(this.root,l.skin,[0,0,0],[.031,.039,.018]);const fingers=[];
   for(let i=0;i<20;i++)fingers.push(segment(this.root,l.skin));this.hands.push({palm,fingers});
  }
  this.joints=[];this.grips={};this.mouthOpen=0;
 }
 update(frame,sourceCamera,placement){
  const spec=this.spec,l=spec.look,root=this.root;root.position.fromArray(placement.position);root.rotation.set(0,THREE.MathUtils.degToRad(placement.yaw||0),0);root.scale.setScalar(l.height/({'A':1.65,'B':1.78,'C':1.78}[spec.id]||1.78));root.updateMatrixWorld(true);
  let p=frame.pose.map(a=>new THREE.Vector3(a[0],-a[1],-a[2]));
  if(spec.seated){
   p[23]=V([.13,0,0]);p[24]=V([-.13,0,0]);p[25]=V([.14,-.13,.35]);p[26]=V([-.14,-.13,.35]);p[27]=V([.14,-.53,.37]);p[28]=V([-.14,-.53,.37]);p[31]=V([.14,-.55,.48]);p[32]=V([-.14,-.55,.48]);
  }
  const shoulder=p[11].clone().add(p[12]).multiplyScalar(.5),hip=p[23].clone().add(p[24]).multiplyScalar(.5);
  const y=shoulder.clone().sub(hip).normalize(),x=p[11].clone().sub(p[12]).normalize(),z=x.clone().cross(y).normalize();x.copy(y).cross(z).normalize();
  this.torso.position.copy(shoulder).add(hip).multiplyScalar(.5);this.torso.scale.set(l.torsoWidth*l.build*.57,(shoulder.distanceTo(hip)+.065)*.59,l.torsoDepth*l.build*.60);this.torso.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x,y,z));this.pelvis.position.copy(hip);
  const sourceRot=sourceCamera.quaternion.clone(),headQ=root.quaternion.clone().invert().multiply(sourceRot).multiply(new THREE.Quaternion().fromArray(frame.face.quaternion));
  const huvudMitt=p[0].clone().sub(V([0,-.043,l.head[2]*.98]).applyQuaternion(headQ));
  if(placement.lookAt?.amount>0){const tl=root.worldToLocal(V(placement.lookAt.target)),ql=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(tl,huvudMitt,V([0,1,0]))),vinkel=headQ.angleTo(ql);if(vinkel>1e-4)headQ.slerp(ql,Math.min(placement.lookAt.amount,THREE.MathUtils.degToRad(80)/vinkel));}   // titta mot: bara huvudet
  this.head.quaternion.copy(headQ);this.head.position.copy(huvudMitt);
  const neckEnd=this.head.position.clone().add(V([0,-.105,0]).applyQuaternion(headQ));fitSegment(this.neck,shoulder,neckEnd,.047);
  for(let s=0;s<2;s++){
   const a=p[11+s],b=p[13+s],c=p[15+s];fitSegment(this.arms[s][0],a,b,l.sleeveRadius*l.build);fitSegment(this.arms[s][1],b,c,spec.id==='A'?.053:.043);
   fitSegment(this.arms[s][2],c,c.clone().lerp(b,.16),.039);
   fitSegment(this.legs[s][0],p[23+s],p[25+s],.092);fitSegment(this.legs[s][1],p[25+s],p[27+s],.067);this.legs[s][2].position.copy(p[27+s]).add(V([0,-.025,.06]));
   const measured=frame.hands.find(h=>h.side===(s===0?'Left':'Right'));let hp;
   if(measured){const hw=measured.world.map(a=>V([a[0],-a[1],-a[2]]));hp=hw.map(v=>v.clone().sub(hw[0]).add(c));}
   else{
    // Relaxed fingers, anchored to the measured pose wrist. No invented gesture.
    const dir=c.clone().sub(b).normalize(),right=new THREE.Vector3(1,0,0),front=right.clone().cross(dir).normalize();hp=[c.clone()];
    for(let f=0;f<5;f++)for(let j=1;j<=4;j++)hp.push(c.clone().addScaledVector(dir,.022+j*.016).addScaledVector(right,(f-2)*.014).addScaledVector(front,.008*(j-1)**1.4));
   }
   const hand=this.hands[s];hand.palm.position.copy(hp[0]).lerp(hp[9],.55);hand.palm.quaternion.setFromUnitVectors(V([0,1,0]),hp[9].clone().sub(hp[0]).normalize());
   for(let f=0;f<5;f++)for(let j=0;j<4;j++){const k=f*4+j;fitSegment(hand.fingers[k],hp[j===0?0:1+f*4+j-1],hp[1+f*4+j],j===0?.008:.0055);}
   p[17+s]=hp[20].clone();p[19+s]=hp[8].clone();p[21+s]=hp[4].clone();this.grips[s===0?'Left':'Right']=hp[8].clone().add(hp[4]).multiplyScalar(.5).applyMatrix4(root.matrixWorld);
  }
  const b=frame.face.blendshapes;this.mouthOpen=b.jawOpen;this.mouth.scale.set(.025+.012*(b.mouthSmileLeft+b.mouthSmileRight),.003+.045*b.jawOpen,.008);this.lowerLip.position.y=-.086-.045*b.jawOpen;
  this.eyes.forEach((m,i)=>m.scale.y=.009*Math.max(.06,1-b[i?'eyeBlinkLeft':'eyeBlinkRight']));
  this.brows.forEach((m,i)=>{m.position.y=.033+.018*b.browInnerUp-.012*b[i?'browDownLeft':'browDownRight'];m.rotation.z=(i?1:-1)*(.1+.25*b.browInnerUp);});
  root.updateMatrixWorld(true);this.joints=p.map(v=>v.clone().applyMatrix4(root.matrixWorld));
  this.joints[0]=this.nose.getWorldPosition(new THREE.Vector3());this.joints[7]=this.ears[0].getWorldPosition(new THREE.Vector3());this.joints[8]=this.ears[1].getWorldPosition(new THREE.Vector3());
 }
}
