# Agent IA – Vidéos dev TikTok

Agent local (Ollama) qui crée des vidéos avec ta voix et ton personnage.

## Installation (une seule fois)

1. Installe **Python 3.11** (python.org, coche « Add to PATH »)
2. Installe **Ollama** (ollama.com), puis dans un terminal : `ollama pull qwen2.5:3b`
3. Installe **FFmpeg** : `winget install ffmpeg`
4. Dans PowerShell, dans ce dossier :

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src\prepare_assets.py
python src\check_setup.py
```

Quand tout est ✅ (sauf la voix pour l'instant), tu es prêt.

## Utilisation

```
.venv\Scripts\activate
python src\main.py "Les closures en JavaScript"
```

Le script est enregistré dans `output\<sujet>\scenes.json`.

## Réglages

Tout se règle dans `config.yaml` : durée, ton, directives, modèle, poses du personnage.

## Dossiers

| Dossier | Contenu |
|---|---|
| `assets/character/` | Poses du personnage (1080 px, fond transparent) |
| `assets/character/originals/` | Tes images d'origine (2048 px) |
| `assets/voice/` | Ton échantillon `ref.wav` (à ajouter) |
| `assets/music/` | Musique libre de droits (à ajouter) |
| `prompts/` | Consignes données au modèle |
| `src/` | Le code |
| `output/` | Les vidéos et scripts générés |

## Poses du personnage

| Pose | Bouche qui parle ? |
|---|---|
| enjoue | oui (fermée + ouverte) |
| contrariee | oui (fermée + ouverte) |
| sourire | non, il manque une version bouche ouverte |
| content | non, il manque une version bouche ouverte |
| interrogation | non, il manque une version bouche ouverte |

Pour ces 3 poses, on dessinera la bouche ouverte plus tard si tu veux. En attendant, le personnage bougera légèrement pendant qu'il parle.

## Avancement

- [x] Phase 1 : setup
- [x] Phase 2 : script (`script_gen.py`)
- [ ] Phase 3 : voix
- [ ] Phase 4 : timing
- [ ] Phase 5 : personnage
- [ ] Phase 6 : code à l'écran
- [ ] Phase 7 : montage
