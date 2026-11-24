import * as THREE from 'three';
const boot=performance.now(),$=id=>document.getElementById(id),url='/paket/notan/';
const M=await (await fetch(url+'manifest.json')).json();
const renderer=new THREE.WebGLRenderer({antialias:false,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(1);renderer.setSize(576,1024,false);renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
$('viewport').append(renderer.domElement);
const gl=renderer.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info');
const gpu=debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
const world=new THREE.Scene(),camera=new THREE.PerspectiveCamera(45,576/1024,.02,100),room=new THREE.Group();world.add(room);
world.background=new THREE.Color('#8b8d91');camera.up.set(0,0,1);
const commonVertex=`
uniform bool ps2; uniform vec2 resolution;
varying vec3 vAffine; varying vec2 vUv; varying vec3 vWorld;
void finishVertex(vec4 p){
 vWorld=p.xyz;vec4 clip=projectionMatrix*viewMatrix*p;
 vUv=uv;vAffine=vec3(uv*clip.w,clip.w);
 if(ps2)clip.xy=floor(clip.xy/clip.w*resolution*.5+.5)/(resolution*.5)*clip.w;
 gl_Position=clip;
}`;
const fragment=`
precision highp float;
uniform sampler2D map; uniform bool textured; uniform bool ps2;uniform vec3 tint;uniform float lighting;
uniform bool visibilityEnabled;uniform sampler2D visibilityMap;uniform vec2 maskTile;uniform float maskRows;uniform vec2 resolution;
varying vec3 vAffine; varying vec2 vUv; varying vec3 vWorld;
void main(){
 if(visibilityEnabled){vec2 mu=(vec2(gl_FragCoord.x/resolution.x,1.-gl_FragCoord.y/resolution.y)+maskTile)/vec2(8.,maskRows);mu.y=1.-mu.y;if(texture2D(visibilityMap,mu).r<.5)discard;}
 vec2 t=ps2?vAffine.xy/vAffine.z:vUv;
 vec3 col=textured?texture2D(map,t).rgb:vec3(1.);
 vec3 n=normalize(cross(dFdx(vWorld),dFdy(vWorld)));
 float light=mix(1.,.78+.22*abs(dot(n,normalize(vec3(.4,-.5,1.)))),lighting);
 gl_FragColor=vec4(col*tint*light,1.);
}`;
const allMaterials=[];
function material({texture=null,color='#ffffff',skin=false,palette=null,bones=127}={}){
 const mat=new THREE.ShaderMaterial({side:THREE.DoubleSide,uniforms:{ps2:{value:true},resolution:{value:new THREE.Vector2(192,342)},map:{value:texture},textured:{value:!!texture},tint:{value:new THREE.Color(color)},lighting:{value:skin?.35:1},palette:{value:palette},boneCount:{value:bones},visibilityEnabled:{value:false},visibilityMap:{value:null},maskTile:{value:new THREE.Vector2()},maskRows:{value:1}},
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
 const mesh=new THREE.Mesh(geo,material({color:o.farg}));mesh.position.fromArray(o.pos_m);mesh.rotation.set(...o.rotation_rad);mesh.scale.fromArray(o.matt_m);mesh.userData.interval=o.synlig_ut;room.add(mesh);
}
const loaded=await Promise.all(M.scenes.map(async s=>{
 const m=s.person;const [buffer,tex,plate,visibility]=await Promise.all([fetch(url+m.stem+'.bin').then(r=>r.arrayBuffer()),texture(m.stem+'-texture.png'),texture(s.plate),texture(s.visibilityAtlas)]);
 let offset=0;const take=n=>{const a=new Float32Array(buffer,offset,n);offset+=n*4;return a;};const n=m.triangles*3;
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(take(n*3),3));geo.setAttribute('joints',new THREE.BufferAttribute(take(n*4),4));geo.setAttribute('weights',new THREE.BufferAttribute(take(n*4),4));geo.setAttribute('uv',new THREE.BufferAttribute(take(n*2),2));
 const palettes=take(m.frames*m.bones*16),data=new Float32Array(m.bones*16);
 const pal=new THREE.DataTexture(data,4,m.bones,THREE.RGBAFormat,THREE.FloatType);pal.magFilter=pal.minFilter=THREE.NearestFilter;pal.needsUpdate=true;
 const mesh=new THREE.Mesh(geo,material({skin:true,texture:tex,palette:pal,bones:m.bones}));mesh.frustumCulled=false;mesh.visible=false;world.add(mesh);
 mesh.material.uniforms.visibilityMap.value=visibility;mesh.material.uniforms.maskRows.value=s.visibilityRows;
 return {s,mesh,plate,pal,palettes,data};
}));
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
 const ts=texts.filter(t=>t.ut[0]<=frame&&frame<t.ut[1]);const key=ts.map(t=>t.id+':'+t.text).join('|')+textEdited;
 if(key===textKey)return;textKey=key;ctx.clearRect(0,0,576,1024);
 for(const t of ts){const style=t.stil,[x,y,w,h]=t.box;let lines=(textEdited&&t.scen==='s1'?'Vem bjuder på middag?':t.text).split('\n');
 ctx.font=`bold ${style.storlek_px}px Arial`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.fillStyle=style.farg;ctx.strokeStyle=style.kontur_farg;ctx.lineWidth=style.kontur_px*2;
 lines.forEach((line,i)=>{const yy=y+h/2+(i-(lines.length-1)/2)*style.storlek_px*1.05;ctx.strokeText(line,x+w/2,yy);ctx.fillText(line,x+w/2,yy);});}
 textTex.needsUpdate=true;
}
function draw(){
 const start=performance.now(),sf=sourceFrame(),l=loaded.find(l=>sf>=l.s.source[0]&&sf<l.s.source[1]);if(!l)return;active=l;
 const local=sf-l.s.source[0],isTripod=tripod.has(l.s.id),ps2=$('ps2').checked,plate=$('plate').checked&&!isTripod;
 const w=ps2?192:576,h=ps2?342:1024,size=`${w}x${h}`;
 if(lastSize!==size){target.setSize(w,h);lastSize=size;postmat.uniforms.size.value.set(w,h);for(const mat of allMaterials)mat.uniforms.resolution.value.set(w,h);}
 for(const x of loaded)x.mesh.visible=x===l&&x.s.person.visible[local];
 l.data.set(l.palettes.subarray(local*l.s.person.bones*16,(local+1)*l.s.person.bones*16));l.pal.needsUpdate=true;
 l.mesh.material.uniforms.visibilityEnabled.value=plate&&$('occlusion').checked;l.mesh.material.uniforms.maskTile.value.set(local%8,Math.floor(local/8));
 for(const x of loaded)x.mesh.material.uniforms.tint.value.set(tinted&&x.s.person.person==='A'?'#80a8ff':'#ffffff');
 for(const mat of allMaterials)mat.uniforms.ps2.value=ps2;
 postmat.uniforms.ps2.value=ps2;
 setCamera(isTripod?tripod.get(l.s.id):M.cameras.nycklar[sf]);
 world.background=plate?l.plate:new THREE.Color('#8b8d91');room.visible=!plate;
 for(const child of room.children){const iv=child.userData.interval;child.visible=!iv||(iv[0]<=sf&&sf<iv[1]);}
 updateText();renderer.setRenderTarget(target);renderer.clear();renderer.render(world,camera);renderer.autoClear=false;renderer.clearDepth();renderer.render(overlay,ortho);renderer.autoClear=true;
 renderer.setRenderTarget(null);renderer.render(post,ortho);
 $('clock').textContent=`${(frame/30).toFixed(2)} / ${(sourceFrames.length/30).toFixed(2)} s · ${l.s.id}`;$('scrub').value=frame;
 $('viewLabel').textContent=`${ps2?'PS2 192×342':'Vanlig 576×1024'} · ${l.s.id} · ${plate?'medianplåt'+($('occlusion').checked?' + synlighetsmask':''):isTripod?'mallrum (kameran ändrad)':'möblerat mallrum'}`;
 frameTimes.push(performance.now()-start);if(frameTimes.length>2000)frameTimes.shift();
 if(pending.length){gl.finish();const entries=pending.splice(0);const completed=performance.now();requestAnimationFrame(()=>{for(const p of entries){const result={edit:p.name,clickToSubmitMs:completed-p.start,clickToNextRafMs:performance.now()-p.start,outputFrame:frame,sourceFrame:sf,...p.extra};measurements.push(result);p.resolve?.(result);}status();});}
}
function status(){const med=arr=>[...arr].sort((a,b)=>a-b)[Math.floor(arr.length/2)]||0;
 $('status').textContent=`GPU: ${gpu}\nPaket klart: ${loadMs.toFixed(1)} ms · median JS+render-submit: ${med(frameTimes).toFixed(2)} ms\n`+measurements.map(m=>`${m.edit}: ${m.clickToNextRafMs.toFixed(1)} ms till nästa rAF efter ändrad render`).join('\n');}
function syncMedia(force=false){const time=sourceFrame()/30;if(force||Math.abs(video.currentTime-time)>.12)video.currentTime=time;if(force||Math.abs(audio.currentTime-time)>.12)audio.currentTime=time;}
function seek(f){frame=Math.max(0,Math.min(sourceFrames.length-1,Math.round(f)));playFrame=frame;playStart=performance.now();syncMedia(true);draw();}
function pause(){playing=false;audio.pause();video.pause();}
function togglePlay(){if(playing)pause();else{if(frame>=sourceFrames.length-1)seek(0);playing=true;playFrame=frame;playStart=performance.now();syncMedia(true);audio.play().catch(()=>{});video.play().catch(()=>{});}}
function mark(name,start=performance.now(),extra={}){return new Promise(resolve=>{pending.push({name,start,extra,resolve});draw();});}
async function edit(name){const start=performance.now();
 if(name==='tint'){tinted=!tinted;if(active.s.person.person!=='A')seek(sourceFrames.indexOf(25));}
 if(name==='text'){textEdited=!textEdited;seek(sourceFrames.indexOf(25));}
 if(name==='camera'){
  const id=active.s.id;if(tripod.has(id))tripod.delete(id);else{
   const key=structuredClone(M.cameras.nycklar[Math.floor((active.s.source[0]+active.s.source[1])/2)]),mat=new THREE.Matrix4().fromArray(key.matris.flat()).transpose(),p=new THREE.Vector3(),q=new THREE.Quaternion(),scale=new THREE.Vector3();mat.decompose(p,q,scale);
   p.add(new THREE.Vector3(.55,0,.25).applyQuaternion(q));mat.compose(p,q,scale);key.matris=Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>mat.elements[j*4+i]));key.lins_mm*=.85;tripod.set(id,key);
  }
 }
 if(name==='pipeline'){
  pause();$('pipeline').disabled=true;
  try{const r=await fetch('/api/regi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:'remove-s2',op:'ta_bort_scen',ursprung:{typ:'cm'},scen:'s2'})});if(!r.ok)throw Error(await r.text());const result=await r.json();if(result.rejected.length)throw Error(JSON.stringify(result.rejected));sourceFrames=result.sourceFrames;texts=result.text;frame=sourceFrames.indexOf(114);if(frame<0)frame=0;$('scrub').max=sourceFrames.length-1;syncMedia(true);return await mark(name,start,{compileAndIoMs:result.compileAndIoMs,frames:sourceFrames.length});}
  finally{$('pipeline').disabled=false;}
 }
 return await mark(name,start);
}
$('play').onclick=togglePlay;$('scrub').oninput=e=>{pause();seek(Number(e.target.value));};
for(const name of ['tint','text','camera','pipeline'])$(name).onclick=()=>edit(name).catch(e=>{$('status').textContent=String(e);console.error(e);});
$('reset').onclick=()=>{pause();tripod.clear();tinted=false;textEdited=false;sourceFrames=Array.from({length:M.frames},(_,i)=>i);texts=M.text;$('scrub').max=M.frames-1;seek(0);};
for(const name of ['ps2','plate','occlusion'])$(name).onchange=draw;$('side').onchange=()=>{$('sourceBox').hidden=!$('side').checked;};
const loadMs=performance.now()-boot;
function tick(now){if(lastRaf)rafTimes.push(now-lastRaf);lastRaf=now;if(rafTimes.length>2000)rafTimes.shift();if(playing){frame=Math.min(sourceFrames.length-1,Math.floor(playFrame+(now-playStart)*.03));if(frame>=sourceFrames.length-1)pause();syncMedia();}draw();requestAnimationFrame(tick);}
window.__WORLD__={ready:true,manifest:M,gpu,loadMs,renderer,measurements,frameTimes,rafTimes,edit,draw,pause,
 async seek(f,{plate=true,ps2=true}={}){pause();$('plate').checked=plate;$('ps2').checked=ps2;seek(f);if(video.readyState<2||Math.abs(video.currentTime-sourceFrame()/30)>.001)await new Promise(r=>{video.addEventListener('seeked',r,{once:true});setTimeout(r,2000);});draw();gl.finish();return{frame,sourceFrame:sourceFrame(),scene:active.s.id};},
 png:()=>renderer.domElement.toDataURL('image/png'),
 async benchmark(count=180){pause();const start=performance.now(),samples=[];for(let i=0;i<count;i++){const t=performance.now();seek(i%sourceFrames.length);gl.finish();samples.push(performance.now()-t);await new Promise(requestAnimationFrame);}const wall=performance.now()-start;const sorted=[...samples].sort((a,b)=>a-b);return {count,wallMs:wall,deliveredFps:count*1000/wall,renderFinishMedianMs:sorted[Math.floor(count*.5)],renderFinishP95Ms:sorted[Math.floor(count*.95)],gpu};},
 reset:()=>$('reset').click()};
seek(0);status();requestAnimationFrame(tick);
