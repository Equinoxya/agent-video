# character.py : anime le personnage selon la voix
# Usage : python src/character.py les-bases-de-python
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

from common import dossier_sortie

import numpy as np
import yaml
from PIL import Image,ImageFilter, ImageOps

FPS = 30
SEUIL = 0.15          # volume à partir duquel la bouche s'ouvre (à ajuster)
FOND = (30, 30, 46)   # même couleur que le fond de compose.py
def degrade(haut, bas, largeur=1080, hauteur=1920):
    """Crée un fond en dégradé vertical, de la couleur du haut vers celle du bas"""
    t = np.linspace(0, 1, hauteur)[:, None]
    couleurs = (1 - t) * np.array(haut) + t * np.array(bas)
    bande = np.repeat(couleurs[:, None, :], largeur, axis=1).astype(np.uint8)
    return Image.fromarray(bande, "RGB")


# Vert sapin en haut, bordeaux en bas
FOND_IMAGE = ImageOps.fit(
    Image.open("assets/bureau.jpg").convert("RGB"), (1080, 1920)
).filter(ImageFilter.GaussianBlur(6))
config = yaml.safe_load(open("config.yaml", encoding="utf-8"))
emotions = config["personnage"]["emotions"]
dossier_perso = Path("assets/character")

sujet = sys.argv[1]
dossier = dossier_sortie() / sujet
scenes = json.load(open(dossier / "scenes.json", encoding="utf-8"))["scenes"]


def charge(nom):
    """Charge une image du personnage (ou None si absente)"""
    return Image.open(dossier_perso / nom).convert("RGBA") if nom else None


def volumes(chemin):
    """Volume moyen de l'audio pour chaque image de la vidéo"""
    with wave.open(str(chemin)) as f:
        sr = f.getframerate()
        largeur = f.getsampwidth()      # 2 = 16 bits, 4 = 32 bits
        canaux = f.getnchannels()
        brut = f.readframes(f.getnframes())
    types = {1: np.uint8, 2: np.int16, 4: np.int32}
    data = np.frombuffer(brut, dtype=types[largeur]).astype(np.float32)
    data = data[::canaux]                       # garde un seul canal
    data = data / np.abs(data).max() if data.any() else data  # entre -1 et 1
    pas = sr / FPS
    nb_images = round(len(data) / pas)          # même durée que l'audio
    return [
        np.sqrt(np.mean(data[int(k * pas):int((k + 1) * pas)] ** 2))
        for k in range(nb_images)
    ]


# FFmpeg reçoit les images une par une et fabrique la vidéo
ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", "1080x1920", "-r", str(FPS), "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    str(dossier / "personnage.mp4"),
], stdin=subprocess.PIPE)

n = 0  # compteur d'images, pour la respiration
for i, scene in enumerate(scenes, start=1):
    # Émotion de la scène (sourire si inconnue)
        # Pour l'instant : enjouée partout (seule expression avec bouche ouverte)
    emo = emotions["enjoue"]
    ferme = charge(emo["ferme"])
    ouvert = charge(emo.get("ouvert"))  # None = la bouche ne bouge pas

    vols = volumes(dossier / "audio" / f"scene_{i:02d}.wav")
    # Lissage : moyenne sur 3 images pour éviter le clignotement
    vols = np.convolve(vols, np.ones(3) / 3, mode="same")
    # Seuil automatique : la moitié du volume moyen quand tu parles
    parle = vols[vols > 0.02]
    seuil = 0.5 * np.mean(parle) if len(parle) else SEUIL
    bouche_ouverte = False
    duree_etat = 0
    for vol in vols:
        voulu = vol > seuil
        # On garde chaque état au moins 3 images (0,1 s) avant de changer
        if voulu != bouche_ouverte and duree_etat >= 2:
            bouche_ouverte = voulu
            duree_etat = 0
        duree_etat += 1

        img = ouvert if (ouvert and bouche_ouverte) else ferme
        dy = int(6 * math.sin(n / FPS * 2))
        frame = FOND_IMAGE.copy()
        frame.paste(img, (0, 1920 - 1080 + dy), img)
        ffmpeg.stdin.write(frame.tobytes())
        n += 1

ffmpeg.stdin.close()
ffmpeg.wait()
print(f"Terminé : {dossier / 'personnage.mp4'}")