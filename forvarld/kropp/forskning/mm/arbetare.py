"""Python 3.8-arbetare: ett JSON-uppdrag per stdinrad, ett JSON-svar per stdoutrad."""
import contextlib, io, json, os, sys, time, traceback
from pathlib import Path

# IsaacGym skriver även direkt till fd 1. Behåll originalröret för protokollet och
# styr därefter hela fd 1 till stderr, inte bara Pythons sys.stdout.
PROTOKOLL = os.fdopen(os.dup(sys.stdout.fileno()), 'w', buffering=1, encoding='utf-8')
sys.stdout.flush(); os.dup2(sys.stderr.fileno(), sys.stdout.fileno())


def svar(obj):
    PROTOKOLL.write(json.dumps(obj, ensure_ascii=False) + '\n'); PROTOKOLL.flush()


def main():
    # Import, simulatorbygge och checkpointsutskrifter får aldrig hamna i radprotokollet.
    with contextlib.redirect_stdout(sys.stderr):
        from kor_mm import MMKornare, EXEMPEL
        kornare = MMKornare(EXEMPEL, {'villkor': []})
    for rad in sys.stdin:
        t0 = time.time(); logg = io.StringIO()
        try:
            uppdrag = json.loads(rad); V = uppdrag['villkor']
            with contextlib.redirect_stdout(logg):
                kornare.kor(uppdrag['inn'], uppdrag['ut'], V)
            ok = Path(uppdrag['ut']).exists()
            svar({'ok': ok, 's': round(time.time() - t0, 3), 'logg': logg.getvalue()})
        except Exception:
            logg.write(traceback.format_exc())
            svar({'ok': False, 's': round(time.time() - t0, 3), 'logg': logg.getvalue()})


if __name__ == '__main__': main()
