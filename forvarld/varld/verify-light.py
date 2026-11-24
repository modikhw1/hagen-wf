"""Read-only inputs, small local checks. No upstream Python imports or compiler."""
from pathlib import Path
import json,re,ast
import cv2,numpy as np
O=Path('forvarld/varld');read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))

def valid(v,s,root):
    if '$ref' in s:
        node=root
        for key in s['$ref'][2:].split('/'):node=node[key]
        if not valid(v,node,root):return False
    types={'null':v is None,'boolean':isinstance(v,bool),'integer':type(v)==int,'number':type(v) in (float,int),'string':isinstance(v,str),'array':isinstance(v,list),'object':isinstance(v,dict)}
    if 'type' in s and not any(types[t] for t in (s['type'] if isinstance(s['type'],list) else [s['type']])):return False
    if 'const' in s and v!=s['const'] or 'enum' in s and v not in s['enum']:return False
    if isinstance(v,str) and (len(v)<s.get('minLength',0) or 'pattern' in s and not re.search(s['pattern'],v)):return False
    if type(v) in (float,int) and not s.get('minimum',float('-inf'))<=v<=s.get('maximum',float('inf')):return False
    if isinstance(v,list):
        if not s.get('minItems',0)<=len(v)<=s.get('maxItems',float('inf')):return False
        if 'items' in s and not all(valid(x,s['items'],root) for x in v):return False
    if isinstance(v,dict):
        if len(v)<s.get('minProperties',0) or any(k not in v for k in s.get('required',[])):return False
        props=s.get('properties',{})
        if s.get('additionalProperties') is False and any(k not in props for k in v):return False
        if any(not valid(x,props[k],root) for k,x in v.items() if k in props):return False
    if any(not valid(v,b,root) for b in s.get('allOf',[])):return False
    if 'anyOf' in s and not any(valid(v,b,root) for b in s['anyOf']):return False
    if 'oneOf' in s and sum(valid(v,b,root) for b in s['oneOf'])!=1:return False
    return True

schema=read('scen/3d/kontrakt/regi.schema.json');base=read(O/'pipeline/base-regi.json');samples=read(O/'edit-check.json')['edits']
for r in read(O/'chat-measurements.json')['rows']:samples+=r['response'].get('edits',[])
failures=[e for e in samples if not valid({**base,'edits':[e]},schema,schema)]
M=read(O/'paket/notan/manifest.json');masked=0
for s in M['scenes']:
    atlas=cv2.imread(str(O/'paket/notan'/s['live']['atlas']))
    for i in range(s['source'][1]-s['source'][0]):
        patch=atlas[(i//8)*256:(i//8+1)*256,(i%8)*144:(i%8+1)*144]
        for t in M['text']:
            if t['ut'][0]<=s['source'][0]+i<t['ut'][1]:
                x,y,w,h=np.asarray(t['box'])/4
                if patch[max(0,int(y)):int(np.ceil(y+h)),max(0,int(x)):int(np.ceil(x+w))].any():raise ValueError('Live alpha contains source text')
                masked+=1
for name in ['body_source.py','export.py','export_blender.py','refine.py','live.py','compose-v5.py']:
    ast.parse((O/name).read_text(encoding='utf-8-sig'))
size={name:sum(p.stat().st_size for p in (O/name).rglob('*') if p.is_file()) for name in ['paket/notan','paket/backdrops','paket']}
result=dict(schemaSamples=len(samples),schemaFailures=failures,sourceTextMaskChecks=masked,packageBytes=size,pythonSyntax='ok',scope='schema subset used by regi; no upstream reference/hash/compiler validation')
(O/'light-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if failures:raise ValueError('Invalid regi samples')
