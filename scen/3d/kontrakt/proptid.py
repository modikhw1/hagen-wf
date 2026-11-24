"""Ordnade propredigeringar över delar av en scen, utan att ändra kropp/tid."""
import copy


def andra(scen, pid, span, fn):
    a, b = scen['a'], scen['b']
    left, right = max(a, span[0]), min(b, span[1])
    if left >= right:
        return None
    current = scen['objekt'].get(pid)
    versions = current.get('_propversioner') if current else None
    if versions is None:
        versions = [dict(kalla=[a, b], objekt=copy.deepcopy(current))]
    result, changes = [], []
    for version in versions:
        va, vb = version['kalla']
        cuts = sorted({va, vb, max(va, min(vb, left)), max(va, min(vb, right))})
        for x, y in zip(cuts, cuts[1:]):
            obj = copy.deepcopy(version['objekt'])
            if left <= x < right:
                obj = fn(obj)
                changes.append(dict(kalla=[x, y], objekt=copy.deepcopy(obj)))
            result.append(dict(kalla=[x, y], objekt=obj))
    kept = [v['objekt'] for v in result if v['objekt'] is not None]
    if not kept:
        scen['objekt'].pop(pid, None)
    elif len(result) == 1:
        scen['objekt'][pid] = kept[0]
    else:
        wrapper = copy.deepcopy(kept[0])
        wrapper['_propversioner'] = result
        scen['objekt'][pid] = wrapper
    return changes


def byggposter(objekt, scen, ut):
    versions = objekt.get('_propversioner', [dict(kalla=[scen['a'], scen['b']], objekt=objekt)])
    for v in versions:
        a, b = max(v['kalla'][0], scen['a']), min(v['kalla'][1], scen['b'])
        if v['objekt'] is None or a >= b:
            continue
        obj = copy.deepcopy(v['objekt'])
        obj['synlig_ut'] = [ut[0] + a - scen['a'], ut[0] + b - scen['a']]
        yield obj
