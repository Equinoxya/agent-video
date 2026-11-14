"""Outils communs : chemins, configuration."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# Évite les erreurs d'accents / emojis dans le terminal Windows
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8")
    except Exception:
        pass


def charger_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dossier_sortie() -> Path:
    """Dossier où sont enregistrées les vidéos (config.yaml > sortie).
    Un chemin relatif part du dossier de l'agent."""
    chemin = Path(charger_config().get("sortie", "output"))
    if not chemin.is_absolute():
        chemin = ROOT / chemin
    chemin.mkdir(parents=True, exist_ok=True)
    return chemin
