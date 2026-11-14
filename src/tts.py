# tts.py : génère la voix de chaque scène
# Moteur au choix dans config.yaml (voix > moteur) :
#   "voicebox" -> Qwen3-TTS via l'API locale de Voicebox (Voicebox doit être ouvert)
#   "sopro"    -> Sopro en ligne de commande (ancien moteur, gardé en secours)
# Usage : python src/tts.py les-bases-de-python
import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

from common import dossier_sortie

import requests
import yaml

# Lecture de la config
config = yaml.safe_load(open("config.yaml", encoding="utf-8"))
voix = config.get("voix", {})
moteur = voix.get("moteur", "voicebox")

# Dossier du sujet (ex : output/les-bases-de-python)
sujet = sys.argv[1]
dossier = dossier_sortie() / sujet
scenes = json.load(open(dossier / "scenes.json", encoding="utf-8"))["scenes"]
dossier_audio = dossier / "audio"
dossier_audio.mkdir(exist_ok=True)


# ------------------------------------------------------------
#  Voicebox (Qwen3-TTS)
# ------------------------------------------------------------
vb = voix.get("voicebox", {})
URL = vb.get("url", "http://127.0.0.1:17493")


def profil_voicebox():
    """Trouve l'identifiant du profil de voix à partir de son nom"""
    try:
        profils = requests.get(f"{URL}/profiles", timeout=10).json()
    except requests.ConnectionError:
        raise SystemExit("❌ Voicebox ne répond pas : ouvre l'appli Voicebox puis relance.")
    nom = vb.get("profil", "Ma voix")
    for p in profils:
        if p["name"] == nom:
            return p["id"]
    raise SystemExit(f"❌ Profil « {nom} » introuvable dans Voicebox.")


def voicebox(texte, sortie, profil_id):
    """Demande l'audio à Voicebox, attend la fin, puis télécharge le fichier"""
    demande = {
        "profile_id": profil_id,
        "text": texte,
        "language": "fr",
        "engine": vb.get("engine", "qwen"),
        "model_size": vb.get("model_size", "1.7B"),
    }
    if vb.get("instruct"):
        demande["instruct"] = vb["instruct"]   # ex : "ton enjoué et chaleureux"

    rep = requests.post(f"{URL}/generate", json=demande, timeout=1800)
    rep.raise_for_status()
    gen = rep.json()

    # On attend que la génération soit terminée
    while gen.get("status") not in ("completed", "failed", "error"):
        time.sleep(2)
        gen = requests.get(f"{URL}/history/{gen['id']}", timeout=30).json()
    if gen.get("status") != "completed":
        raise SystemExit(f"❌ Voicebox a échoué : {gen.get('error')}")

    audio = requests.get(f"{URL}/audio/{gen['id']}", timeout=60)
    audio.raise_for_status()
    sortie.write_bytes(audio.content)


# ------------------------------------------------------------
#  Sopro (secours)
# ------------------------------------------------------------
def sopro(texte, sortie):
    """Ancien moteur : découpe sur la ponctuation et recolle avec des pauses"""
    echantillon = voix.get("echantillon", "assets/voice/ref.wav")
    temperature = voix.get("temperature", 0.8)
    morceaux = [m.strip() for m in re.split(r"(?<=[.,!?;:…])\s+", texte) if m.strip()]
    pauses = {",": 0.15, ";": 0.2, ":": 0.2}  # sinon 0.35 s après . ! ? …

    sons = []
    for k, morceau in enumerate(morceaux):
        tmp = dossier_audio / f"tmp_{k}.wav"
        subprocess.run([
            "soprotts", morceau, "--ref", echantillon, "--lang", "fr",
            "--temperature", str(temperature), "--device", "cuda", "--out", str(tmp),
        ], check=True)
        with wave.open(str(tmp)) as f:
            params = f.getparams()
            sons.append(f.readframes(f.getnframes()))
        if k < len(morceaux) - 1:
            nb = int(params.framerate * pauses.get(morceau[-1], 0.35))
            sons.append(b"\x00" * nb * params.sampwidth * params.nchannels)
        tmp.unlink()

    with wave.open(str(sortie), "wb") as f:
        f.setparams(params)
        f.writeframes(b"".join(sons))


# ------------------------------------------------------------
#  Boucle principale : une génération par scène
# ------------------------------------------------------------
profil_id = profil_voicebox() if moteur == "voicebox" else None

for i, scene in enumerate(scenes, start=1):
    sortie = dossier_audio / f"scene_{i:02d}.wav"
    print(f"Scène {i}/{len(scenes)} ({moteur}) : {scene['texte'][:40]}...")

    # Remplace les mots mal prononcés (le sous-titre garde le vrai texte)
    texte = scene["texte"]
    for mot, phonetique in voix.get("prononciation", {}).items():
        texte = texte.replace(mot, phonetique)

    if moteur == "voicebox":
        voicebox(texte, sortie, profil_id)
    else:
        sopro(texte, sortie)

print(f"Terminé : {len(scenes)} audios dans {dossier_audio}")
