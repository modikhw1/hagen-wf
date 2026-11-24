import pycolmap, time, sys
from pathlib import Path
H=Path(sys.argv[1]); db=H/'db.db'; db.unlink(missing_ok=True); ut=H/'sparse'; ut.mkdir(exist_ok=True)
t=time.time()
eo=pycolmap.FeatureExtractionOptions(); eo.sift.max_num_features=4000
ro=pycolmap.ImageReaderOptions(); ro.mask_path=str(H/'masker'); ro.camera_model='SIMPLE_RADIAL'
pycolmap.extract_features(db, H/'bilder', camera_mode=pycolmap.CameraMode.SINGLE, reader_options=ro, extraction_options=eo)
print('extraktion', round(time.time()-t,1), flush=True)
mo=pycolmap.SequentialPairingOptions(); mo.overlap=12
pycolmap.match_sequential(db, pairing_options=mo)
print('matchning', round(time.time()-t,1), flush=True)
rec=pycolmap.incremental_mapping(db, H/'bilder', ut)
print('kartor', len(rec), round(time.time()-t,1))
for i,r in rec.items(): print(i, r.summary())
