"""Komplettera en snabb plan med full diagnostik, utan ingest eller rendering."""
import argparse
from pathlib import Path
from gemensamt import ladda, skriv, kontrollmodul
from kvalitet import komplettera
from trohet import mat, rapport

VARNING='Bildtrohet överskrider egna diagnostiska trösklar. Se kvalitet.bildtrohet; render kräver uttryckligt granskningsläge.'

def diagnostik(plan):
    # Planens mätpekare är absoluta. Ändrade hashlåsta mätfiler får inte användas.
    kontroll=kontrollmodul()
    kontroll.hashar(dict(matning=plan['matning'],semantik={}),Path('.'))
    if kontroll.fel_lista:raise ValueError('\n'.join(kontroll.fel_lista))
    if 'skymning' not in plan['kvalitet']:raise ValueError('Planen saknar lösta skymningsbeslut; kompilera om den.')
    plan['kvalitet']['bildtrohet']=mat(plan)
    komplettera(plan,{},med_planbeslut=False)
    plan['kvalitet'].pop('diagnostik',None)
    plan['varningar']=[v for v in plan['varningar'] if v!=VARNING]
    if plan['kvalitet']['bildtrohet']['flaggad']:plan['varningar'].append(VARNING)
    return plan

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan');p.add_argument('ut',help='ny plan med diagnostik');a=p.parse_args()
    if Path(a.ut).exists():raise FileExistsError('Välj en ny utfil: '+a.ut)
    plan=diagnostik(ladda(a.plan));skriv(a.ut,plan);rapport(plan,a.ut)

if __name__=='__main__':main()
