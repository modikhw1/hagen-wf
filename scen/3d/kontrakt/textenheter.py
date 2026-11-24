"""Gemensam synlighet för ett tal och dess enhet på samma källrad."""
import copy
import re


def korsar(a,b):
    ax,ay,aw,ah=a['box'];bx,by,bw,bh=b['box']
    return max(ax,bx)<min(ax+aw,bx+bw) and max(ay,by)<min(ay+ah,by+bh)


def kallstod(a,b):
    """Samtidighet är stödd när båda enheterna är självständigt uppmätta i källan."""
    return all(x.get('ursprung',{}).get('typ')=='uppmatt' and x.get('ursprung',{}).get('timing_typ','uppmatt')=='uppmatt' for x in (a,b))


def block(items):
    """Gör samtidiga fragment till ett block och ersätt ostödda block i källordning."""
    utvidgade=[]
    for t0 in items:
        t=copy.deepcopy(t0);u=t.get('ursprung',{});match=re.match(r'^(.+?[!?])\s+(.+)$',t['text'])
        # En lokaliserad delsträng mitt i en första lång text lämnar annars
        # ett verkligt inledande utrop osynligt. Bevara det som föregående block.
        if match and u.get('timing_typ')=='uppmatt_delstrang' and u.get('sokt_delstrang') and t['start_s']>u.get('scen_start_s',t['start_s'])+1e-6:
            prefix=copy.deepcopy(t);prefix['text']=match.group(1);prefix['start_s']=u['scen_start_s'];prefix['slut_s']=t['start_s']
            prefix['ursprung']['metod']='Inledande utrop före den lokaliserade delsträngens första källruta.';prefix['ursprung']['timing_typ']='avgransad_av_delstrang'
            t['text']=match.group(2);utvidgade.append(prefix)
        utvidgade.append(t)
    result=[]
    for t in utvidgade:
        same=next((x for x in result if x['scen']==t['scen'] and abs(x['start_s']-t['start_s'])<1e-6 and abs(x['slut_s']-t['slut_s'])<1e-6
                   and korsar(x,t) and not x.get('ursprung',{}).get('timing_samordning') and not t.get('ursprung',{}).get('timing_samordning')),None)
        if same is None:result.append(copy.deepcopy(t));continue
        delar=same['ursprung'].setdefault('sammanslagen_fran',[same['id']]);delar.append(t['id'])
        same['text']=(same['text'].rstrip()+' '+t['text'].lstrip()).strip()
        x0=min(same['box'][0],t['box'][0]);y0=min(same['box'][1],t['box'][1]);x1=max(same['box'][0]+same['box'][2],t['box'][0]+t['box'][2]);y1=max(same['box'][1]+same['box'][3],t['box'][1]+t['box'][3])
        same['box']=[x0,y0,x1-x0,y1-y0];same['stil']['justering']='center'
        same['konfidens']=min(same.get('konfidens',0),t.get('konfidens',0))
        same['ursprung']['typ']='antagen' if 'antagen' in (same['ursprung'].get('typ'),t.get('ursprung',{}).get('typ')) else 'uppmatt'
        same['ursprung']['metod']='Samtidiga textfragment med samma källintervall och skärmyta har samlats till ett block.'
        if not same.get('replik'):same['replik']=t.get('replik')
        if same.get('replik'):same['typ']='undertext'
    for scen in {t['scen'] for t in result}:
        seq=[t for t in result if t['scen']==scen]
        for i,a in enumerate(seq):
            for b in seq[i+1:]:
                if not korsar(a,b) or a['slut_s']<=b['start_s'] or b['slut_s']<=a['start_s']:continue
                if kallstod(a,b):
                    a['ursprung'].setdefault('samvisning_med',[]).append(b['id']);b['ursprung'].setdefault('samvisning_med',[]).append(a['id']);continue
                if a['start_s']<=b['start_s']<a['slut_s']:a['slut_s']=b['start_s']
                else:b['slut_s']=a['start_s']
    result=[t for t in result if t['slut_s']-t['start_s']>1e-6]
    for i,t in enumerate(result):t['id']=f'st{i+1}'
    return result


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
    return block(out)
