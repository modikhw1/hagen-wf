import re,sys
def rows(fn):
    out={}
    for l in open(fn,encoding='utf-8'):
        m=re.match(r'\| (s\d+|S\d+) \| ([\d./–-]+) \|.*\| ((?:bra|granska|dålig|ej bedömd)[^|]*) \|$',l.rstrip())
        if m:out[m.group(1).lower()]=(m.group(2),m.group(3))
    return out
pairs=[('b','b/tom2','b/tom3'),('kenny','kenny/tom2','kenny/tom3'),('a','a/tom2','a/tom3'),('notan','notan/golv_tom','notan/jamn_tom')]
for c,a,b in pairs:
    A=rows(a+'/kvalitet.md');B=rows(b+'/kvalitet.md')
    print('##',c)
    for k in sorted(B,key=lambda s:int(s[1:])):
        sa=A.get(k,('-','saknas'));sb=B[k]
        print(f'{k}: {sa[1].split(":")[0]} | {sb[1].split(":")[0]}   [{sb[1][:230]}]')
