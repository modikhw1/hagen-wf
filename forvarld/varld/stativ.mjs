// Samma geometri som kompilera.py:kameranycklar. Underlaget innehåller bara
// uppmätta kameror, personmål och sedda props ur grundplanen, inga stativlägen.
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const mul=(a,k)=>a.map(x=>x*k);
const dot=(a,b)=>a.reduce((n,x,i)=>n+x*b[i],0);
const unit=a=>{const n=Math.hypot(...a);if(n<1e-8)throw Error('Kamerans position och mål sammanfaller.');return mul(a,1/n);};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const pos=k=>k.matris.slice(0,3).map(r=>r[3]);
const col=(k,i)=>k.matris.slice(0,3).map(r=>r[i]);
const median=a=>{const x=[...a].sort((a,b)=>a-b),i=Math.floor(x.length/2);return x.length%2?x[i]:(x[i-1]+x[i])/2;};

export function stativNyckel(M,s){
 const u=M.stativunderlag;if(!u)throw Error('Stativkamerans mätunderlag saknas.');
 const e=s.camera,[a,b]=s.cameraSource||[s.a,s.b],source=u.scener[s.origin];
 const measured=u.kameror[a],p=pos(measured),fov=e.fov_grader??40,tv=Math.tan(fov*Math.PI/360),th=tv*u.bredd/u.hojd;
 let points=[],target;
 if(e.mal){
  points=(source.mal[e.mal.id]?.[e.mal.punkt||'kropp']||[]).filter(k=>a<=k.ruta&&k.ruta<b).map(k=>k.mal_m);
  if(!points.length)throw Error('Personmålet är inte synligt i scenen.');
  target=[0,1,2].map(i=>median(points.map(p=>p[i])));
 }else target=sub(p,col(measured,2));
 if(e.inramning&&e.mal?.punkt==='huvud')target=sub(target,[0,0,{hel:2.1,halv:1.25,nara:.55}[e.inramning]*.28]);
 const back=unit(sub(p,target));let right=cross([0,0,1],back);
 if(Math.hypot(...right)<1e-8)right=cross([0,1,0],back);
 right=unit(right);const up=cross(back,right);
 let distance=Math.hypot(...sub(p,target));
 if(e.inramning){
  distance={hel:2.1,halv:1.25,nara:.55}[e.inramning]/(2*tv);
  for(const point of [...points,...source.props.filter(o=>!s.cameraHiddenProps?.includes(o.id)).map(o=>o.pos_m)]){
   const delta=sub(point,target),x=dot(right,delta),y=dot(up,delta),z=dot(back,delta);
   distance=Math.max(distance,z+(Math.abs(x)+.25)/th,z+(Math.abs(y)+.2)/tv);
  }
 }
 const p1=add(target,mul(back,distance));
 return {matris:[...p1.map((x,i)=>[right[i],up[i],back[i],x]),[0,0,0,1]],mal_m:target,
  lins_mm:M.cameras.sensor_bredd_mm*u.hojd/u.bredd/(2*tv)};
}

// Webbpaketet har en äldre koordinatram. Flytta position och mål med samma
// rigida transform, förankrad i den uppmätta kameran (ingen meterskala ändras).
export function stativIPaket(M,s){
 const key=stativNyckel(M,s),a=(s.cameraSource||[s.a,s.b])[0];
 const base=M.stativunderlag.kameror[a],pkg=M.cameras.nycklar[a];
 const vector=v=>[0,1,2].map(i=>[0,1,2].reduce((n,j)=>n+col(pkg,j)[i]*dot(col(base,j),v),0));
 const point=p=>add(pos(pkg),vector(sub(p,pos(base))));
 const axes=[0,1,2].map(i=>vector(col(key,i))),p=point(pos(key));
 return {...key,mal_m:point(key.mal_m),matris:[...p.map((x,i)=>[...axes.map(v=>v[i]),x]),[0,0,0,1]]};
}

export function stativMatt(M,s){
 const key=stativNyckel(M,s),base=M.cameras.nycklar[Math.floor((s.a+s.b)/2)];
 const measured=M.stativunderlag.kameror[Math.floor((s.a+s.b)/2)];
 return {lens_mm:key.lins_mm,lens_faktor:key.lins_mm/base.lins_mm,
  forskjutning_m:Math.hypot(...sub(pos(key),pos(measured)))};
}
