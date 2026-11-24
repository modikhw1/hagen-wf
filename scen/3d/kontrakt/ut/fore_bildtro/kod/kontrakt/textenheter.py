"""Gemensam synlighet för ett tal och dess enhet på samma källrad."""
import copy
import re


def samordna(items):
    groups=[]
    for t in items:
        key=(t['scen'],t['text'],tuple(t['box']),tuple(sorted(t['stil'].items())))
        group=next((g for g in groups if g['key']==key),None)
        if group is None:group=dict(key=key,item=copy.deepcopy(t),span=[]);groups.append(group)
        group['span'].append([t['start_s'],t['slut_s']])
    for g in groups:
        t=g['item']
        if not re.fullmatch(r'\d[,.]\d{3}',t['text']):continue
        possible=[h for h in groups if h['item']['scen']==t['scen'] and h['item']['text']=='kg' and h['item']['stil']['farg']==t['stil']['farg'] and abs(h['item']['box'][1]-t['box'][1])<20]
        if not possible:continue
        unit=min(possible,key=lambda h:abs(h['item']['box'][1]-t['box'][1]))
        # Antagen samhörighet: tal och enhet visas som ett värde. Båda måste
        # ha egna teckenträffar. Deras union fyller kontrastbortfall i kött/papper.
        spans=g['span']+unit['span'];spans.sort();merged=[]
        for a,b in spans:
            if merged and a<=merged[-1][1]+1e-6:merged[-1][1]=max(merged[-1][1],b)
            else:merged.append([a,b])
        g['span']=unit['span']=merged
        for h in (g,unit):h['item']['ursprung']['timing_samordning']=dict(typ='antagen',orsak='Tal och kg på samma rad hör ihop. Union av bådas uppmätta teckenträffar fyller lokala kontrastbortfall.')
    out=[]
    for g in groups:
        for a,b in g['span']:
            t=copy.deepcopy(g['item']);t.update(id=f'st{len(out)+1}',start_s=a,slut_s=b);out.append(t)
    return out
