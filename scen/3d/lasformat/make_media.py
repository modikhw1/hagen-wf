#!/usr/bin/env python3
"""Skapa original | genererat | kropp projicerad med befintliga renderbilder."""
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "ingest" / "ut" / "notan-tagningar" / "klipp" / "S4.mp4"


def main() -> None:
    for fmt in "ABC":
        generated = ROOT / "genererat" / f"{fmt}_01" / "video_30fps.mp4"
        outdir = ROOT / "ut" / fmt
        video = outdir / "sida_vid_sida.mp4"
        still = outdir / "sida_vid_sida_f0045.jpg"
        filt = (
            "[0:v]scale=366:650,pad=480:832:57:0:color=black,setsar=1[orig];"
            "[1:v]scale=480:832,setsar=1,split[g1][g2];"
            "[2:v]scale=480:832,format=rgba,colorchannelmixer=aa=0.55[body];"
            "[g2][body]overlay=shortest=1[projected];"
            "[orig][g1][projected]hstack=3[v]"
        )
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(ORIGINAL), "-i", str(generated),
                "-framerate", "30", "-start_number", "0", "-i", str(outdir / "render" / "f%04d.png"),
                "-filter_complex", filt, "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
                "-profile:v", "main", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac",
                "-ac", "2", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(video),
            ],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", "1.5", "-i", str(video), "-frames:v", "1", str(still)],
            check=True,
        )
        print(fmt, video, still)


if __name__ == "__main__":
    main()
