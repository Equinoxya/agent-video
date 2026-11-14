# align.py : timing mot par mot de chaque scène avec faster-whisper
# Usage : python src/align.py les-bases-de-python
import json
import sys
from pathlib import Path

from common import dossier_sortie

from faster_whisper import WhisperModel

# Dossier du sujet
sujet = sys.argv[1]
dossier = dossier_sortie() / sujet
dossier_audio = dossier / "audio"

# Modèle "small" sur le CPU : on laisse le GPU tranquille
modele = WhisperModel("small", device="cpu", compute_type="int8")

resultat = []
for audio in sorted(dossier_audio.glob("scene_*.wav")):
    print(f"Analyse de {audio.name}...")
    segments, _ = modele.transcribe(str(audio), language="fr", word_timestamps=True)

    # On garde chaque mot avec son début et sa fin (en secondes)
    mots = []
    for segment in segments:
        for mot in segment.words:
            mots.append({
                "mot": mot.word.strip(),
                "debut": round(mot.start, 2),
                "fin": round(mot.end, 2),
            })
    resultat.append({"audio": audio.name, "mots": mots})

# Sauvegarde dans timings.json
sortie = dossier / "timings.json"
json.dump(resultat, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Terminé : {sortie}")