"""Prépare les images du personnage : redimensionne les originaux (2048 px)
en 1080 px, fond transparent conservé.

Utilisation : python src/prepare_assets.py
"""
from PIL import Image

from common import ROOT

TAILLE = 1080


def main():
    src = ROOT / "assets" / "character" / "originals"
    dst = ROOT / "assets" / "character"
    fichiers = sorted(src.glob("*.png"))
    if not fichiers:
        raise SystemExit("❌ Aucune image dans assets/character/originals/")
    for f in fichiers:
        img = Image.open(f).convert("RGBA")
        img = img.resize((TAILLE, TAILLE), Image.LANCZOS)
        img.save(dst / f.name, optimize=True)
        print(f"✅ {f.name}  ->  {TAILLE}x{TAILLE}")


if __name__ == "__main__":
    main()
