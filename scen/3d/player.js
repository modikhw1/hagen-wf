import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {Character,makeObject,V,disposeGeometry} from './meshes.js';
import {createRigged} from './rigged.js';
import {applyCamera,placementAt,animateFrame,merge} from './scene_runtime.js';
import {XbotCharacter} from './avatar_xbot.js';
import {dumpPlayer} from './blender/dump.js'; // SCEN_BAKE_READ_ONLY
const $=id=>document.getElementById(id),params=new URLSearchParams(location.hash.slice(1));
const capture=params.has('capture');if(capture)document.body.classList.add('capture');if(params.has('textning'))document.body.classList.add('medtext');   // textning även i fångstläge (film)
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(576,1024,false);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;$('stage').prepend(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#c4cccd');
scene.add(new THREE.HemisphereLight('#fff6e5','#596b70',2.2));const light=new THREE.DirectionalLight('#fff4dd',3);light.position.set(-2,5,1);scene.add(light);const fill=new THREE.DirectionalLight('#d4e3ee',1);fill.position.set(3,3,4);scene.add(fill);
const camera=new THREE.PerspectiveCamera(68,576/1024,.025,80),sourceCamera=camera.clone();const controls=new OrbitControls(camera,renderer.domElement);controls.enabled=false;controls.enableDamping=false;
const world=new THREE.Group();scene.add(world);let spec,rawSpec,motion,tracks={},procedural={},rigged={},xbots={},mouthTracks={},objects={},revision=0,playing=false,t=Number(params.get('t')||0),lastTime=performance.now(),orbit=false,variant=params.get('avatar')||'procedural',mask=params.get('mode')==='mask',camOverride=params.get('cam'),lastShot,errors=[];
const audio=new Audio();audio.preload='auto';let audioOn=false,audioMode=params.get('ljud')||null;   // designed = designade röster + munkurvor (standard), original = källans ljud + MediaPipe-mun
const audioSrc=()=>audioMode==='original'||!spec.audioDesigned?spec.audio:spec.audioDesigned+(spec.audioVersion?'?v='+spec.audioVersion:'');
function disposeTree(root){root.traverse(o=>{if(o.isMesh&&!o.userData.shared){o.geometry?.dispose();}});}
async function rebuild(newSpec){
 if(!newSpec.actors?.length||!newSpec.shots?.length||!Array.isArray(newSpec.set)||!Array.isArray(newSpec.props))throw Error('Missing scene arrays');
 for(const o of [...newSpec.set,...newSpec.props])if(!o.id||!o.type||o.dims?.length!==3||o.transform?.position?.length!==3)throw Error('Invalid object '+o.id);
 for(const shot of newSpec.shots)if(!(shot.duration>0)||!shot.camera?.keyframes?.length)throw Error('Invalid shot '+shot.id);
 const nextTracks={...tracks};for(const a of newSpec.actors){const ref=a.motion.ref;if(!nextTracks[ref]){const response=await fetch(ref);if(!response.ok)throw Error('Motion not found: '+ref);nextTracks[ref]=await response.json();if(!nextTracks[ref].frames?.length)throw Error('Empty motion: '+ref);}}tracks=nextTracks;
 for(const a of newSpec.actors){const p=a.voice?.mouthTrack;if(p){try{const r=await fetch(p,{cache:'no-store'});if(r.ok)mouthTracks[p]=await r.json();}catch(e){}}}   // alltid om: op replik/casting gör om kurvorna
 spec=newSpec;for(const o of Object.values(objects))disposeGeometry(o);for(const c of Object.values(procedural))disposeGeometry(c.root);world.clear();objects={};procedural={};
 for(const o of [...spec.set,...spec.props]){const m=makeObject(o);objects[o.id]=m;world.add(m);}
 for(const a of spec.actors){const c=new Character(a);procedural[a.id]=c;world.add(c.root);if(rigged[a.id])world.add(rigged[a.id].root);}
 for(const a of spec.actors){if(xbots[a.id]&&xbots[a.id].nyckel!==XbotCharacter.nyckel(a))delete xbots[a.id];if(!xbots[a.id])xbots[a.id]=await XbotCharacter.create(a);xbots[a.id].spec=a;world.add(xbots[a.id].root);}
 // Background guest: untracked, neutral seated pose, deliberately excluded from actor metrics.
 const guestSpec=structuredClone(spec.actors.find(a=>a.id==='B'));guestSpec.id='guest';guestSpec.look.shirt='#b5a99c';guestSpec.look.hair='#6d5b46';guestSpec.transform={position:[.60,.60,1.44],yaw:90};const guest=new Character(guestSpec);procedural.guest=guest;world.add(guest.root);
 if(!xbots.guest)xbots.guest=await XbotCharacter.create(guestSpec);xbots.guest.spec=guestSpec;world.add(xbots.guest.root);   // gästen är också en neutral docka (ingen likhet)
 audioMode=audioMode||spec.audioMode||'designed';$('ljud').value=audioMode;if(!audio.src.endsWith(audioSrc())){const tid=audio.currentTime;audio.src=audioSrc();audio.currentTime=tid;if(playing&&audioOn)audio.play().catch(()=>{});}$('shot').innerHTML='<option value="">Kameraklipp</option>'+spec.shots.map(s=>`<option>${s.id}</option>`).join('');$('timeline').max=spec.shots.reduce((a,s)=>a+s.duration,0);revision++;render();
}
function shotAt(time){let start=0;for(const s of spec.shots){if(time<start+s.duration-1e-7)return {shot:s,start};start+=s.duration;}return {shot:spec.shots.at(-1),start:start-spec.shots.at(-1).duration};}
// Kamera: nyckelbilder + ev. orbit (scene_runtime). Källkamera: den kamera rörelsen MÄTTES med, oberoende av redigerad bildkamera.
function setCamera(cam,shot,time){return applyCamera(cam,shot,time);}
function sourceCameraFor(frame){
 // shot.source.camera = fryst kopia av originaltagningens kamera (op.py normalisera); fall tillbaka på tagningen med samma id
 const owner=spec.shots.find(s=>(s.source.shotId||s.id)===frame.shot&&s.source.camera)||spec.shots.find(s=>s.id===frame.shot);
 const cam=new THREE.PerspectiveCamera(68,576/1024,.025,80);
 if(owner?.source.camera){const k=owner.source.camera;cam.position.fromArray(k.pos);cam.up.fromArray(k.up||[0,1,0]);cam.lookAt(V(k.target));cam.fov=k.fov;cam.updateProjectionMatrix();cam.updateMatrixWorld(true);}
 else if(owner)setCamera(cam,owner,0);
 return cam;
}
// Aktörens bildruta: helst samma källtid; saknas aktören där (t.ex. tillagd i en annan tagning) loopas aktörens egen tagning.
function frameFor(track,actorId,sourceT,local,entry){
 let f=track.frames[Math.min(track.frames.length-1,Math.floor(sourceT*(track.fps||30)+1e-5))];
 if(f&&f.actor===actorId&&!entry?.motion?.fromShot)return f;
 const own=track.frames.filter(x=>x.actor===actorId&&(!entry?.motion?.fromShot||x.shot===entry.motion.fromShot));
 return own.length?own[Math.floor(local*(track.fps||30))%own.length]:null;
}
// tagningens tidskarta: lokal tid -> källtid. op.py langd (replik) skriver source.knots; annars linjärt över [inSec, outSec].
function srcAt(shot,local){const k=shot.source.knots;if(!k?.length)return shot.source.inSec+local/shot.duration*(shot.source.outSec-shot.source.inSec);if(local<=k[0][0])return k[0][1];for(let i=1;i<k.length;i++)if(local<=k[i][0]){const [l0,s0]=k[i-1],[l1,s1]=k[i];return s0+(local-l0)/Math.max(1e-6,l1-l0)*(s1-s0);}return k[k.length-1][1];}
function rateAt(shot,local){const k=shot.source.knots;if(!k?.length)return (shot.audioRange[1]-shot.audioRange[0])/shot.duration;for(let i=1;i<k.length;i++)if(local<=k[i][0])return (k[i][1]-k[i-1][1])/Math.max(1e-6,k[i][0]-k[i-1][0]);return 1;}
const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function render(){
 if(!spec||!motion)return;
 const current=shotAt(t),shot=current.shot,local=t-current.start;const sourceT=srcAt(shot,local),index=Math.min(motion.frames.length-1,Math.max(0,Math.floor(sourceT*30+1e-5))),frame=motion.frames[index];
 const srcCam=sourceCameraFor(frame);sourceCamera.position.copy(srcCam.position);sourceCamera.quaternion.copy(srcCam.quaternion);sourceCamera.fov=srcCam.fov;sourceCamera.updateProjectionMatrix();sourceCamera.updateMatrixWorld(true);
 const viewShot=spec.shots.find(s=>s.id===camOverride)||shot;const target=setCamera(sourceCamera.clone(),viewShot,local);
 if(!orbit){setCamera(camera,viewShot,local);controls.target.copy(target);}
 for(const [id,c] of Object.entries(procedural))c.root.visible=false;for(const c of Object.values(rigged))c.root.visible=false;for(const c of Object.values(xbots))c.root.visible=false;
 const active={};
 for(const entry of shot.actors){
  const a=spec.actors.find(a=>a.id===entry.id);if(!a)continue;const track=tracks[a.motion.ref]||motion,trackActor=a.motion.actor||a.id;
  const raw=frameFor(track,trackActor,sourceT,local,entry);if(!raw)continue;
  // intensitet, spegling, humör och handankare per tagning (entry.motion överstyr aktörens motion)
  const f=animateFrame(raw,track,merge(a.motion,entry.motion));
  const placement=placementAt(a,entry,local);const mm=merge(a.motion,entry.motion);
  if(mm.lookAt){const L=mm.lookAt,r=L.ramp||[0,.35],k=THREE.MathUtils.clamp((local-r[0])/Math.max(1e-3,r[1]-r[0]),0,1);placement.lookAt={target:L.target,amount:(L.amount??.85)*k*k*(3-2*k)};}   // titta mot: bara huvudet
  const cam=raw.shot===frame.shot?sourceCamera:sourceCameraFor(raw);
  // munkurva från designad röst (actor.voice.mouthTrack) ersätter MediaPipes käke när den finns
  if(shot.tyst){f.face={...f.face,blendshapes:{...f.face.blendshapes,jawOpen:0}};}
  const mt=!shot.tyst&&audioMode!=='original'&&a.voice?.mouthTrack&&mouthTracks[a.voice.mouthTrack];if(mt){const k=Math.min(mt.values.length-1,Math.max(0,Math.floor((mt.time==='scene'?t:sourceT)*mt.fps)));f.face={...f.face,blendshapes:{...f.face.blendshapes,jawOpen:mt.values[k]}};}
  const c=variant==='vrm'&&rigged[a.id]?rigged[a.id]:variant==='xbot'&&xbots[a.id]?xbots[a.id]:procedural[a.id];c.spec=a;c.update(f,cam,placement);c.root.visible=true;active[a.id]=c;
 }
 const guest=variant==='xbot'&&xbots.guest?xbots.guest:procedural.guest;if(shot.id==='S4'){const f=motion.frames[93];guest.update(f,sourceCamera,guest.spec.transform);guest.root.visible=true;}
 for(const p of spec.props){const o={...p,...(shot.propOverrides[p.id]||{})},m=objects[p.id];m.visible=o.visible!==false;m.position.fromArray(o.transform.position);m.rotation.set(0,THREE.MathUtils.degToRad(o.transform.yaw||0),0);if(o.attach){const c=active[o.attach.actor];m.visible=!!c&&o.visible!==false;if(c?.joints[o.attach.joint]){m.position.copy(c.grips?.[o.attach.hand]||c.joints[o.attach.joint]);m.position.add(V(o.attach.offset||[0,0,0]).applyQuaternion(c.root.quaternion));m.quaternion.copy(c.root.quaternion);if(o.attach.rotation)m.quaternion.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...o.attach.rotation.map(THREE.MathUtils.degToRad))));}}}
 scene.updateMatrixWorld(true);
 const restore=[],background=scene.background,tonemap=renderer.toneMapping;
 if(mask){scene.background=new THREE.Color(0);renderer.toneMapping=THREE.NoToneMapping;world.traverse(o=>{if(o.isMesh){let p=o,isActor=false;while(p){if(p.userData.actor===frame.actor){isActor=true;break;}p=p.parent;}restore.push([o,o.material]);o.material=new THREE.MeshBasicMaterial({color:isActor?0xffffff:0,side:THREE.DoubleSide});}});}
 renderer.render(scene,camera);for(const [m,material]of restore){m.material.dispose();m.material=material;}scene.background=background;renderer.toneMapping=tonemap;
 const c=active[frame.actor],project=p=>p?(()=>{const q=p.clone().project(camera);return [(q.x+1)*288,(1-q.y)*512,q.z];})():null;
 // textning/teleprompter: repliken med ordtider; sagda ord framhävs (raden står kvar 0,35 s efter sista ordet)
 const line=shot.tyst?null:spec.dialogue.filter(d=>sourceT>=d.start-.1&&sourceT<d.end+.35).sort((x,y)=>y.start-x.start)[0],cap=$('caption');   // senast påbörjade repliken vinner
 const roll=spec.actors.find(a=>a.id===line?.speaker)?.casting?.role;
 if($('captions').checked&&line){cap.innerHTML=(roll?`<b class="roll">${esc(roll)}</b> `:'')+(line.words?.length?line.words.map(w=>`<span class="${sourceT>=w.start?'sagt':'osagt'}">${esc(w.w)}</span>`).join(' '):esc(line.text));cap.dataset.speaker=line.speaker;cap.style.display='';}else{cap.textContent='';cap.style.display='none';}
 $('timeline').value=t;$('time').textContent=`${t.toFixed(2)} s / ${Number($('timeline').max).toFixed(2)} s`;$('status').textContent=`${shot.id} | ${shot.beat}\n${variant} | frame ${index}\nJSON revision ${revision} | ${camera.fov.toFixed(1)} deg`;
 const audioTime=shot.source.knots?.length?sourceT:shot.audioRange[0]+local/shot.duration*(shot.audioRange[1]-shot.audioRange[0]);audio.volume=shot.tyst?0:1;if(playing&&audioOn){audio.preservesPitch=true;audio.playbackRate=Math.min(4,Math.max(.25,rateAt(shot,local)));if(Math.abs(audio.currentTime-audioTime)>.12)audio.currentTime=audioTime;}
 window.__frame={t,sourceT,audioTime,audioMode,caption:{text:cap.style.display==='none'?'':cap.textContent,sagda:cap.querySelectorAll('.sagt').length,talare:line?.speaker||null},mouthByActor:Object.fromEntries(Object.entries(active).map(([id,c])=>[id,c.mouthOpen])),index,shot:shot.id,variant,mask,revision,joints:c?.joints.map(project),mouthOpen:c?.mouthOpen,mouthAperture_m:c?.mouth?c.mouth.scale.y*2:null,triangles:renderer.info.render.triangles,mem:{js:performance.memory?.usedJSHeapSize,geo:renderer.info.memory.geometries,tex:renderer.info.memory.textures,prog:renderer.info.programs?.length},calls:renderer.info.render.calls,objects:Object.fromEntries(Object.entries(objects).map(([id,o])=>[id,{visible:o.visible,position:o.position.toArray(),uv:project(o.position)}])),camera:{pos:camera.position.toArray(),quaternion:camera.quaternion.toArray()},errors};lastShot=shot.id;
 return window.__frame;
}
async function loadVRM(){if(Object.keys(rigged).length)return;for(const a of spec.actors){const mid=motion.frames.find(f=>f.actor===a.id);const c=await createRigged(a,mid);rigged[a.id]=c;world.add(c.root);}render();}
function catalog(){
 const s=new THREE.Scene();s.background=new THREE.Color('#d7d2c8');s.add(new THREE.HemisphereLight('#fff6e5','#75828b',3));const l=new THREE.DirectionalLight('#ffffff',3);l.position.set(-2,4,5);s.add(l);
 const types=['paper_cup','drink_can','burger','pizza_slice','fries_box','tray','sauce_cup','card_terminal','fry'],dims=[[.3,.5,.3],[.22,.55,.22],[.58,.3,.58],[.55,.1,.6],[.4,.4,.35],[.6,.04,.4],[.3,.15,.3],[.25,.07,.4],[.035,.45,.035]];
 const c=new THREE.OrthographicCamera(-1.35,1.35,2.4,-2.4,.1,20);c.position.set(.7,2.2,6);c.lookAt(0,0,0);c.updateMatrixWorld(true);const labels=[];
 types.forEach((type,i)=>{const o=makeObject({id:type,type,dims:dims[i],transform:{position:[(i%3-1)*.85,1.25-Math.floor(i/3)*1.1,0],yaw:-15}});s.add(o);const p=o.position.clone().add(V([0,-.4,0])).project(c);labels.push({type,uv:[(p.x+1)*288,(1-p.y)*512]});});renderer.render(s,c);disposeGeometry(s);return {catalog:true,labels};
}
async function setFrame(time,options={}){playing=false;audio.pause();t=time;window.__VRM_RETARGET=options.rigMode||'unmirror';if(options.variant==='vrm')await loadVRM();variant=options.variant||variant;mask=options.mask??mask;camOverride=options.cam??camOverride;if(options.orbit){orbit=true;camera.position.fromArray(options.orbit.pos);camera.up.set(0,1,0);camera.lookAt(V(options.orbit.target));controls.target.copy(V(options.orbit.target));}else orbit=false;controls.enabled=orbit;return render();}
window.__SCEN3D__={dump:options=>dumpPlayer({xbots,objects,camera,spec,shotAt},options),setFrame,render,loadVRM,catalog,getSpec:()=>structuredClone(spec),getMotion:()=>motion,audioState:()=>({time:audio.currentTime,paused:audio.paused,rate:audio.playbackRate,ready:audio.readyState}),ready:false};
window.addEventListener('error',e=>errors.push(e.message));window.addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
try{rawSpec=await (await fetch('./scen3d.json',{cache:'no-store'})).text();motion=await(await fetch('./data/motion-2.json')).json();tracks['data/motion-2.json']=motion;await rebuild(JSON.parse(rawSpec));variant=params.get('avatar')||spec.defaultAvatar||'procedural';if(variant==='vrm')await loadVRM();render();window.__SCEN3D__.ready=true;}catch(e){errors.push(e.stack);$('status').textContent=e.stack;throw e;}
setInterval(async()=>{try{const text=await(await fetch('./scen3d.json',{cache:'no-store'})).text();if(text!==rawSpec){const next=JSON.parse(text);if(!next.actors||!next.shots?.length||!next.set)throw Error('Invalid scene schema');await rebuild(next);rawSpec=text;}}catch(e){$('status').textContent='JSON reload: '+e.message;}},1000);
$('play').onclick=()=>{playing=!playing;if(playing&&t>=Number($('timeline').max)-.03)t=0;$('play').textContent=playing?'Pausa':'Spela';if(playing&&audioOn){audio.currentTime=window.__frame.audioTime;audio.play().catch(e=>errors.push(e.message));}else audio.pause();};
$('timeline').oninput=e=>{t=Number(e.target.value);const c=shotAt(t);audio.currentTime=srcAt(c.shot,t-c.start);render();};
$('orbit').onclick=()=>{orbit=!orbit;controls.enabled=orbit;$('orbit').classList.toggle('active',orbit);render();};controls.addEventListener('change',()=>render());
$('shot').onchange=e=>{camOverride=e.target.value||null;render();};$('avatar').onchange=async e=>{if(e.target.value==='vrm')await loadVRM();variant=e.target.value;render();};$('audio').onchange=e=>{audioOn=e.target.checked;if(audioOn&&playing){audio.currentTime=window.__frame.audioTime;audio.play();}else audio.pause();};$('captions').onchange=render;$('ljud').onchange=e=>{audioMode=e.target.value;const tid=audio.currentTime;audio.src=audioSrc();audio.currentTime=tid;if(playing&&audioOn)audio.play();render();};
window.addEventListener('hashchange',()=>{const p=new URLSearchParams(location.hash.slice(1));setFrame(Number(p.get('t')||0),{mask:p.get('mode')==='mask',cam:p.get('cam')||null,variant:p.get('avatar')||variant});});
function tick(now){const dt=Math.min(.1,(now-lastTime)/1000);lastTime=now;if(playing){t+=dt;if(t>=Number($('timeline').max)){t=Number($('timeline').max)-1/30;playing=false;audio.pause();$('play').textContent='Spela';}render();}requestAnimationFrame(tick);}requestAnimationFrame(tick);
