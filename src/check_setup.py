"""Vérifie que tout est installé. Lance : python src/check_setup.py"""
import shutil
import subprocess
import sys

import requests

from common import ROOT, charger_config


def ligne(ok: bool | None, texte: str, aide: str = ""):
    icone = {True: "✅", False: "❌", None: "➖"}[ok]
    print(f"{icone} {texte}")
    if ok is False and aide:
        print(f"      → {aide}")


def main():
    cfg = charger_config()
    print("\n=== Vérification de l'installation ===\n")

    v = sys.version_info
    ligne(v >= (3, 10), f"Python {v.major}.{v.minor}",
          "Installe Python 3.11 (python.org) et coche « Add to PATH ».")
    if v >= (3, 12):
        print("      ⚠️  Python 3.11 recommandé : la voix (XTTS-v2) ne marche pas encore en 3.12+.")

    ligne(shutil.which("ffmpeg") is not None, "FFmpeg",
          "Dans PowerShell : winget install ffmpeg (puis rouvre le terminal).")

    modele = cfg["llm"]["modele"]
    try:
        r = requests.get(f'{cfg["llm"]["url"]}/api/tags', timeout=5)
        noms = [m["name"] for m in r.json().get("models", [])]
        ligne(True, "Ollama répond")
        ligne(any(n == modele or n.startswith(modele + ":") for n in noms),
              f"Modèle {modele}", f"Lance : ollama pull {modele}")
    except requests.RequestException:
        ligne(False, "Ollama répond", "Lance l'application Ollama (ollama.com).")

    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10).stdout.strip()
            ligne(True, f"Carte graphique : {out}")
        except Exception:
            ligne(None, "Carte graphique : non lisible")
    else:
        ligne(False, "Pilotes NVIDIA", "Mets à jour les pilotes sur nvidia.com.")

    print()
    manquants = [
        e[k] for e in cfg["personnage"]["emotions"].values() for k in ("ferme", "ouvert") if k in e
        if not (ROOT / "assets" / "character" / e[k]).exists()
    ]
    ligne(not manquants, "Images du personnage",
          "Lance : python src/prepare_assets.py")
    ligne((ROOT / cfg["voix"]["echantillon"]).exists(), "Échantillon de voix (ref.wav)",
          "À enregistrer, pas urgent (phase 3).")
    print()


if __name__ == "__main__":
    main()
