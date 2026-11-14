# subtitles.py : sous-titres style TikTok
# Le TEXTE vient de scenes.json (ton script, bonne orthographe),
# le TIMING vient de timings.json (faster-whisper).
# Usage : python src/subtitles.py les-bases-de-python
import difflib
import json
import re
import sys
import wave
from pathlib import Path

MOTS_PAR_GROUPE = 3          # nombre de mots affichés en même temps
JAUNE = "{\\c&H00FFFF&}"     # couleur du mot en cours (format ASS : BGR)
BLANC = "{\\c&HFFFFFF&}"

sujet = sys.argv[1]
dossier = Path("output") / sujet
timings = json.load(open(dossier / "timings.json", encoding="utf-8"))
scenes = json.load(open(dossier / "scenes.json", encoding="utf-8"))["scenes"]


def temps_ass(s):
    """Convertit des secondes en format ASS : h:mm:ss.cc"""
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def duree_audio(chemin):
    """Durée d'un fichier WAV, en secondes"""
    with wave.open(str(chemin)) as f:
        return f.getnframes() / f.getframerate()


def normalise(mot):
    """Mot sans ponctuation ni majuscules, pour comparer"""
    return re.sub(r"[^\w]", "", mot.lower())


def fusionne(mots):
    """Recolle les morceaux coupés par Whisper : c + 'est -> c'est, abonne + -toi"""
    res = []
    for m in mots:
        if res and m["mot"][:1] in "'’-":
            res[-1] = {"mot": res[-1]["mot"] + m["mot"],
                       "debut": res[-1]["debut"], "fin": m["fin"]}
        else:
            res.append(dict(m))
    return res


def aligne(texte, mots_whisper):
    """Donne à chaque mot du script le timing du mot entendu par Whisper"""
    # Découpe en mots ; ":", "?", "!" seuls restent collés au mot d'avant
    script = []
    for m in texte.split():
        if script and not normalise(m):
            script[-1] += " " + m   # espace insécable
        else:
            script.append(m)
    entendus = fusionne(mots_whisper)
    temps = [None] * len(script)

    comparaison = difflib.SequenceMatcher(
        None, [normalise(m) for m in script],
        [normalise(m["mot"]) for m in entendus], autojunk=False)
    for tag, i1, i2, j1, j2 in comparaison.get_opcodes():
        if tag == "equal":
            # Même mot des deux côtés : on prend son timing
            for k in range(i2 - i1):
                temps[i1 + k] = (entendus[j1 + k]["debut"], entendus[j1 + k]["fin"])
        elif tag == "replace":
            # Mots différents (ex : "dépit" entendu "des pieds") :
            # on répartit le temps entendu sur les mots du script
            debut, fin = entendus[j1]["debut"], entendus[j2 - 1]["fin"]
            n = i2 - i1
            for k in range(n):
                temps[i1 + k] = (debut + (fin - debut) * k / n,
                                 debut + (fin - debut) * (k + 1) / n)

    # Mots du script que Whisper n'a pas entendus : on les place entre leurs voisins
    for k in range(len(temps)):
        if temps[k] is None:
            avant = temps[k - 1][1] if k > 0 and temps[k - 1] else 0.0
            apres = next((t[0] for t in temps[k + 1:] if t), avant + 0.3)
            temps[k] = (avant, max(apres, avant + 0.1))

    return [{"mot": m, "debut": d, "fin": f} for m, (d, f) in zip(script, temps)]


# En-tête : texte gros, gras, contour noir, en haut de l'écran
entete = """[Script Info]
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, Outline, Alignment, MarginV
Style: TikTok,Arial,90,&H00FFFFFF,&H00000000,1,6,8,400

[Events]
Format: Layer, Start, End, Style, Text
"""

lignes = []
decalage = 0.0  # les scènes se suivent : on décale chaque scène

for scene, timing in zip(scenes, timings):
    mots = aligne(scene["texte"], timing["mots"])

    for g in range(0, len(mots), MOTS_PAR_GROUPE):
        groupe = mots[g:g + MOTS_PAR_GROUPE]
        for i, mot in enumerate(groupe):
            # Le mot reste affiché jusqu'au début du mot suivant (pas de clignotement)
            idx = g + i
            fin = mots[idx + 1]["debut"] if idx + 1 < len(mots) else mot["fin"]
            texte = " ".join(
                (JAUNE if j == i else BLANC) + m["mot"].upper()
                for j, m in enumerate(groupe)
            )
            lignes.append(
                f"Dialogue: 0,{temps_ass(decalage + mot['debut'])},"
                f"{temps_ass(decalage + fin)},TikTok,{texte}"
            )
    decalage += duree_audio(dossier / "audio" / timing["audio"])

sortie = dossier / "sous_titres.ass"
sortie.write_text(entete + "\n".join(lignes), encoding="utf-8")
print(f"Terminé : {sortie}")
