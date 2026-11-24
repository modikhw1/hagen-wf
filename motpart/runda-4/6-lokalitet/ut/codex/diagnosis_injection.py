"""Can the actual per-frame dispersion detect a common 30-degree normal bias?"""
from pathlib import Path
import ast, json, math
import numpy as np
OUT=Path(__file__).resolve().parent; BASE=OUT.parents[1]
src=(BASE/'lokalitet.py').read_text(encoding='utf-8')
tree=ast.parse(src)
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['dominant_axel','lodlinje']]
env={'math':math,'np':np,'STOD':('golv','bank','bord','spis','skap')}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(BASE/'lokalitet.py'),'exec'),env)
results=[]
for bias in [0,30]:
    angle=math.radians(bias)
    normal=np.array([0.,-math.cos(angle),-math.sin(angle)])
    obs=[{'N':np.broadcast_to(normal,(30,30,3)).copy(),'G':np.full((30,30),'golv',object),'M':np.ones((30,30),bool)} for _ in range(3)]
    u=env['lodlinje'](obs,None)[0]
    per=[env['lodlinje']([o],None)[0] for o in obs]
    spread=[round(math.degrees(math.acos(np.clip(float(p@u),-1,1))),1) for p in per]
    measured=math.degrees(math.asin(u[2])); truth=0.
    assert max(spread)==0
    results.append({'injected_bias_deg':bias,'independent_truth_deg':truth,'moge_pitch':measured,'spread':spread,'absolute_error_deg':abs(measured-truth)})
assert results[1]['absolute_error_deg']>10
(OUT/'diagnosis-injection.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results))
