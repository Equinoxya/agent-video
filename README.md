# Agent IA – Vidéos dev TikTok

Agent 100 % local qui crée des vidéos dev avec ta voix clonée et ton personnage 2D.

## Installation (une seule fois)

1. Installe **Python 3.11** (python.org, coche « Add to PATH »)
2. Installe **Ollama** (ollama.com), puis dans un terminal : `ollama pull mistral-nemo`
3. Installe **FFmpeg** : `winget install ffmpeg`
4. Installe **Voicebox** (voicebox.sh), crée un profil de voix « Ma voix » avec ton échantillon,
   et télécharge le moteur **Qwen3-TTS 1.7B**
5. Dans PowerShell, dans ce dossier :

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src\prepare_assets.py
python src\check_setup.py
```

## Utilisation

**Voicebox doit être ouvert** pendant la génération de la voix.

```
.venv\Scripts\activate
python src\main.py "Les closures en JavaScript"
```

Les vidéos sont enregistrées **hors du dossier de l'agent**, dans le dossier `sortie` de `config.yaml`
(par défaut `Bureau\video-tiktok`). Le script arrive dans `<sortie>\<sujet>\scenes.json`.
Ensuite, lance les étapes une par une (`<sujet>` = nom du dossier, ex : `les-closures-en-javascript`) :

```
python src\tts.py <sujet>         # voix de chaque scène (Voicebox / Qwen3-TTS)
python src\align.py <sujet>       # timing mot par mot (faster-whisper)
python src\subtitles.py <sujet>   # sous-titres style TikTok
python src\character.py <sujet>   # personnage animé sur le fond bureau
python src\compose.py <sujet>     # montage final -> <sortie>\<sujet>\video.mp4
```

Pour une vidéo écrite à la main (ex : la présentation), crée directement
`<sortie>\<sujet>\scenes.json` et lance les 5 étapes.

## Réglages

Tout se règle dans `config.yaml` :

| Section | Ce qu'on y règle |
|---|---|
| `sortie` | Dossier où sont enregistrées les vidéos |
| `video` | Taille, fps, durée visée |
| `llm` | Modèle Ollama (actuellement `mistral-nemo`) |
| `style` | Ton et directives du script |
| `voix` | Moteur (`voicebox` ou `sopro` en secours), profil Voicebox, prononciation |
| `personnage` | Images de chaque émotion |

### Prononciation

Si la voix écorche un mot, ajoute-le sous `voix > prononciation` :

```yaml
"mot à écrire": "mot à prononcer"
```

Les sous-titres affichent toujours le texte de `scenes.json`, avec la bonne orthographe.

## Dossiers

| Dossier | Contenu |
|---|---|
| `assets/character/` | Poses du personnage (1080 px, fond transparent) |
| `assets/character/originals/` | Images d'origine (2048 px) |
| `assets/character/ancien/` | Anciennes versions du personnage (non publiées) |
| `assets/voice/` | Échantillon `ref.wav` pour Sopro (non publié, à ajouter toi-même) |
| `assets/bureau.jpg` | Fond de la vidéo (flouté automatiquement) |
| `assets/music/` | Musique libre de droits (à ajouter) |
| `prompts/` | Consignes données au modèle |
| `src/` | Le code |

## Poses du personnage

| Pose | Bouche qui parle ? |
|---|---|
| enjoue | oui (fermée + ouverte) |
| contrariee | non, bouche ouverte à refaire |
| sourire | non, il manque une version bouche ouverte |
| content | non, il manque une version bouche ouverte |
| interrogation | non, il manque une version bouche ouverte |

Pour l'instant, `character.py` utilise la pose **enjoue** sur toutes les scènes.
Quand les autres versions bouche ouverte seront prêtes, on remettra une émotion par scène.

## Avancement

- [x] Phase 1 : setup
- [x] Phase 2 : script (`script_gen.py`)
- [x] Phase 3 : voix (`tts.py`, Qwen3-TTS via Voicebox)
- [x] Phase 4 : timing (`align.py`) et sous-titres (`subtitles.py`)
- [x] Phase 5 : personnage (`character.py`, bouche synchronisée)
- [ ] Phase 6 : code à l'écran
- [x] Phase 7 : montage de base (`compose.py`)
- [ ] Phase 8 : finitions (musique, transitions, `main.py` qui enchaîne tout)
