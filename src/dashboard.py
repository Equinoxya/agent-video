from flask import Flask, jsonify
import json
from status import FICHIER
import subprocess, sys
from flask import request
from common import ROOT
app = Flask(__name__)

PAGE = """<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Open space – Agent vidéo</title>
<style>
body{margin:0;font-family:monospace;background:#2b2438;color:#fff}
h1{text-align:center;color:#ffd27f;margin:16px}
#lanceur{text-align:center;margin-bottom:10px}
#lanceur input{padding:8px;width:300px;border-radius:6px;border:none}
#lanceur button{padding:8px 16px;border-radius:6px;border:none;background:#ffd27f;cursor:pointer}
#bureau{display:grid;grid-template-columns:repeat(3,220px);gap:30px;justify-content:center;
 padding:30px;background:repeating-linear-gradient(45deg,#3a3150 0 20px,#40375a 20px 40px)}
.poste{background:#5a4a3a;border:4px solid #3d3026;border-radius:8px;height:150px;position:relative}
.ecran{position:absolute;top:12px;left:60px;width:100px;height:55px;background:#111;border:3px solid #888;
 font-size:11px;color:#6f6;padding:3px;overflow:hidden}
.perso{position:absolute;bottom:10px;left:85px;font-size:42px}
.nom{position:absolute;bottom:-26px;width:100%;text-align:center;color:#ffd27f}
.en_cours .perso{animation:tape .3s infinite alternate}
.en_cours .ecran{background:#123;box-shadow:0 0 12px #6cf}
.ok .ecran{color:#7f7}.erreur .ecran{color:#f66}
.attente .perso{opacity:.6;filter:grayscale(1)}
@keyframes tape{from{transform:translateY(0)}to{transform:translateY(-6px)}}
#msg{text-align:center;margin-top:40px;color:#ccc}
</style>
<h1>🏢 <span id="sujet">Open space</span></h1>
<div id="lanceur">
 <input id="s" placeholder="Sujet de la vidéo">
 <button onclick="go()">🚀 Lancer</button>
</div>
<div id="bureau"></div><p id="msg"></p>
<script>
const persos={script:"🧑‍💻",voix:"🎤",timing:"⏱️",personnage:"🎨",code:"⌨️",montage:"🎬"};
const txt={attente:"zzz…",en_cours:"au travail…",ok:"terminé ✓",erreur:"erreur !"};
async function maj(){
  const d=await (await fetch('/status')).json();
  document.getElementById('sujet').textContent=d.sujet||'Open space';
  document.getElementById('bureau').innerHTML=Object.entries(d.etapes||{})
   .map(([n,e])=>`<div class="poste ${e}"><div class="ecran">${txt[e]}</div>
   <div class="perso">${persos[n]||'🙂'}</div><div class="nom">${n}</div></div>`).join('');
  document.getElementById('msg').textContent=(d.message||'')+' · '+(d.maj||'');
}
async function go(){
  const sujet=document.getElementById('s').value;
  await fetch('/lancer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sujet})});
}
setInterval(maj,1000);maj();
</script></html>"""

@app.route("/")
def index():
    return PAGE

@app.route("/status")
def status():
    if FICHIER.exists():
        return jsonify(json.loads(FICHIER.read_text(encoding="utf-8")))
    return jsonify({"message": "En attente d'une vidéo"})
@app.route("/lancer", methods=["POST"])
def lancer():
    sujet = request.json.get("sujet", "").strip()
    if not sujet:
        return jsonify({"ok": False, "erreur": "Sujet vide"})
    subprocess.Popen([sys.executable, str(ROOT / "src" / "main.py"), sujet], cwd=ROOT)
    return jsonify({"ok": True})
if __name__ == "__main__":
    app.run(port=5000)