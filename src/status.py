import json, time
from common import dossier_sortie

FICHIER = dossier_sortie() / "status.json"
ETAPES = ["script", "voix", "timing", "personnage", "code", "montage"]

def maj(etape, etat, message=""):
    """etat : 'attente', 'en_cours', 'ok' ou 'erreur'"""
    data = json.loads(FICHIER.read_text(encoding="utf-8")) if FICHIER.exists() else {}
    data.setdefault("etapes", {e: "attente" for e in ETAPES})
    data["etapes"][etape] = etat
    data["message"] = message
    data["maj"] = time.strftime("%H:%M:%S")
    FICHIER.parent.mkdir(exist_ok=True)
    FICHIER.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def reset(sujet):
    FICHIER.write_text(json.dumps({"sujet": sujet, "etapes": {e: "attente" for e in ETAPES},
                                   "message": "Démarrage", "debut": time.strftime("%H:%M:%S")},
                                  ensure_ascii=False, indent=2), encoding="utf-8")