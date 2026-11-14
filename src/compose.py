# compose.py : montage fond uni + voix + sous-titres
# Usage : python src/compose.py les-bases-de-python
import subprocess
import sys
from pathlib import Path

from common import dossier_sortie

sujet = sys.argv[1]
dossier = dossier_sortie() / sujet
audios = sorted((dossier / "audio").glob("scene_*.wav"))

# 1. Liste des audios pour les mettre bout à bout
liste = dossier / "liste_audio.txt"
liste.write_text("".join(f"file '{a.resolve().as_posix()}'\n" for a in audios), encoding="utf-8")

voix = dossier / "voix.wav"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(liste), "-c", "copy", str(voix)], check=True)

# 2. Fond uni 1080x1920 + voix + sous-titres
# On lance FFmpeg depuis le dossier du sujet : plus simple pour le chemin du .ass sous Windows
subprocess.run([
    "ffmpeg", "-y",
    "-i", "personnage.mp4",
    "-i", "voix.wav",
    "-vf", "subtitles=sous_titres.ass",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-shortest",
    "video.mp4",
], check=True, cwd=dossier)

print(f"Terminé : {dossier / 'video.mp4'}")