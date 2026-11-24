"""Source-only prop measurements. Six free-tier Gemini calls, cached; no keys logged.
Run with the project venv: python -B scen/3d/measure_props3.py
"""
import json,os,time,subprocess,shutil
from pathlib import Path
import cv2
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
SAMPLES={'S1':36,'S2':93,'S3':141,'S4':213,'S5':267,'S6':309}
def main():
    start=time.perf_counter();out=ROOT/'verifiering/fas3/source';out.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'cache/gemini-phase3';cache.mkdir(parents=True,exist_ok=True)
    if not (ROOT/'scen3d.fas2.json').exists():shutil.copy2(ROOT/'scen3d.json',ROOT/'scen3d.fas2.json')
    cap=cv2.VideoCapture(str(REPO/'scen/klipp/d-dialog-notan.mp4'))
    for sid,n in SAMPLES.items():
        image=out/f'{sid}-{n:03d}.jpg';cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,bgr=cap.read();assert ok;cv2.imwrite(str(image),bgr)
        target=ROOT/f'data/props-source-{sid}-3.json'
        if target.exists():continue
        owner='A' if sid in ['S1','S3','S6'] else 'C' if sid=='S4' else 'B'
        context=f'''VIKTIGT: detta är ORIGINALFOTOT från videon, inte linjeteckning. Vi mäter rekvisita, inte personer eller rum. Ange endast synliga saker på huvudpersonens bord/i händer. Använd exakta etiketter med ägare {owner}:cup (pappmugg), {owner}:can (dryckesburk), {owner}:burger (själva synliga hamburgaren, UTAN papper/box), {owner}:burger_wrap (öppen box/papper runt den främre hamburgaren), {owner}:fries (hela pommesportionen inklusive dess kartong), {owner}:sauce (liten såskopp), {owner}:tray (bricka), {owner}:terminal (kortterminal), {owner}:fry (enskild pommes i handen). Om det finns ytterligare en inslagen produkt bakom främre hamburgaren: {owner}:rear_wrap (papper/förpackning, innehåll okänt). Tajta synliga rutor. Inga gissade dolda matvaror. Utelämna saker som inte säkert går att identifiera. Ingen person, möbel eller annan bakgrund. Separera MAT från förpackning; överlappande rutor är okej.'''
        subprocess.run(['node',str(ROOT/'gemini_source3.mjs'),str(image),str(target),context],check=True,cwd=REPO,env={**os.environ,'TEMP':str(cache),'TMP':str(cache),'CURL_SSL_BACKEND':'openssl'})
    cap.release();(ROOT/'data/measure-props-runtime-3.json').write_text(json.dumps({'seconds':time.perf_counter()-start,'source_frames':SAMPLES,'max_calls':6},indent=2))
if __name__=='__main__':main()
