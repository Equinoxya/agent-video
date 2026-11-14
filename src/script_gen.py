"""Étape 1 : sujet + directives -> scenes.json (via Ollama).

Utilisation :
    python src/script_gen.py "Les closures en JavaScript"
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import requests

from common import ROOT, charger_config

MOTS_PAR_SECONDE = 2.5   # débit de parole moyen en français


def slug(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte[:50] or "video"


def schema_json(emotions: list[str]) -> dict:
    """Schéma que le modèle doit respecter (Ollama 'structured outputs')."""
    return {
        "type": "object",
        "properties": {
            "titre": {"type": "string"},
            # Champ obligatoire : force le modèle à écrire un exemple de code.
            "exemple_code": {
                "type": "object",
                "properties": {
                    "langage": {"type": "string"},
                    "contenu": {"type": "string", "minLength": 1},
                },
                "required": ["langage", "contenu"],
            },
            "scenes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "texte": {"type": "string", "minLength": 1},
                        "emotion": {"type": "string", "enum": emotions},
                        "code": {
                            "type": "object",
                            "properties": {
                                "langage": {"type": "string"},
                                "contenu": {"type": "string"},
                            },
                            "required": ["langage", "contenu"],
                        },
                    },
                    "required": ["texte", "emotion"],
                },
            },
        },
        "required": ["titre", "exemple_code", "scenes"],
    }


def placer_exemple_code(data: dict) -> dict:
    """Retire les scènes vides, puis si aucune scène n'a de code,
    place "exemple_code" sur la 2e scène (juste après l'accroche)."""
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        return data
    data["scenes"] = [s for s in data["scenes"] if str(s.get("texte", "")).strip()]
    exemple = data.pop("exemple_code", None)
    deja = any(isinstance(s.get("code"), dict) and str(s["code"].get("contenu", "")).strip()
               for s in data["scenes"])
    if not deja and isinstance(exemple, dict) and str(exemple.get("contenu", "")).strip() \
            and data["scenes"]:
        data["scenes"][min(1, len(data["scenes"]) - 1)]["code"] = exemple
    return data


def construire_prompt(cfg: dict) -> str:
    duree = cfg["video"]["duree_cible_s"]
    emotions = cfg["personnage"]["emotions"]
    aide = "\n".join(f'  - {nom} : {e["usage"]}' for nom, e in emotions.items())
    valeurs = {
        "langue": cfg["style"]["langue"],
        "ton": cfg["style"]["ton"],
        "directives": cfg["style"]["directives"].strip(),
        "duree": str(duree),
        "mots": str(int(duree * MOTS_PAR_SECONDE)),
        "nb_min": str(max(3, duree // 12)),
        "nb_max": str(max(4, duree // 6)),
        "emotions_aide": aide,
    }
    texte = (ROOT / "prompts" / "script.txt").read_text(encoding="utf-8")
    for cle, valeur in valeurs.items():
        texte = texte.replace("{" + cle + "}", valeur)
    return texte


def valider(data: dict, emotions: list[str], duree_cible: float | None = None) -> list[str]:
    """Renvoie la liste des problèmes (vide = tout est bon)."""
    problemes = []
    if not isinstance(data, dict) or not str(data.get("titre", "")).strip():
        problemes.append("titre manquant")
    scenes = data.get("scenes") if isinstance(data, dict) else None
    if not isinstance(scenes, list) or len(scenes) < 2:
        return problemes + ["il faut au moins 2 scènes"]
    mots = 0
    a_du_code = False
    for i, s in enumerate(scenes, 1):
        texte = str(s.get("texte", ""))
        mots += len(texte.split())
        if not texte.strip():
            problemes.append(f"scène {i} : texte vide")
        if s.get("emotion") not in emotions:
            problemes.append(f"scène {i} : émotion inconnue ({s.get('emotion')})")
        code = s.get("code")
        if isinstance(code, dict) and str(code.get("contenu", "")).strip():
            a_du_code = True
    if not a_du_code:
        problemes.append("aucun exemple de code")
    if duree_cible:
        duree = mots / MOTS_PAR_SECONDE
        if duree > duree_cible * 1.5:
            problemes.append(f"trop long (~{duree:.0f} s pour {duree_cible} s visées)")
    return problemes


BLOC_CODE = re.compile(r"```(\w*)\s*\n?(.*?)```", re.S)


def sortir_code_du_texte(data: dict) -> dict:
    """Le modèle recopie parfois le code dans le texte parlé : on le déplace
    dans le champ "code" et on retire les backticks (lus par la voix)."""
    for s in data.get("scenes", []) if isinstance(data, dict) else []:
        texte = str(s.get("texte", ""))
        bloc = BLOC_CODE.search(texte)
        if bloc:
            code = s.get("code")
            if not isinstance(code, dict) or not str(code.get("contenu", "")).strip():
                s["code"] = {"langage": bloc.group(1) or "", "contenu": bloc.group(2).strip()}
            texte = BLOC_CODE.sub("", texte).strip() or "Regarde cet exemple."
        s["texte"] = texte.replace("`", "")
    return data


def nettoyer(data: dict) -> dict:
    """Ajoute la durée estimée, retire les blocs de code vides."""
    for s in data["scenes"]:
        s["texte"] = s["texte"].strip()
        code = s.get("code")
        if not code or not str(code.get("contenu", "")).strip():
            s["code"] = None
        s["duree_estimee"] = round(len(s["texte"].split()) / MOTS_PAR_SECONDE, 1)
    data["duree_estimee_totale"] = round(sum(s["duree_estimee"] for s in data["scenes"]), 1)
    return data


def appeler_ollama(cfg: dict, sujet: str, systeme: str, emotions: list[str]) -> dict:
    llm = cfg["llm"]
    try:
        r = requests.post(
            f'{llm["url"]}/api/chat',
            json={
                "model": llm["modele"],
                "messages": [
                    {"role": "system", "content": systeme},
                    {"role": "user", "content": f"Sujet de la vidéo : {sujet}"},
                ],
                "stream": True,   # pour afficher la progression
                "format": schema_json(emotions),
                "keep_alive": 0,  # libère la VRAM juste après (utile pour la voix)
                "options": {
                    "temperature": llm["temperature"],
                    # Petit contexte = le modèle tient entier dans la VRAM (sinon
                    # Ollama alloue 16k tokens et une partie tourne sur le CPU).
                    "num_ctx": llm.get("contexte", 4096),
                    # Garde-fou : coupe si le modèle part en boucle.
                    "num_predict": llm.get("max_tokens", 2000),
                },
            },
            stream=True,
            timeout=(10, 300),  # 10 s pour se connecter, 300 s max sans rien recevoir
        )
    except requests.ConnectionError:
        sys.exit("❌ Ollama ne répond pas. Lance l'application Ollama puis recommence.")
    if r.status_code == 404:
        sys.exit(f'❌ Modèle introuvable. Lance : ollama pull {llm["modele"]}')
    r.raise_for_status()

    morceaux: list[str] = []
    for ligne in r.iter_lines():
        if not ligne:
            continue
        d = json.loads(ligne)
        if "error" in d:
            sys.exit(f"❌ Erreur Ollama : {d['error']}")
        morceaux.append(d.get("message", {}).get("content", ""))
        if len(morceaux) % 20 == 0:
            print(".", end="", flush=True)
        if d.get("done"):
            print(f" ({d.get('eval_count', '?')} tokens)", flush=True)
            if d.get("done_reason") == "length":
                raise json.JSONDecodeError("réponse tronquée", "", 0)
    return json.loads("".join(morceaux))


def generer(sujet: str, cfg: dict | None = None) -> dict:
    cfg = cfg or charger_config()
    emotions = list(cfg["personnage"]["emotions"])
    systeme = construire_prompt(cfg)
    problemes: list[str] = []
    for essai in range(1, cfg["llm"]["essais"] + 1):
        print(f"📝 Génération du script (essai {essai})…")
        try:
            data = appeler_ollama(cfg, sujet, systeme, emotions)
        except json.JSONDecodeError:
            problemes = ["réponse JSON illisible"]
            continue
        data = sortir_code_du_texte(data)
        data = placer_exemple_code(data)
        problemes = valider(data, emotions, cfg["video"]["duree_cible_s"])
        if not problemes:
            return nettoyer(data)
        print("   ⚠️ ", "; ".join(problemes))
    sys.exit(f"❌ Script invalide après {cfg['llm']['essais']} essais : {problemes}")


def sauvegarder(data: dict, sujet: str) -> Path:
    dossier = ROOT / "output" / slug(sujet)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / "scenes.json"
    chemin.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin


def main():
    p = argparse.ArgumentParser(description="Génère le script d'une vidéo.")
    p.add_argument("sujet", help='ex. "Les closures en JavaScript"')
    args = p.parse_args()
    data = generer(args.sujet)
    chemin = sauvegarder(data, args.sujet)
    print(f'✅ "{data["titre"]}" : {len(data["scenes"])} scènes, '
          f'~{data["duree_estimee_totale"]} s')
    print(f"   Fichier : {chemin}")


if __name__ == "__main__":
    main()
