"""Point d'entrée : crée une vidéo complète à partir d'un sujet.

    python src/main.py "Les closures en JavaScript"

Reprendre une vidéo existante (ex : la présentation écrite à la main),
à partir d'une étape précise :

    python src/main.py --dossier presentation
    python src/main.py --dossier presentation --depuis sous-titres

Étapes : script -> voix -> timing -> sous-titres -> personnage -> montage
Voicebox doit être ouvert pour l'étape "voix".
"""
import argparse
import subprocess
import sys

from common import ROOT, charger_config, dossier_sortie
from script_gen import generer, sauvegarder
from status import maj, reset

# Statut pour le dashboard multi-agents : facultatif.
# Si le module agent_status n'est pas trouvé, on continue sans.
try:
    from agent_status import envoyer_statut
except ImportError:
    def envoyer_statut(*args, **kwargs):
        pass

# (nom de l'étape, script à lancer, nom dans status.json)
ETAPES = [
    ("voix", "tts.py", "voix"),
    ("timing", "align.py", "timing"),
    ("sous-titres", "subtitles.py", "timing"),
    ("personnage", "character.py", "personnage"),
    ("montage", "compose.py", "montage"),
]


def ecrire_script(sujet):
    """Étape 1 : le LLM écrit le script, renvoie le nom du dossier créé"""
    maj("script", "en_cours", "Écriture du script…")
    envoyer_statut("agent_videos", "en_cours", "Écriture du script")
    data = generer(sujet, charger_config())
    chemin = sauvegarder(data, sujet)
    maj("script", "ok", "Script terminé")

    print(f'\n🎬 "{data["titre"]}"')
    for i, s in enumerate(data["scenes"], 1):
        print(f'  {i}. [{s["emotion"]}] {s["texte"]}')
    print(f"\nScript enregistré : {chemin}\n")
    return chemin.parent.name


def lancer_etape(nom, script, cle, dossier):
    """Lance un script de src/ sur le dossier de la vidéo"""
    print(f"\n▶ {nom}…")
    maj(cle, "en_cours", f"{nom}…")
    envoyer_statut("agent_videos", "en_cours", nom)
    # cwd=ROOT : les scripts lisent config.yaml et assets/ depuis le dossier de l'agent
    subprocess.run([sys.executable, str(ROOT / "src" / script), dossier],
                   cwd=ROOT, check=True)
    maj(cle, "ok", f"{nom} terminé")


def main():
    p = argparse.ArgumentParser(description="Agent IA de création de vidéos dev.")
    p.add_argument("sujet", nargs="?", help="Le sujet de la vidéo (nouveau script)")
    p.add_argument("--dossier", help="Reprendre une vidéo existante (nom du dossier)")
    p.add_argument("--depuis", choices=[e[0] for e in ETAPES], default="voix",
                   help="Étape de départ quand on reprend une vidéo")
    args = p.parse_args()
    if not args.sujet and not args.dossier:
        p.error("donne un sujet, ou --dossier pour reprendre une vidéo")

    envoyer_statut("agent_videos", "en_cours", args.sujet or args.dossier)
    cle = "script"  # étape en cours, pour signaler une erreur au bon endroit
    try:
        reset(args.sujet or args.dossier)

        # 1. Script (seulement pour un nouveau sujet)
        if args.dossier:
            dossier, depart = args.dossier, args.depuis
        else:
            dossier, depart = ecrire_script(args.sujet), "voix"

        # 2 à 6. Voix, timing, sous-titres, personnage, montage
        noms = [e[0] for e in ETAPES]
        for nom, script, cle in ETAPES[noms.index(depart):]:  # cle = étape en cours
            lancer_etape(nom, script, cle, dossier)

        video = dossier_sortie() / dossier / "video.mp4"
        print(f"\n✅ Vidéo prête : {video}")
        envoyer_statut("agent_videos", "termine", str(video))
    except Exception as e:
        maj(cle, "erreur", str(e))
        envoyer_statut("agent_videos", "erreur", str(e))
        raise


if __name__ == "__main__":
    main()
