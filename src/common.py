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
