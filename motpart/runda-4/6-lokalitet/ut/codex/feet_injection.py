"""Execute the actual contact/height source block with deliberately wrong input geometry."""
from pathlib import Path
import json, textwrap, math
import numpy as np

OUT=Path(__file__).resolve().parent; BASE=OUT.parents[1]
src=(BASE/'lokalitet.py').read_text(encoding='utf-8').splitlines()
begin=next(i for i,s in enumerate(src) if '# L2b Kontaktskala:' in s)
end=next(i for i,s in enumerate(src) if 'C = np.array([0.0, 0.0, h])' in s)
block=textwrap.dedent('\n'.join(src[begin:end]))
results=[]
for name,floor_y,foot_y in [('baseline',2.,1.4),('floor_depth_x2',4.,1.4),('feet_one_metre_lower',2.,2.4)]:
    P=np.zeros((20,20,3)); P[...,1]=floor_y; P[...,2]=3
    J=np.zeros((5,2,3)); J[...,1]=foot_y; J[...,2]=3
    env=dict(np=np,math=math,obs=[{'P':P,'M':np.ones((20,20),bool),'G':np.full((20,20),'golv',object)}],
             u_cv=np.array([0.,-1.,0.]),Jcv={'A':(np.arange(5),J)},A={'personer':{'A':{'pose':'staende'}}},
             utan_stod=[],ix={'l_foot':0,'r_foot':1},info={'skala':{'varde':1.0}},skala=1.)
    exec(compile(block,str(BASE/'lokalitet.py')+':contact-excerpt','exec'),env)
    foot_over=env['h']-foot_y
    assert abs(foot_over-.08)<1e-12
    assert env['info']['kamerahojd']['m']==env['info']['kamerahojd']['fotter_m']
    results.append({'case':name,'floor_y':floor_y,'foot_y':foot_y,'scale':env['skala'],'height':env['h'],'foot_over_floor':foot_over})
(OUT/'feet-injection.json').write_text(json.dumps({'source_lines':[begin+1,end],'tests':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
