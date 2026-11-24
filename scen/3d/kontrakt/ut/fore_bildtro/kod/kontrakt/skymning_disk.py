"""Bevara en öppen monter genom att bara utelämna osäkra ramdelar."""
import numpy as np


def valj(records,blocked,grans):
    removed=set();handled=set();actions=[]
    for scene,group in sorted(blocked):
        rows=[r for r in records if r['scen']==scene and r['grupp']==group]
        if not rows:continue
        active={id for row in rows for id in row['hits']};den=sum(len(next(iter(row['hits'].values()))) for row in rows)
        def count(ids):
            total=0
            for row in rows:
                bits=[a for id,a in row['hits'].items() if id in ids]
                if bits:total+=int(np.logical_or.reduce(bits).sum())
            return total
        from skymning import DELAR,DEL_GRANS,DEL_MIN
        def delvis(ids):
            pc=np.zeros((len(DELAR),2),int)
            for row in rows:
                bits=[a for id,a in row['hits'].items() if id in ids]
                if not bits or 'delar' not in row:continue
                u=np.logical_or.reduce(bits)
                for j in range(len(DELAR)):
                    sel=row['delar']==j;pc[j,0]+=int((u&sel).sum());pc[j,1]+=int(sel.sum())
            return any(pc[j,0]>=DEL_MIN and pc[j,0]/max(pc[j,1],1)>DEL_GRANS for j in range(len(DELAR)))
        def flaggad(ids,cur):return (cur/max(den,1)>grans and cur>=10) or delvis(ids)
        handled.add((scene,group));before=count(active);current=before
        while active and flaggad(active,current):
            candidate=min(active,key=lambda id:(delvis(active-{id}),count(active-{id}),-sum(int(r['hits'][id].sum()) for r in rows if id in r['hits']),id))
            active.remove(candidate);removed.add((scene,candidate));current=count(active)
            actions.append(dict(scen=scene,del_id=candidate,grupp=group,atgard='en ramdel utelämnad endast i denna scen',status='antagen',
                orsak='Girigt val av enskilda mallbitar tills den oförändrade skymningsgränsen klaras. Andra delar av disken behålls; ingen person, kamera eller gräns flyttas.',
                grupp_fore_andel=before/max(den,1),grupp_efter_andel=current/max(den,1)))
    return removed,handled,actions
