"""One sequential GPU reservation. Never retries automatically; preserves exact errors."""
import argparse,datetime,importlib.util,io,json,sys,time,traceback,zipfile,os
from pathlib import Path

BANK=Path(__file__).resolve().parent
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('candidate');p.add_argument('mode',choices=['prepare','evaluate']);p.add_argument('--shots',default='all');args=p.parse_args()
    bp=BANK/'budget.json';budget=json.loads(bp.read_text(encoding='utf-8'));previous=[e for e in budget['events'] if e['candidate']==args.candidate];startup=not any(e.get('success') for e in previous)
    reserve=min(900,4500-budget['charged_upper_bound_seconds'],1200-sum(e['charged_upper_bound_seconds'] for e in previous) if startup else 900)
    if args.mode=='evaluate':
        if budget['active_reservation']:raise RuntimeError('Unsettled GPU reservation: review before continuing')
        if reserve<90:raise RuntimeError('GPU allowance exhausted')
        os.environ['RUM_GPU_TIMEOUT']=str(int(reserve-60))
    spec=importlib.util.spec_from_file_location('bank_candidate',BANK/f'modal_{args.candidate}.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    if args.mode=='prepare':
        import modal
        with modal.enable_output(),module.app.run():result=module.prepare.remote()
        write(BANK/f'{args.candidate}_prepared.json',result);print(json.dumps(result,ensure_ascii=False));return
    manifest=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'));jobs=[]
    for job in manifest:
        if args.shots!='all' and job['id'] not in args.shots.split(','):continue
        if (BANK/'ut'/args.candidate/job['id']/'timing.json').exists():continue
        paths=[BANK/x['path'] for x in job['inputs']] if 'inputs' in job else [BANK/job['input_dir']/f'{i:05d}.jpg' for i in job['frames']]
        import numpy as np
        maxframes=len(paths) if job['id'].endswith('_fullrate') else getattr(module,'MAX_FRAMES',10000)
        chosen=list(range(len(paths))) if len(paths)<=maxframes else sorted(set(np.rint(np.linspace(0,len(paths)-1,maxframes)).astype(int).tolist()+[job['frames'].index(i) for i in job['overlay_frames'] if i in job['frames']]))
        payload=dict(id=job['id'],images=[paths[i].read_bytes() for i in chosen],indices=chosen,fps=(job.get('fps') or 30)*len(paths)/job['source_frames'])
        if getattr(module,'USE_EXISTING_MASKS',False):
            import cv2
            maskpath=BANK.parents[2]/job['reference']/'masker.npy' if job.get('reference') else None
            masks=np.load(maskpath,mmap_mode='r') if maskpath and maskpath.exists() else None
            payload['masks']=[]
            mask_cache={};available=[]
            for i in chosen:
                frame=job['frames'][i];local_masks=masks;source_mask=None
                if local_masks is None and 'inputs' in job:
                    item=job['inputs'][i];frame=item['frame'];sid='S1' if item['shot']=='notan_S1' else 'S4';source_mask=BANK.parents[2]/'scen/3d/ingest/ut/notan-tagningar'/sid/'masker.npy'
                elif local_masks is None and job['id'] in ['notan_uncut','notan_fullrate']:
                    start=0
                    for sid,count in [(1,73),(2,41),(3,57),(4,85),(5,25),(6,56),(7,46)]:
                        if start<=frame<start+count:
                            frame-=start;source_mask=BANK.parents[2]/'scen/3d/ingest/ut/notan-tagningar'/f'S{sid}'/'masker.npy';break
                        start+=count
                if source_mask and source_mask.exists():
                    key=str(source_mask)
                    if key not in mask_cache:mask_cache[key]=np.load(source_mask,mmap_mode='r')
                    local_masks=mask_cache[key]
                available.append(local_masks is not None)
                mask=(local_masks[frame]>0).astype(np.uint8)*255 if local_masks is not None else np.zeros((768,432),np.uint8)
                payload['masks'].append(cv2.imencode('.png',mask)[1].tobytes())
            payload['masks_available']=all(available)
        jobs.append(payload)
    if not jobs:print('No uncached jobs');return
    budget=json.loads(bp.read_text(encoding='utf-8'))
    if budget['active_reservation']:raise RuntimeError('Unsettled GPU reservation: review before continuing')
    if startup and sum(e['charged_upper_bound_seconds'] for e in previous)+reserve>1200:raise RuntimeError('Startup allowance exhausted; do not retry')
    if budget['charged_upper_bound_seconds']+reserve>4500:raise RuntimeError('Total GPU allowance exhausted')
    event=dict(candidate=args.candidate,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reserved_seconds=reserve,charged_upper_bound_seconds=reserve,shots=[j['id'] for j in jobs],startup=startup,success=False)
    budget['events'].append(event);budget['active_reservation']=event['utc'];budget['charged_upper_bound_seconds']+=reserve;write(bp,budget)
    with (BANK/'RUM-LOGG.md').open('a',encoding='utf-8') as log:log.write(f'\nGPU-reservation {event["utc"]}: {args.candidate}, {reserve} s, {event["shots"]}. Kommando: `scen/.venv/Scripts/python.exe -B scen/3d/rumsbank/run_bank.py {args.candidate} evaluate --shots {args.shots}`.\n')
    t=time.monotonic();last=0;completed=[];ran=[]
    try:
        import modal
        with modal.enable_output(),module.app.run():
            for result in module.evaluate.remote_gen(jobs):
                dest=BANK/'ut'/args.candidate/result['id'];dest.mkdir(parents=True,exist_ok=True)
                with zipfile.ZipFile(io.BytesIO(result['archive'])) as z:
                    for name in z.namelist():
                        if '/' in name or '\\' in name or '..' in name:raise ValueError('Unexpected archive path')
                        (dest/name).write_bytes(z.read(name))
                write(dest/'timing.json',result['info']);last=result['info']['elapsed_s'];completed.append(result['id'])
                if result['info'].get('status')!='did_not_run':ran.append(result['id'])
                print('SAVED',result['id'],flush=True)
        event['success']=bool(ran);event['function_completed']=True
    except Exception:
        error=traceback.format_exc();(BANK/f'{args.candidate}_error.txt').write_text(error,encoding='utf-8');print(error,flush=True)
    # Conservative upper bound includes local upload/build/wait, capped at reservation. Startup/idle extra 60 s.
    wall=time.monotonic()-t;charged=min(reserve,wall+60)
    event.update(wall_s=wall,measured_function_lower_bound_s=last,charged_upper_bound_seconds=charged,completed=completed)
    budget['charged_upper_bound_seconds']+=charged-reserve;budget['measured_gpu_function_seconds']+=last;budget['active_reservation']=None;write(bp,budget)
    with (BANK/'RUM-LOGG.md').open('a',encoding='utf-8') as log:log.write(f'Avslut {args.candidate}: success={event["success"]}, sparat={completed}, konservativ debitering {charged:.1f} s.\n')

if __name__=='__main__':main()
