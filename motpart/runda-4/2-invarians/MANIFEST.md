# MANIFEST, steg 2 (invarians), version v1

Skrivet 2026-11-20T22:42:53 (lokal tid) **före första testmätningen** av de 12 testklippen. Protokoll: `motpart/runda-4/T4-codex/FORREGISTRERING.md` avsnitt Gemensamt och A. Tolkningar och avvikelser: `AVVIKELSER.md` (skriven före detta manifest).

## Frön
- Urvalsfrö 202611204 (T4, `las_urval.py`, redan utfört). Permutationsfrö i förtestet: `numpy.random.default_rng(202611204)`, 100 permutationer.
- Ingen annan slumpkälla används i mätning eller dom. ffmpeg-recepten är deterministiska (kontrolleras med Cr och N0r).

## Indata (sha256)
- `motpart/runda-4/1-datagrund/urval.json` 41f5010b60b268264244b69df43be0e2d9fb057dd7c64e946e0a69abacb434e1
- `motpart/runda-4/1-datagrund/manifest.jsonl` 9453841dfe0c08eb72f1812fe57ea746d1de82c200bda980d9c66846efd94914
- `motpart/runda-3-opus/D-medielager/urval.json` ec4bf80d26b22acceea98085bc06d27b4d7fc3557354ce2cb3de08dcdd570c37
- `motpart/runda-4/T4-codex/FORREGISTRERING.md` 42a1466c61982aade7f3749092f92a00feaca7e5efd3555411c003b6e585d277
- `motpart/runda-4/T4-codex/las_urval.py` 95f91bd10766fb5962bb8863addb66231e42b2886b2ecc31be4d3df4f9c949d2
- Alla 200 källfiler i `C:\Users\praiseworthy\Downloads\letrend-r4\`: sha256 verifierad mot `manifest.jsonl` (0 avvikelser), `verifiera_kalla.py`; ffprobe för de 156 använda i `ffprobe_kallor.json` (902d4b229210b7e72c44ae546cc0cdb7303af222dada864c60b19e5168d4c102).
- Urval återskapat med `las_urval.py` i `urval_las.json` (d8f09b7e02ff473255814e22005db9cbdca8eb6241557b66ce9f8bbdfd9ec39b): 12 testklipp, 144 referensklipp i 72 konton.

## Extraktorer (orörda; byte-identiska kopior körs, kontrolleras vid trädbygget)
- `video/format/e28-tek.mjs` d41786c4984bd773b4e26033dc8e9483fee3ba2dd7609aa4d97b56fd672dbe15
- `video/format/e30_tal.py` c940a359e71e6b26820cbfeb3690a30f60cd8305f19ddf1dced50bb65a3ef72c
- `video/format/e37_personer.py` ed06486fe1901d8f3f03f4e0aab663226630d80eff6d3c806c4f2d649153c62b
- `video/analys/verktyg.mjs` 12726c2de3320e23e818e9add3409f3c29eba8cfc15b7c20d3f209a6f23f7e1e
- Modellvikter `data/format/e37/yolov8n.pt` f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36
- Silero VAD: `load_silero_vad(onnx=True)` ur paketet silero-vad (modellfil i paketet).

## Min kod (sha256)
- `recept.py` e9c0c746936216feb190e92aa23c6507dcecd0b45f0803992ad2bd282b7e8fbe
- `falt.py` 55e5279e774fb4b2780fcb30dd16fc0b626e8ee9653a790e8321f60137ac6039
- `mat_adapter.py` 58a8805ed7712c2e967065d3c01a823d4693d6af98f0c127fb4e63b6af3be2ac
- `bilaga.py` cf3f29bc3dd51d645ac59644f58f78acdde0ad561db8a22c4ddbee2e1dac9b0f
- `ref_kor.py` 7c0be03d35ef1fbc40156f030eb2cf909c7f5de2fe38704bbd8a71dca0cf5088
- `test_kor.py` c47cc33573fb954987f753a21b16b94cc99fe6807553d9019e2fd3b9f2c87c14
- `analys.py` ad571975eaf8449a499effe443224c4c5aaacaeec41e1a4ddcb15885c713cdc9
- `kontaktkarta.py` 81e7ac0a4ba39e48c6928f5dee26369cc2019ca3249002d88bc49d4be2efabe5
- `bygg_kontroll.py` 63e5c8d5c5c72ec34bc00cf7ed7558dbebfdb5bf4cbb4db44f8b4cdef99656d6
- `verifiera_kalla.py` 3773458f4b6734e4ac4a109342531e3f48e53f3217f51b82981ab73481440a89
- `manifest.py` 420f46a3001bda0822cca6a18c1250bf1b7ab1437800cf93acaa739a693c018b

## Versioner
- Python 3.12.13 (`scen/.venv`), plattform Windows-10-10.0.19045-SP0, processor Intel64 Family 6 Model 142 Stepping 10, GenuineIntel
- numpy 2.5.4
- torch 2.15.0+cpu
- silero-vad 6.2.3
- onnxruntime 1.31.1
- ultralytics 8.4.204
- opencv-python 5.0.0.93
- opencv-python-headless 5.0.0.93
- scipy 1.18.1
- pillow 13.0.0
- node v24.14.1
- ffmpeg (fullständigt versions- och konfigurationsblock):
```text
ffmpeg version 8.1-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
built with gcc 15.2.0 (Rev11, Built by MSYS2 project)
configuration: --enable-gpl --enable-version3 --enable-static --disable-w32threads --disable-autodetect --enable-cairo --enable-fontconfig --enable-iconv --enable-gnutls --enable-lcms2 --enable-libxml2 --enable-gmp --enable-bzlib --enable-lzma --enable-libsnappy --enable-zlib --enable-librist --enable-libsrt --enable-libssh --enable-libzmq --enable-avisynth --enable-libbluray --enable-libcaca --enable-libdvdnav --enable-libdvdread --enable-sdl2 --enable-libaribb24 --enable-libaribcaption --enable-libdav1d --enable-libdavs2 --enable-libopenjpeg --enable-libquirc --enable-libuavs3d --enable-libxevd --enable-libzvbi --enable-liboapv --enable-libqrencode --enable-librav1e --enable-libsvtav1 --enable-libvvenc --enable-libwebp --enable-libx264 --enable-libx265 --enable-libxavs2 --enable-libxeve --enable-libxvid --enable-libaom --enable-libjxl --enable-libsvtjpegxs --enable-libvpx --enable-mediafoundation --enable-libass --enable-frei0r --enable-libfreetype --enable-libfribidi --enable-libharfbuzz --enable-liblensfun --enable-libvidstab --enable-libvmaf --enable-libzimg --enable-amf --enable-cuda-llvm --enable-cuvid --enable-dxva2 --enable-d3d11va --enable-d3d12va --enable-ffnvcodec --enable-libvpl --enable-nvdec --enable-nvenc --enable-vaapi --enable-libshaderc --enable-vulkan --enable-libplacebo --enable-opencl --enable-libcdio --enable-openal --enable-libgme --enable-libmodplug --enable-libopenmpt --enable-libopencore-amrwb --enable-libmp3lame --enable-libshine --enable-libtheora --enable-libtwolame --enable-libvo-amrwbenc --enable-libcodec2 --enable-libilbc --enable-libgsm --enable-liblc3 --enable-libopencore-amrnb --enable-libopus --enable-libspeex --enable-libvorbis --enable-ladspa --enable-libbs2b --enable-libflite --enable-libmysofa --enable-librubberband --enable-libsoxr --enable-chromaprint --enable-whisper
libavutil      60. 26.100 / 60. 26.100
libavcodec     62. 28.100 / 62. 28.100
libavformat    62. 12.100 / 62. 12.100
libavdevice    62.  3.100 / 62.  3.100
libavfilter    11. 14.100 / 11. 14.100
libswscale      9.  5.100 /  9.  5.100
libswresample   6.  3.100 /  6.  3.100

Exiting with exit code 0
```
- ffprobe: ffprobe version 8.1-full_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers

## Explicita extraktorparametrar (VAD och scen)
- E30, anrop i skriptet: `get_speech_timestamps(audio, model, sampling_rate=16000, return_seconds=True, min_silence_duration_ms=300)`. Övriga argument är paketets standardvärden för installerad version, uppslagna med `inspect.signature` och fastlåsta här:
```text
(audio: torch.Tensor, model, threshold: float = 0.5, sampling_rate: int = 16000, min_speech_duration_ms: int = 250, max_speech_duration_s: float = inf, min_silence_duration_ms: int = 100, speech_pad_ms: int = 30, return_seconds: bool = False, time_resolution: int = 1, visualize_probs: bool = False, progress_tracking_callback: Callable[[float], NoneType] = None, neg_threshold: float = None, window_size_samples: int = 512, min_silence_at_max_speech: int = 98, use_max_poss_sil_at_max_speech: bool = True)
```
- E30: avkodning `ffmpeg -v quiet -i <fil> -ac 1 -ar 16000 -f s16le -`, `torch.set_num_threads(2)`.
- E28: `ffmpeg -hide_banner -nostats -i <fil> -vf "select='gte(scene,0)',metadata=print" -af "silencedetect=n=-35dB:d=0.3,ebur128=framelog=quiet" -f null -`; byte där scenpoäng >0,3; första bildens poäng ignoreras.
- E37: YOLOv8n, sex rutor vid relativa positioner linspace(0,05, 0,95, 6), `imgsz=320`, klass 0, konfidens >=0,4, `torch.set_num_threads(2)`.
- Extraktorerna körs sekventiellt (E28 `--par 1`), en batch i taget.

## Kommandorader (argv; ingen shell). Platshållare: O.mp4 = originalfil, C.mkv = C-fil
```text
ffmpeg -nostdin -hide_banner -loglevel warning -y -i O.mp4 -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -vf fps=fps=30:start_time=0:round=near,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0,setsar=1 -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a pcm_s24le -fps_mode passthrough C.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -c copy N0.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -c:v libx264 -preset medium -crf 28 -pix_fmt yuv420p -threads:v 1 -c:a copy -fps_mode passthrough N1.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -vf scale=w='max(2,trunc(iw/4)*2)':h='max(2,trunc(ih/4)*2)':flags=lanczos,setsar=1 -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N2.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -af volume=-6dB -c:v copy -c:a pcm_s24le N3.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -af volume=-12dB -c:v copy -c:a pcm_s24le N4.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -vf fps=fps=15:start_time=0:round=near -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N5.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -vf crop=iw-4:ih-4:2:2,pad=iw+4:ih+4:2:2:black,setsar=1 -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a copy -fps_mode passthrough N6.mkv
ffmpeg -nostdin -hide_banner -loglevel warning -y -i C.mkv -map 0:v:0 -map 0:a:0? -map_metadata -1 -map_chapters -1 -vf setpts=(PTS-STARTPTS)/1.25,fps=fps=30:start_time=0:round=near -af atempo=1.25 -c:v ffv1 -level 3 -pix_fmt yuv420p -c:a pcm_s24le -fps_mode passthrough P.mkv
```
- Ytterligare en körning: `ffprobe`, `ffmpeg ... -f framehash -hash sha256`, `ffmpeg ... -af volumedetect`, samt E28/E30-bilagorna (`bilaga.py`).

## Referensparametrar (fryst på R, endast C-versioner av de 144 referensklippen)
- Referensklipp med komplett C och E28-rad: 144 av 144, konton: 72. `ref_mat.jsonl` sha256 004989893f534292c9ba574c9dceeb50000851e1a63c6d02f95baf46bbfff2cb.
- Transform: `F_j(x) = sum_i w_i [1(r_ij < x) + 0,5 * 1(r_ij = x)]`, `z_j = (F_j - mu_j) / sigma_j`; kontovikter lika (summa 1), fördelade lika över kontots klipp med giltigt värde för fältet, normaliserade över giltiga konton. Färre än 30 giltiga konton eller sigma=0 ger ingen kalibrerad axel.

| fält | klass | eps | giltiga konton | kalibrerad | mu | sigma | min | median | max |
|---|---|---|---|---|---|---|---|---|---|
| e28.langd | Ttid | 0.1 | 72 | ja | 0.500000 | 0.288660 | 5.04 | 19.25 | 58.54 |
| e28.skott_median | Ttid | 0.1 | 72 | ja | 0.500000 | 0.288650 | 0.13 | 3.255 | 52.92 |
| e28.skott_max | Ttid | 0.1 | 72 | ja | 0.500000 | 0.288662 | 1.17 | 7.185 | 52.92 |
| e28.forsta_byte | Ttid | 0.1 | 72 | ja | 0.500000 | 0.288653 | 0.03 | 3.53 | 52.92 |
| e28.forsta_ljud | Ttid | 0.1 | 72 | ja | 0.500000 | 0.128193 | 0 | 0 | 1.48 |
| e30.langd | Ttid | 0.1 | 72 | ja | 0.500000 | 0.288657 | 5.04 | 19.25 | 58.54 |
| e30.forsta_tal | Ttid | 0.1 | 65 | ja | 0.500000 | 0.285915 | 0 | 0.2 | 26.1 |
| e28.takt | Ttat | 0.02 | 72 | ja | 0.500000 | 0.286783 | 0 | 0.235 | 1.61 |
| e30.tal_per_s | Ttat | 0.005 | 72 | ja | 0.500000 | 0.286398 | 0 | 0.0925 | 0.458 |
| e28.rorelse | Tq | 0.2 | 72 | ja | 0.500000 | 0.288648 | 0.06 | 1.11 | 6.07 |
| e28.rorelse_2s | Tq | 0.2 | 72 | ja | 0.500000 | 0.288648 | 0.07 | 0.91 | 14.48 |
| e28.rorelse_kvot | Tq | 0.1 | 72 | ja | 0.500000 | 0.288646 | 0.02 | 0.815 | 17.98 |
| e28.byten | Gr | 0.0 | 72 | ja | 0.500000 | 0.286356 | 0 | 4.5 | 35 |
| e28.pauser | Gr | 0.0 | 72 | ja | 0.500000 | 0.235872 | 0 | 0 | 32 |
| e30.tal_segment | Gr | 0.0 | 72 | ja | 0.500000 | 0.281931 | 0 | 1.5 | 21 |
| e28.skott_max_andel | Ga | 0.02 | 72 | ja | 0.500000 | 0.286413 | 0.08 | 0.35 | 1 |
| e28.skott_cv | Ga | 0.05 | 72 | ja | 0.500000 | 0.286681 | 0 | 0.43 | 1.59 |
| e28.ljud_andel | Ga | 0.02 | 72 | ja | 0.500000 | 0.235989 | 0.27 | 1 | 1 |
| e30.tal_andel | Ga | 0.02 | 72 | ja | 0.500000 | 0.286399 | 0 | 0.524 | 1 |
| e28.byten_3s | Gf | 0.0 | 72 | ja | 0.500000 | 0.254935 | 0 | 0 | 12 |
| e28.lufs | L | 0.5 | 72 | ja | 0.500000 | 0.288650 | -37.9 | -20.75 | -6.3 |
| e28.lra | L | 0.5 | 72 | ja | 0.500000 | 0.288612 | 0.3 | 4.6 | 23.4 |
| e37.antal0 | Gp | 0.0 | 72 | ja | 0.500000 | 0.265010 | 0 | 1 | 4 |
| e37.antal1 | Gp | 0.0 | 72 | ja | 0.500000 | 0.257256 | 0 | 1 | 4 |
| e37.antal2 | Gp | 0.0 | 72 | ja | 0.500000 | 0.265502 | 0 | 1 | 5 |
| e37.antal3 | Gp | 0.0 | 72 | ja | 0.500000 | 0.265405 | 0 | 1 | 5 |
| e37.antal4 | Gp | 0.0 | 72 | ja | 0.500000 | 0.265012 | 0 | 1 | 5 |
| e37.antal5 | Gp | 0.0 | 72 | ja | 0.500000 | 0.263352 | 0 | 1 | 5 |
| e37.personer_medel | Gp | 0.0 | 72 | ja | 0.500000 | 0.285460 | 0 | 1 | 3.167 |
| e37.andel_minst_en | Gp | 0.0 | 72 | ja | 0.500000 | 0.277602 | 0 | 0.8333 | 1 |
| e37.andel_minst_tva | Gp | 0.0 | 72 | ja | 0.500000 | 0.259516 | 0 | 0 | 1 |
| e37.personer_max | Gp | 0.0 | 72 | ja | 0.500000 | 0.274763 | 0 | 1 | 5 |

## Dry run (mekanik, endast R-klipp, ingen testklipp)
- Dry-körningens mätvärden: `dry_test_mat.jsonl` sha256 6c77ec54acdf39f5ff893ee0e9660c9982f6632d50034b6a4915b7ce72e2e373. Dry-värden används i ingen dom.
