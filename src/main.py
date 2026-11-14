"""Point d'entrée : crée une vidéo à partir d'un sujet.

    python src/main.py "Les closures en JavaScript"

Étapes déjà actives : 1 (script).
Les autres s'ajouteront phase après phase.
"""
import argparse

from common import charger_config
from script_gen import generer, sauvegarder
from status import maj, reset
from agent_status import envoyer_statut

def main():
    p = argparse.ArgumentParser(description="Agent IA de création de vidéos dev.")
    p.add_argument("sujet", help="Le sujet de la vidéo")
    args = p.parse_args()
    envoyer_statut("agent_videos", "en_cours", f"Sujet : {args.sujet}")
    try:
        cfg = charger_config()

        reset(args.sujet)
        maj("script", "en_cours", "Écriture du script…")
        envoyer_statut("agent_videos", "en_cours", "Écriture du script")
        data = generer(args.sujet, cfg)
        maj("script", "ok", "Script terminé")
        chemin = sauvegarder(data, args.sujet)

        print(f'\n🎬 "{data["titre"]}"')
        for i, s in enumerate(data["scenes"], 1):
            print(f'  {i}. [{s["emotion"]}] {s["texte"]}')
        print(f"\nScript enregistré : {chemin}")

        envoyer_statut("agent_videos", "termine", data["titre"])
    except Exception as e:
        envoyer_statut("agent_videos", "erreur", str(e))
        raise
    cfg = charger_config()

    # 1. Script (phase 2)
    reset(args.sujet)
    maj("script", "en_cours", "Écriture du script…")
    data = generer(args.sujet, cfg)
    maj("script", "ok", "Script terminé")
    chemin = sauvegarder(data, args.sujet)
    print(f'\n🎬 "{data["titre"]}"')
    for i, s in enumerate(data["scenes"], 1):
        print(f'  {i}. [{s["emotion"]}] {s["texte"]}')
    print(f"\nScript enregistré : {chemin}")

    # 2. Voix            -> phase 3  (tts.py)
    # 3. Timestamps      -> phase 4  (align.py)
    # 4. Personnage      -> phase 5  (character.py)
    # 5. Code à l'écran  -> phase 6  (code_render.py)
    # 6. Montage         -> phase 7  (compose.py)


if __name__ == "__main__":
    main()
