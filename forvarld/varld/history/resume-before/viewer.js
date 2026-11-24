import {initial,apply,timeline,sourceMap,describe,propId} from './edits.mjs';
import * as THREE from 'three';
const boot=performance.now(),$=id=>document.getElementById(id),url='/paket/notan/';
const M=await (await fetch(url+'manifest.json')).json();
let state=initial(M),edits=[],transactions=[],chatPending=null;
const baseRegi=await (await fetch('/pipeline/base-regi.json')).json();
const renderer=new THREE.WebGLRenderer({antialias:false,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(1);renderer.setSize(576,1024,false);renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
$('viewport').append(renderer.domElement);
const gl=renderer.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info');
const gpu=debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
const world=new THREE.Scene(),camera=new THREE.PerspectiveCamera(45,576/1024,.02,100),room=new THREE.Group();world.add(room);
world.background=new THREE.Color('#8b8d91');camera.up.set(0,0,1);
const commonVertex=`
uniform bool ps2; uniform vec2 resolution;uniform mat4 sourceVP;
varying vec3 vAffine; varying vec2 vUv; varying vec3 vWorld;varying vec4 vSource;
void finishVertex(vec4 p){
 vWorld=p.xyz;vSource=sourceVP*p;vec4 clip=projectionMatrix*viewMatrix*p;
 vUv=uv;vAffine=vec3(uv*clip.w,clip.w);
 if(ps2)clip.xy=floor(clip.xy/clip.w*resolution*.5+.5)/(resolution*.5)*clip.w;
 gl_Position=clip;
}`;
const fragment=`
precision highp float;
#include <packing>
uniform bool liveEnabled;uniform bool depthPass;uniform int liveMode;uniform sampler2D liveMap;uniform sampler2D liveAlpha;uniform sampler2D sourceDepth;uniform vec4 freezeMouth;
uniform sampler2D map; uniform bool textured; uniform bool ps2;uniform vec3 tint;uniform float lighting;uniform bool cutout;
uniform bool visibilityEnabled;uniform sampler2D visibilityMap;uniform vec2 maskTile;uniform float maskRows;uniform vec2 resolution;
varying vec3 vAffine; varying vec2 vUv; varying vec3 vWorld;varying vec4 vSource;
void main(){
 if(depthPass){gl_FragColor=packDepthToRGBA(gl_FragCoord.z);return;}
 if(visibilityEnabled){vec2 mu=(vec2(gl_FragCoord.x/resolution.x,1.-gl_FragCoord.y/resolution.y)+maskTile)/vec2(8.,maskRows);mu.y=1.-mu.y;if(texture2D(visibilityMap,mu).r<.5)discard;}
 vec2 t=ps2?vAffine.xy/vAffine.z:vUv;
 vec4 sampleColor=textured?texture2D(map,t):vec4(1.);
 if(liveEnabled&&liveMode>0){
  vec2 su=vSource.xy/vSource.w*.5+.5;bool inside=vSource.w>0.&&su.x>=0.&&su.x<=1.&&su.y>=0.&&su.y<=1.;
  vec2 mu=(vec2(su.x,1.-su.y)+maskTile)/vec2(8.,maskRows);mu.y=1.-mu.y;
  vec3 alpha=texture2D(liveAlpha,mu).rgb;
  bool frozen=freezeMouth.z>0.&&su.x>freezeMouth.x&&su.x<freezeMouth.x+freezeMouth.z&&su.y>freezeMouth.y&&su.y<freezeMouth.y+freezeMouth.w;
  if(liveMode>=2){float a=liveMode==2?alpha.r:liveMode==3?alpha.g:alpha.b;if(!inside||a<.5)discard;if(!frozen)sampleColor=texture2D(liveMap,su);}
  else if(inside&&!frozen){float dep=unpackRGBAToDepth(texture2D(sourceDepth,su));float z=-perspectiveDepthToViewZ(dep,.02,100.);if(texture2D(visibilityMap,mu).r>.5&&abs(z-vSource.w)<.025)sampleColor=texture2D(liveMap,su);}
 }
 if(cutout&&sampleColor.a<.5)discard;vec3 col=sampleColor.rgb;
 vec3 n=normalize(cross(dFdx(vWorld),dFdy(vWorld)));
 float light=mix(1.,.78+.22*abs(dot(n,normalize(vec3(.4,-.5,1.)))),lighting);
 gl_FragColor=vec4(col*tint*light,1.);
}`;
const allMaterials=[];
function material({texture=null,color='#ffffff',skin=false,palette=null,bones=127,cutout=false}={}){
 const mat=new THREE.ShaderMaterial({side:THREE.DoubleSide,uniforms:{liveEnabled:{value:false},liveMode:{value:0},depthPass:{value:false},sourceVP:{value:new THREE.Matrix4()},liveMap:{value:null},liveAlpha:{value:null},sourceDepth:{value:null},freezeMouth:{value:new THREE.Vector4()},ps2:{value:true},resolution:{value:new THREE.Vector2(192,342)},map:{value:texture},textured:{value:!!texture},cutout:{value:cutout},tint:{value:new THREE.Color(color)},lighting:{value:cutout?0:skin?.35:1},palette:{value:palette},boneCount:{value:bones},visibilityEnabled:{value:false},visibilityMap:{value:null},maskTile:{value:new THREE.Vector2()},maskRows:{value:1}},
 vertexShader:skin?`
 attribute vec4 joints;attribute vec4 weights;
 uniform sampler2D palette;uniform float boneCount;
 mat4 bone(float i){float y=(i+.5)/boneCount;return mat4(texture2D(palette,vec2(.125,y)),texture2D(palette,vec2(.375,y)),texture2D(palette,vec2(.625,y)),texture2D(palette,vec2(.875,y)));}
 ${commonVertex}
 void main(){mat4 s=bone(joints.x)*weights.x+bone(joints.y)*weights.y+bone(joints.z)*weights.z+bone(joints.w)*weights.w;finishVertex(s*vec4(position,1.));}`:
 `${commonVertex} void main(){finishVertex(modelMatrix*vec4(position,1.));}`,
 fragmentShader:fragment});allMaterials.push(mat);return mat;
}
const loader=new THREE.TextureLoader();
async function texture(file){const t=await loader.loadAsync(url+file);t.magFilter=t.minFilter=THREE.NearestFilter;t.generateMipmaps=false;t.colorSpace=THREE.NoColorSpace;return t;}
for(const o of M.room){
 const geo=o.typ==='cylinder'?new THREE.CylinderGeometry(.5,.5,1,12).rotateX(Math.PI/2):new THREE.BoxGeometry(1,1,1);
 if(o.top_slope){const p=geo.attributes.position;for(let i=0;i<p.count;i++)if(p.getZ(i)>0)p.setZ(i,p.getZ(i)+o.top_slope*p.getX(i)*o.matt_m[0]/o.matt_m[2]);p.needsUpdate=true;}
 const mesh=new THREE.Mesh(geo,material({color:o.farg}));mesh.position.fromArray(o.pos_m);mesh.rotation.set(...o.rotation_rad);mesh.scale.fromArray(o.matt_m);mesh.userData.interval=o.synlig_ut;mesh.userData.basePosition=o.pos_m;room.add(mesh);
}
const loaded=await Promise.all(M.scenes.map(async s=>{
 const m=s.person;const [buffer,tex,plate,visibility]=await Promise.all([fetch(url+m.stem+'.bin').then(r=>r.arrayBuffer()),texture(m.stem+'-texture.png'),texture(s.plate),texture(s.visibilityAtlas)]);
 let offset=0;const take=n=>{const a=new Float32Array(buffer,offset,n);offset+=n*4;return a;};const n=m.triangles*3;
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(take(n*3),3));geo.setAttribute('joints',new THREE.BufferAttribute(take(n*4),4));geo.setAttribute('weights',new THREE.BufferAttribute(take(n*4),4));geo.setAttribute('uv',new THREE.BufferAttribute(take(n*2),2));
 const palettes=take(m.frames*m.bones*16),data=new Float32Array(m.bones*16);
 const pal=new THREE.DataTexture(data,4,m.bones,THREE.RGBAFormat,THREE.FloatType);pal.magFilter=pal.minFilter=THREE.NearestFilter;pal.needsUpdate=true;
 const mesh=new THREE.Mesh(geo,material({skin:true,texture:tex,palette:pal,bones:m.bones}));mesh.frustumCulled=false;mesh.visible=false;world.add(mesh);
 mesh.material.uniforms.visibilityMap.value=visibility;mesh.material.uniforms.maskRows.value=s.visibilityRows;
 const cards={};
 if(s.layers)for(const name of ['head','foreground','nearForeground']){
  const spec=s.layers[name];if(!spec)continue;
  const tex=await texture(spec.texture),key=s.layers.camera,focal=key.lins_mm/36*576;
  const card=new THREE.Mesh(new THREE.PlaneGeometry(576/focal*spec.depth,1024/focal*spec.depth),material({texture:tex,cutout:true}));
  const C=new THREE.Matrix4().fromArray(key.matris.flat()).transpose();
  card.matrixAutoUpdate=false;card.matrix.copy(C).multiply(new THREE.Matrix4().makeTranslation(0,0,-spec.depth));card.userData.referenceMatrix=card.matrix.clone();
  if(name==='head'){card.userData.rest=new THREE.Matrix4().fromArray(spec.restMatrix.flat()).transpose();card.userData.referenceBoneInverse=new THREE.Matrix4().fromArray(spec.referenceBoneWorld.flat()).transpose().invert();}
  card.frustumCulled=false;card.visible=false;world.add(card);cards[name]=card;
 }
 const liveAlpha=s.live?await texture(s.live.atlas):null,patches=[];
 if(liveAlpha)for(let k=0;k<3;k++){const spec=k===0?s.layers.head:s.layers.foreground||s.layers.head;const card=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material({texture:await texture(spec.texture),cutout:true}));card.material.uniforms.liveMode.value=k+2;card.matrixAutoUpdate=false;card.visible=false;card.frustumCulled=false;world.add(card);patches.push(card);}
 const liveForeground=s.id==='s5'&&s.live?await texture('s5-foreground-live.png'):null;
 return {s,mesh,plate,pal,palettes,data,cards,liveAlpha,patches,liveForeground};
}));
const backdropTextures=new Map();
for(const b of M.backdrops||[]){const t=await loader.loadAsync(b.url);t.colorSpace=THREE.NoColorSpace;backdropTextures.set(b.id,t);}
for(const l of loaded)for(const card of Object.values(l.cards))card.material.userData.originalMap=card.material.uniforms.map.value;
const sourceDepthTarget=new THREE.WebGLRenderTarget(288,512,{minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter,depthBuffer:true});
const sourceCamera=camera.clone(),liveVideo=new THREE.VideoTexture($('source'));liveVideo.colorSpace=THREE.NoColorSpace;liveVideo.magFilter=liveVideo.minFilter=THREE.LinearFilter;
const backmat=new THREE.ShaderMaterial({side:THREE.DoubleSide,uniforms:{map:{value:null},fit:{value:new THREE.Vector4(.45,.8,.45,.84)}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'uniform sampler2D map;uniform vec4 fit;varying vec2 vUv;void main(){float y=(1.-vUv.y-fit.z)*(fit.y-fit.x)/(fit.w-fit.z)+fit.x;gl_FragColor=vec4(texture2D(map,vec2(vUv.x,clamp(1.-y,0.,1.))).rgb,1.);}'});
const backcard=new THREE.Mesh(new THREE.PlaneGeometry(1,1),backmat);backcard.matrixAutoUpdate=false;backcard.frustumCulled=false;backcard.visible=false;world.add(backcard);
const target=new THREE.WebGLRenderTarget(192,342,{minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter,depthBuffer:true});
const post=new THREE.Scene(),ortho=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const postmat=new THREE.ShaderMaterial({uniforms:{map:{value:target.texture},ps2:{value:true},size:{value:new THREE.Vector2(192,342)}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:`
 varying vec2 vUv;uniform sampler2D map;uniform bool ps2;uniform vec2 size;
 float bayer(vec2 p){int x=int(mod(p.x,4.)),y=int(mod(p.y,4.));int i=x+y*4;
 if(i==0)return 0.;if(i==1)return 8.;if(i==2)return 2.;if(i==3)return 10.;if(i==4)return 12.;if(i==5)return 4.;if(i==6)return 14.;if(i==7)return 6.;if(i==8)return 3.;if(i==9)return 11.;if(i==10)return 1.;if(i==11)return 9.;if(i==12)return 15.;if(i==13)return 7.;if(i==14)return 13.;return 5.;}
 void main(){vec3 c=texture2D(map,vUv).rgb;if(ps2){float d=(bayer(floor(vUv*size))+.5)/16.-.5;c=clamp(floor(c*31.+.5+d)/31.,0.,1.);}gl_FragColor=vec4(c,1.);}`});
post.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),postmat));
const textCanvas=document.createElement('canvas');textCanvas.width=576;textCanvas.height=1024;const ctx=textCanvas.getContext('2d');const textTex=new THREE.CanvasTexture(textCanvas);textTex.magFilter=textTex.minFilter=THREE.NearestFilter;textTex.colorSpace=THREE.NoColorSpace;
const overlay=new THREE.Scene(),textPlane=new THREE.Mesh(new THREE.PlaneGeometry(2,2),new THREE.MeshBasicMaterial({map:textTex,transparent:true,depthTest:false,depthWrite:false}));overlay.add(textPlane);
let frame=0,playing=false,playStart=0,playFrame=0,tripod=new Map(),tinted=false,textEdited=false,sourceFrames=Array.from({length:M.frames},(_,i)=>i),texts=M.text,active=null;
let textKey='',lastSize='',pending=[],measurements=[],frameTimes=[],rafTimes=[],lastRaf=0;
const audio=$('audio'),video=$('source');
function sourceFrame(f=frame){return sourceFrames[Math.max(0,Math.min(sourceFrames.length-1,Math.floor(f)))];}
function setCamera(key){camera.matrix.fromArray(key.matris.flat()).transpose();camera.matrix.decompose(camera.position,camera.quaternion,camera.scale);camera.fov=THREE.MathUtils.radToDeg(2*Math.atan(1024/576*M.cameras.sensor_bredd_mm/(2*key.lins_mm)));camera.updateProjectionMatrix();camera.updateMatrixWorld(true);}
function updateText(){
 const cur=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);const ts=(cur?.texts||[]).filter(t=>t.ut[0]<=sourceFrame()&&sourceFrame()<t.ut[1]);const key=ts.map(t=>t.id+':'+t.text).join('|')+textEdited;
 if(key===textKey)return;textKey=key;ctx.clearRect(0,0,576,1024);
 for(const t of ts){const style=t.stil,[x,y,w,h]=t.box;let lines=(textEdited&&t.scen==='s1'?'Vem bjuder på middag?':t.text).split('\n');
 ctx.font=`bold ${style.storlek_px}px Arial`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.fillStyle=style.farg;ctx.strokeStyle=style.kontur_farg;ctx.lineWidth=style.kontur_px*2;
 lines.forEach((line,i)=>{const yy=y+h/2+(i-(lines.length-1)/2)*style.storlek_px*1.05;ctx.strokeText(line,x+w/2,yy);ctx.fillText(line,x+w/2,yy);});}
 textTex.needsUpdate=true;
}
function draw(){
 const start=performance.now(),sf=sourceFrame(),l=loaded.find(l=>sf>=l.s.source[0]&&sf<l.s.source[1]);if(!l)return;active=l;
 const current=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);
 const local=sf-l.s.source[0],isTripod=tripod.has(current.id),ps2=$('ps2').checked,plate=$('plate').checked&&!isTripod&&!current.venue&&!Object.values(current.props).some(p=>p&&(!p.visible||p.asset.split(':')[0]!==current.origin));
 const w=ps2?192:576,h=ps2?342:1024,size=`${w}x${h}`;
 if(lastSize!==size){target.setSize(w,h);lastSize=size;postmat.uniforms.size.value.set(w,h);for(const mat of allMaterials)mat.uniforms.resolution.value.set(w,h);}
 for(const x of loaded){x.mesh.visible=x===l&&x.s.person.visible[local];for(const card of [...Object.values(x.cards),...x.patches])card.visible=false;}
 l.data.set(l.palettes.subarray(local*l.s.person.bones*16,(local+1)*l.s.person.bones*16));l.pal.needsUpdate=true;
 l.mesh.material.uniforms.visibilityEnabled.value=plate&&$('occlusion').checked;l.mesh.material.uniforms.maskTile.value.set(local%8,Math.floor(local/8));
 for(const x of loaded)x.mesh.material.uniforms.tint.value.set(state.cast[x.s.person.person]?.color||(tinted&&x.s.person.person==='A'?'#80a8ff':'#ffffff'));
 if(l.cards.head&&$('hair').checked){
  const spec=l.s.layers.head,current=new THREE.Matrix4().fromArray(l.data.slice(spec.bone*16,(spec.bone+1)*16)).multiply(l.cards.head.userData.rest);
  l.cards.head.matrix.copy(current).multiply(l.cards.head.userData.referenceBoneInverse).multiply(l.cards.head.userData.referenceMatrix);l.cards.head.matrixWorldNeedsUpdate=true;l.cards.head.visible=true;
  l.cards.head.material.uniforms.tint.value.copy(l.mesh.material.uniforms.tint.value);
 }
 if(l.cards.foreground&&!plate&&$('layers').checked&&current.props.foreground?.visible){l.cards.foreground.visible=true;}
 if(l.cards.nearForeground&&!plate&&$('layers').checked&&current.props.nearForeground?.visible){l.cards.nearForeground.visible=true;}
 for(const mat of allMaterials)mat.uniforms.ps2.value=ps2;
 postmat.uniforms.ps2.value=ps2;
 setCamera(M.cameras.nycklar[sf]);sourceCamera.copy(camera);sourceCamera.updateMatrixWorld(true);const sourceVP=new THREE.Matrix4().multiplyMatrices(sourceCamera.projectionMatrix,sourceCamera.matrixWorldInverse);
 const live=$('live').checked&&l.liveAlpha&&video.readyState>=2&&!video.seeking&&Math.abs(video.currentTime-sf/30)<.045;
 for(const mat of allMaterials){mat.uniforms.liveEnabled.value=!!live;mat.uniforms.sourceVP.value.copy(sourceVP);mat.uniforms.liveMap.value=liveVideo;mat.uniforms.liveAlpha.value=l.liveAlpha;mat.uniforms.sourceDepth.value=sourceDepthTarget.texture;mat.uniforms.freezeMouth.value.set(0,0,0,0);}
 l.mesh.material.uniforms.liveMode.value=1;
 const changedLine=M.lines.some(r=>state.lines[r.id]!=null&&r.start_s<=sf/30&&sf/30<r.slut_s&&r.talare===l.s.person.person);
 if(live){
  const C=sourceCamera.matrixWorld.clone(),focal=M.cameras.nycklar[sf].lins_mm/36*576;
  for(const [k,card] of l.patches.entries()){const d=l.s.live.depths[local][k];card.matrix.copy(C).multiply(new THREE.Matrix4().makeTranslation(0,0,-d)).multiply(new THREE.Matrix4().makeScale(576/focal*d,1024/focal*d,1));card.matrixWorldNeedsUpdate=true;card.visible=k===0?$('hair').checked:$('hands').checked&&(!current.props.foreground||current.props.foreground.visible);const u=card.material.uniforms;u.maskTile.value.set(local%8,Math.floor(local/8));u.maskRows.value=l.s.live.rows;u.tint.value.copy(l.mesh.material.uniforms.tint.value);}
  if(l.cards.head)l.cards.head.visible=false;
  if(changedLine){const [hx,hy]=l.s.live.headCenters[local];for(const mat of [l.mesh.material,l.patches[0].material])mat.uniforms.freezeMouth.value.set(hx-.14,1.-hy-.10,.28,.11);}
  // Render only the posed body from its original camera for source-view self occlusion.
  const visible=world.children.map(x=>x.visible),bg=world.background;for(const child of world.children)child.visible=child===l.mesh;
  const u=l.mesh.material.uniforms;u.depthPass.value=true;u.ps2.value=false;u.sourceDepth.value=null;const vis=u.visibilityEnabled.value;u.visibilityEnabled.value=false;world.background=null;renderer.setRenderTarget(sourceDepthTarget);renderer.setClearColor('#ffffff');renderer.clear();renderer.render(world,sourceCamera);u.sourceDepth.value=sourceDepthTarget.texture;u.depthPass.value=false;u.ps2.value=ps2;u.visibilityEnabled.value=vis;world.children.forEach((x,i)=>x.visible=visible[i]);world.background=bg;
 }
 setCamera(isTripod?tripod.get(current.id):M.cameras.nycklar[sf]);
 world.background=plate?l.plate:new THREE.Color('#8b8d91');room.visible=!plate&&!current.venue;
 backcard.visible=!!current.venue;if(current.venue){const b=M.backdrops.find(b=>b.id===current.venue),key=l.s.layers?.camera||M.cameras.nycklar[sf],d=(l.s.layers?.head?.depth||2)*2.8,focal=key.lins_mm/36*576;backcard.matrix.fromArray(key.matris.flat()).transpose().multiply(new THREE.Matrix4().makeTranslation(0,0,-d)).multiply(new THREE.Matrix4().makeScale(576/focal*d*1.15,1024/focal*d*1.15,1));backcard.matrixWorldNeedsUpdate=true;backmat.uniforms.map.value=backdropTextures.get(current.venue);backmat.uniforms.fit.value.set(b.horizon,b.floor,l.s.id==='s7'?.40:.45,l.s.id==='s7'?.62:.84);}
 for(const name of ['foreground','nearForeground'])if(l.cards[name]&&current.props[name]){const asset=current.props[name].asset.split(':');l.cards[name].material.uniforms.map.value=live&&name==='foreground'&&asset[0]==='s5'?l.liveForeground:loaded.find(x=>x.s.id===asset[0])?.cards[asset[1]]?.material.userData.originalMap||l.cards[name].material.userData.originalMap;}
 for(const [i,child] of room.children.entries()){const iv=child.userData.interval;child.visible=(!iv||(iv[0]<=sf&&sf<iv[1]))&&!(!plate&&$('layers').checked&&l.cards.foreground&&M.room[i].id.startsWith('bord_'));child.position.fromArray(l.s.roomAdjustments?.find(a=>a.objectIndex===i)?.position||child.userData.basePosition);}
 updateText();renderer.setRenderTarget(target);renderer.clear();renderer.render(world,camera);renderer.autoClear=false;renderer.clearDepth();renderer.render(overlay,ortho);renderer.autoClear=true;
 renderer.setRenderTarget(null);renderer.render(post,ortho);
 $('clock').textContent=`${(frame/30).toFixed(2)} / ${(sourceFrames.length/30).toFixed(2)} s · ${l.s.id}`;$('scrub').value=frame;
 $('viewLabel').textContent=`${ps2?'PS2 192×342':'Vanlig 576×1024'} · ${l.s.id} · ${plate?'medianplåt'+($('occlusion').checked?' + synlighetsmask':''):(isTripod?'ändrad kamera · ':'')+'mallrum'+($('layers').checked?' + förgrundskort':'')} · ${$('hair').checked?'huvudkort':'3D-huvud'}`;
 frameTimes.push(performance.now()-start);if(frameTimes.length>2000)frameTimes.shift();
 if(pending.length){gl.finish();const entries=pending.splice(0);const completed=performance.now();requestAnimationFrame(()=>{for(const p of entries){const result={edit:p.name,clickToSubmitMs:completed-p.start,clickToNextRafMs:performance.now()-p.start,outputFrame:frame,sourceFrame:sf,...p.extra};measurements.push(result);p.resolve?.(result);}status();});}
}
function status(){const med=arr=>[...arr].sort((a,b)=>a-b)[Math.floor(arr.length/2)]||0;
 $('status').textContent=`GPU: ${gpu}\nPaket klart: ${loadMs.toFixed(1)} ms · median JS+render-submit: ${med(frameTimes).toFixed(2)} ms\n`+measurements.map(m=>`${m.edit}: ${m.clickToNextRafMs.toFixed(1)} ms till nästa rAF efter ändrad render`).join('\n');}
function syncMedia(force=false){const time=sourceFrame()/30;const cur=timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]);audio.muted=!cur?.sound||M.lines.some(r=>state.lines[r.id]!=null&&r.start_s<=time&&time<r.slut_s);if(force||Math.abs(video.currentTime-time)>.12)video.currentTime=time;if(force||Math.abs(audio.currentTime-time)>.12)audio.currentTime=time;}
function seek(f){frame=Math.max(0,Math.min(sourceFrames.length-1,Math.round(f)));playFrame=frame;playStart=performance.now();syncMedia(true);draw();}
function pause(){playing=false;audio.pause();video.pause();}
function togglePlay(){if(playing)pause();else{if(frame>=sourceFrames.length-1)seek(0);playing=true;playFrame=frame;playStart=performance.now();syncMedia(true);audio.play().catch(()=>{});video.play().catch(()=>{});}}
function mark(name,start=performance.now(),extra={}){return new Promise(resolve=>{pending.push({name,start,extra,resolve});draw();});}
function tripodKey(l){
 const key=structuredClone(M.cameras.nycklar[Math.floor((l.s.source[0]+l.s.source[1])/2)]),mat=new THREE.Matrix4().fromArray(key.matris.flat()).transpose(),p=new THREE.Vector3(),q=new THREE.Quaternion(),scale=new THREE.Vector3();mat.decompose(p,q,scale);
 p.add(new THREE.Vector3(.12,0,-.08).applyQuaternion(q));mat.compose(p,q,scale);key.matris=Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>mat.elements[j*4+i]));return key;
}
function regi(){return {...baseRegi,skapad:new Date().toISOString(),edits:structuredClone(edits)};}
function rebuild(){sourceFrames=sourceMap(state);$('scrub').max=sourceFrames.length-1;frame=Math.min(frame,sourceFrames.length-1);tripod.clear();for(const s of state.scenes)if(s.camera?.lage==='stativ'){
 const l=loaded.find(l=>l.s.id===s.origin),key=tripodKey(l);if(s.camera.inramning==='nara')key.lins_mm*=1.12;if(s.camera.inramning==='hel')key.lins_mm*=.88;if(s.camera.fov_grader)key.lins_mm=1024/576*M.cameras.sensor_bredd_mm/(2*Math.tan(s.camera.fov_grader*Math.PI/360));tripod.set(s.id,key);
 }textKey='';$('editList').replaceChildren(...edits.map(e=>{const li=document.createElement('li');li.textContent=describe(e);return li;}));$('regiJson').textContent=JSON.stringify(regi(),null,2);$('undo').disabled=!transactions.length;localStorage.setItem('notan-regi-v5',JSON.stringify({edits,transactions}));syncMedia(true);}
async function event(data){await fetch('/api/event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});}
async function applyEdits(batch,{start=performance.now(),chatId=null}={}){
 pause();let next=state;for(const e of batch)next=apply(next,e,M);transactions.push({count:batch.length,chatId});edits.push(...structuredClone(batch));state=next;rebuild();
 const e=batch[0],scene=state.scenes.find(s=>s.id===e.scen||e.op==='casta'&&loaded.find(l=>l.s.id===s.origin).s.person.person===e.person||e.op==='byt_replik'&&M.lines.find(r=>r.id===e.replik)?.scen===s.origin);
 if(scene)frame=timeline(state).find(s=>s.id===scene.id).ut[0]+Math.floor((scene.b-scene.a)/2);syncMedia(true);
 const result=await mark('regi',start,{ops:batch.map(e=>e.op)});await event({type:'kept',chatId,edits:batch,timing:result});return result;
}
async function undo(){pause();const t=transactions.pop();if(!t)return;edits.splice(-t.count);state=initial(M);for(const e of edits)state=apply(state,e,M);rebuild();await mark('undo');await event({type:'undid',chatId:t.chatId});}
function say(text,who='world'){const row=document.createElement('div');row.className='message '+who;row.textContent=text;$('messages').append(row);row.scrollIntoView({block:'nearest'});return row;}
async function chat(sentence){const start=performance.now();say(sentence,'cm');$('send').disabled=true;
 try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sentence,edits,currentScene:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1])?.id,pending:chatPending})});const response=await r.json();if(!r.ok)throw Error(response.error||'Serverfel');chatPending=response.pending||null;
 const row=say(response.message);let applied=null;
 if(response.edits){applied=await applyEdits(response.edits,{start,chatId:response.id});row.textContent=response.message+` · ${Math.round(applied.clickToNextRafMs)} ms`;}
 if(response.choices){for(const choice of response.choices){const b=document.createElement('button');b.textContent=choice.label;b.onclick=async()=>{try{const result=await applyEdits(choice.edits,{chatId:response.id});row.replaceChildren(document.createTextNode(choice.label+` · ${Math.round(result.clickToNextRafMs)} ms`));await event({type:'picked',chatId:response.id,alternative:choice.id});}catch(e){say(e.message);}};row.append(b);}}
 window.__WORLD__.lastChat={sentence,response,applied,totalMs:applied?.clickToNextRafMs||performance.now()-start};return window.__WORLD__.lastChat;
 }catch(e){say(e.message);throw e;}finally{$('send').disabled=false;}}
async function edit(name){const common={id:crypto.randomUUID(),ursprung:{typ:'cm'}};if(name==='camera')return applyEdits([{...common,op:'renderkamera',scen:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]).id,kamera_id:common.id,lage:'stativ',inramning:'nara',mal:null}]);if(name==='text')return applyEdits([{...common,op:'skarmtext',scen:'s1',skarmtext_id:'st1',atgard:'byt',text:'Vem bjuder på middag?'}]);if(name==='tint')return applyEdits([{...common,op:'casta',person:'A',kundroll:{id:'A',namn:'kvinna'},utseende:{troja_farg:'#80a8ff'}}]);if(name==='pipeline')return applyEdits([{...common,op:'ta_bort_scen',scen:'s2'}]);}
$('play').onclick=togglePlay;$('scrub').oninput=e=>{pause();seek(Number(e.target.value));};
for(const name of ['tint','text','camera','pipeline'])$(name).onclick=()=>edit(name).catch(e=>say(e.message));
$('undo').onclick=undo;
$('reset').onclick=()=>{pause();edits=[];transactions=[];state=initial(M);frame=0;tripod.clear();tinted=false;textEdited=false;chatPending=null;rebuild();draw();event({type:'reset'});};
$('chatForm').onsubmit=e=>{e.preventDefault();const sentence=$('sentence').value.trim();if(sentence){$('sentence').value='';chat(sentence).catch(()=>{});}};
$('download').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(regi(),null,2)],{type:'application/json'}));a.download='regi.json';a.click();URL.revokeObjectURL(a.href);};
async function upload(file){if(!file)return;const r=await fetch('/api/backdrop?name='+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':file.type},body:file});const b=await r.json();if(!r.ok)throw Error(b.error);M.backdrops.push(b);const tex=await loader.loadAsync(b.url);tex.colorSpace=THREE.NoColorSpace;backdropTextures.set(b.id,tex);const row=say('Bilden är sparad lokalt som '+b.label+'.');const button=document.createElement('button');button.textContent='Använd i aktuell scen';button.onclick=()=>applyEdits([{id:crypto.randomUUID(),op:'byt_miljo',ursprung:{typ:'cm'},scen:timeline(state).find(s=>s.ut[0]<=frame&&frame<s.ut[1]).id,rum:{kalla:'upload',tillgang_id:b.id,ord:[],beskrivning:b.label}}]).catch(e=>say(e.message));row.append(button);}
$('upload').onchange=e=>upload(e.target.files[0]).catch(e=>say(e.message));$('chatPanel').ondragover=e=>e.preventDefault();$('chatPanel').ondrop=e=>{e.preventDefault();upload(e.dataTransfer.files[0]).catch(e=>say(e.message));};
for(const name of ['ps2','plate','occlusion','hair','layers','live','hands'])$(name).onchange=draw;$('side').onchange=()=>{$('sourceBox').hidden=!$('side').checked;};
const loadMs=performance.now()-boot;
try{const saved=JSON.parse(localStorage.getItem('notan-regi-v5'));if(saved){for(const e of saved.edits)state=apply(state,e,M);edits=saved.edits;transactions=saved.transactions;}}catch{state=initial(M);edits=[];transactions=[];}rebuild();
function tick(now){if(lastRaf)rafTimes.push(now-lastRaf);lastRaf=now;if(rafTimes.length>2000)rafTimes.shift();if(playing){frame=Math.min(sourceFrames.length-1,Math.floor(playFrame+(now-playStart)*.03));if(frame>=sourceFrames.length-1)pause();syncMedia();}draw();requestAnimationFrame(tick);}
window.__WORLD__={ready:true,applyEdits,undo,chat,regi,getState:()=>structuredClone(state),manifest:M,gpu,loadMs,renderer,measurements,frameTimes,rafTimes,edit,draw,pause,
 async seek(f,{plate=true,ps2=true,layers=false,hair=true,cameraChanged=false,live=true,hands=true}={}){pause();$('live').checked=live;$('hands').checked=hands;$('plate').checked=plate;$('ps2').checked=ps2;$('layers').checked=layers;$('hair').checked=hair;tripod.clear();seek(f);if(cameraChanged)tripod.set(active.s.id,tripodKey(active));if(video.readyState<2||Math.abs(video.currentTime-sourceFrame()/30)>.001)await new Promise(r=>{video.addEventListener('seeked',r,{once:true});setTimeout(r,2000);});draw();gl.finish();return{frame,sourceFrame:sourceFrame(),scene:active.s.id};},
 png:()=>renderer.domElement.toDataURL('image/png'),
 async benchmark(count=180){pause();const start=performance.now(),samples=[];for(let i=0;i<count;i++){const t=performance.now();seek(i%sourceFrames.length);gl.finish();samples.push(performance.now()-t);await new Promise(requestAnimationFrame);}const wall=performance.now()-start;const sorted=[...samples].sort((a,b)=>a-b);return {count,wallMs:wall,deliveredFps:count*1000/wall,renderFinishMedianMs:sorted[Math.floor(count*.5)],renderFinishP95Ms:sorted[Math.floor(count*.95)],gpu};},
 reset:()=>$('reset').click()};
seek(0);status();requestAnimationFrame(tick);
