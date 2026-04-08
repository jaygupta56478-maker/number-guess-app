"""
Number Guessing Game — Single File App
Run:  python number_guess_app.py
Then open:  http://localhost:5000
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import random, uuid

app = Flask(__name__)
app.secret_key = "guess-game-secret-2025"
CORS(app, supports_credentials=True)

DIFFICULTY = {
    "easy":   {"min": 1, "max": 50},
    "medium": {"min": 1, "max": 100},
    "hard":   {"min": 1, "max": 200},
}

games = {}   # session_id → game state

def sid():
    if "id" not in session:
        session["id"] = str(uuid.uuid4())
    return session["id"]

# ─── API ──────────────────────────────────────────────────────────────────────

@app.route("/api/start", methods=["POST"])
def start():
    diff = request.get_json().get("difficulty", "medium")
    if diff not in DIFFICULTY:
        return jsonify({"error": "Invalid difficulty."}), 400
    cfg = DIFFICULTY[diff]
    games[sid()] = {
        "secret": random.randint(cfg["min"], cfg["max"]),
        "min": cfg["min"], "max": cfg["max"],
        "attempts": 0, "guesses": [], "won": False,
    }
    return jsonify({"min": cfg["min"], "max": cfg["max"]})

@app.route("/api/guess", methods=["POST"])
def guess():
    g = games.get(sid())
    if not g:
        return jsonify({"error": "No active game."}), 400
    if g["won"]:
        return jsonify({"error": "Already won — start a new game."}), 400
    try:
        val = int(request.get_json().get("guess"))
    except (TypeError, ValueError):
        return jsonify({"error": "Send a valid integer."}), 400
    if not (g["min"] <= val <= g["max"]):
        return jsonify({"error": f"Out of range ({g['min']}–{g['max']})."}), 400

    g["attempts"] += 1
    g["guesses"].append(val)
    secret = g["secret"]
    diff   = abs(val - secret)

    if val == secret:
        g["won"] = True
        return jsonify({"result": "correct", "attempts": g["attempts"], "secret": secret})

    direction = "higher" if val < secret else "lower"
    hint = "hot" if diff <= 5 else "warm" if diff <= 15 else "cold"
    return jsonify({"result": "wrong", "hint": hint, "direction": direction, "attempts": g["attempts"]})

# ─── Frontend (served as a single HTML page) ──────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Number Guessing Game</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0c0c0e;--surface:#141416;--border:#252528;
  --text:#f0eeea;--muted:#6e6c78;
  --accent:#e8d5a3;--accent-dk:#0c0c0e;
  --hot:#e8745a;--warm:#e8c45a;--cold:#5ab0e8;--win:#6de87a;
  --r:14px;
}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem 1rem;}
.wrap{width:100%;max-width:460px;}

/* header */
header{text-align:center;margin-bottom:2.5rem;}
header h1{font-size:clamp(2.2rem,7vw,3.2rem);font-weight:800;letter-spacing:-.04em;line-height:1;}
header h1 em{font-style:normal;color:var(--accent);}
header p{margin-top:.5rem;font-family:'DM Mono',monospace;font-size:13px;color:var(--muted);}

/* difficulty */
.diff-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:1.5rem;}
.db{padding:10px 4px;background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);color:var(--muted);font-family:'Syne',sans-serif;
  font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;text-align:center;}
.db:hover{border-color:var(--accent);color:var(--text);}
.db.on{background:var(--accent);border-color:var(--accent);color:var(--accent-dk);}
.db small{display:block;font-weight:400;font-family:'DM Mono',monospace;font-size:11px;margin-top:2px;}

/* stats */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:1.5rem;}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:.9rem .75rem;text-align:center;}
.sl{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px;}
.sv{font-size:26px;font-weight:700;}

/* feedback */
.fb{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);
  padding:1rem 1.25rem;text-align:center;margin-bottom:1rem;transition:border-color .3s;}
.fb.hot{border-color:var(--hot);}
.fb.warm{border-color:var(--warm);}
.fb.cold{border-color:var(--cold);}
.fb.win{border-color:var(--win);}
#fbmsg{font-size:15px;font-weight:600;min-height:22px;transition:color .3s;}
.fb.hot  #fbmsg{color:var(--hot);}
.fb.warm #fbmsg{color:var(--warm);}
.fb.cold #fbmsg{color:var(--cold);}
.fb.win  #fbmsg{color:var(--win);}

/* range */
.rng{margin-bottom:1.25rem;}
.rl{display:flex;justify-content:space-between;font-size:11px;
  font-family:'DM Mono',monospace;color:var(--muted);margin-bottom:5px;}
.rt{height:4px;background:var(--border);border-radius:2px;overflow:hidden;}
.rf{height:100%;background:var(--accent);border-radius:2px;transition:width .5s ease;}

/* error */
#err{font-size:13px;color:var(--hot);font-family:'DM Mono',monospace;
  text-align:center;min-height:18px;margin-bottom:.5rem;}

/* input */
.irow{display:flex;gap:8px;margin-bottom:1.25rem;}
#gi{flex:1;padding:12px 16px;background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);color:var(--text);font-family:'DM Mono',monospace;
  font-size:16px;outline:none;transition:border-color .2s;}
#gi:focus{border-color:var(--accent);}
#gi::placeholder{color:var(--muted);}
#gb{padding:12px 22px;background:var(--accent);border:none;border-radius:var(--r);
  color:var(--accent-dk);font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
  cursor:pointer;transition:opacity .2s,transform .1s;white-space:nowrap;}
#gb:hover{opacity:.85;}#gb:active{transform:scale(.97);}
#gb:disabled{opacity:.35;cursor:not-allowed;}

/* history */
.hw{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  padding:1rem 1.25rem;margin-bottom:1rem;min-height:64px;}
.hl{font-size:11px;color:var(--muted);font-family:'DM Mono',monospace;
  text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;}
.chips{display:flex;flex-wrap:wrap;gap:6px;}
.chip{font-family:'DM Mono',monospace;font-size:12px;padding:4px 12px;border-radius:20px;font-weight:500;}
.cl{background:#152333;color:var(--cold);}
.ch{background:#331a12;color:var(--hot);}
.cw{background:#133318;color:var(--win);}

/* reset */
#rb{width:100%;padding:11px;background:transparent;border:1px solid var(--border);
  border-radius:var(--r);color:var(--muted);font-family:'Syne',sans-serif;
  font-size:13px;font-weight:600;cursor:pointer;letter-spacing:.04em;
  transition:border-color .2s,color .2s;}
#rb:hover{border-color:var(--accent);color:var(--text);}

/* win overlay */
#overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);
  align-items:center;justify-content:center;z-index:99;}
#overlay.show{display:flex;}
.ocard{background:var(--surface);border:1px solid var(--win);border-radius:20px;
  padding:2.5rem 2rem;text-align:center;max-width:320px;width:90%;}
.ocard h2{font-size:2rem;font-weight:800;color:var(--win);margin-bottom:.5rem;}
.ocard p{font-size:14px;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:1.5rem;}
.ocard button{padding:12px 28px;background:var(--accent);border:none;border-radius:10px;
  color:var(--accent-dk);font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
  cursor:pointer;}
.ocard button:hover{opacity:.85;}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Guess the <em>Number</em></h1>
    <p>hot · warm · cold — you'll figure it out</p>
  </header>

  <div class="diff-row">
    <button class="db" onclick="setDiff('easy',this)">Easy<small>1 – 50</small></button>
    <button class="db on" onclick="setDiff('medium',this)">Medium<small>1 – 100</small></button>
    <button class="db" onclick="setDiff('hard',this)">Hard<small>1 – 200</small></button>
  </div>

  <div class="stats">
    <div class="stat"><div class="sl">Attempts</div><div class="sv" id="sa">0</div></div>
    <div class="stat"><div class="sl">Best</div><div class="sv" id="sb">—</div></div>
    <div class="stat"><div class="sl">Wins</div><div class="sv" id="sw">0</div></div>
  </div>

  <div class="fb" id="fb"><div id="fbmsg">Pick a difficulty and start guessing!</div></div>

  <div class="rng">
    <div class="rl"><span id="rlo">1</span><span id="rmid">Range</span><span id="rhi">100</span></div>
    <div class="rt"><div class="rf" id="rf" style="width:100%"></div></div>
  </div>

  <div id="err"></div>

  <div class="irow">
    <input type="number" id="gi" placeholder="Your guess…"/>
    <button id="gb" onclick="doGuess()">Guess</button>
  </div>

  <div class="hw">
    <div class="hl">Guess history</div>
    <div class="chips" id="chips"></div>
  </div>

  <button id="rb" onclick="newGame()">↺ New Game</button>
</div>

<!-- Win overlay -->
<div id="overlay">
  <div class="ocard">
    <h2>You got it!</h2>
    <p id="omsg">Found in — attempts</p>
    <button onclick="closeOverlay()">Play Again</button>
  </div>
</div>

<script>
let diff="medium", minN=1, maxN=100, loN=1, hiN=100;
let wins=0, best=null, active=false;

async function setDiff(d, btn){
  diff=d;
  document.querySelectorAll('.db').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  await newGame();
}

async function newGame(){
  setErr(''); setFb('','Pick a difficulty and start guessing!');
  document.getElementById('chips').innerHTML='';
  document.getElementById('gb').disabled=false;
  document.getElementById('gi').value='';
  document.getElementById('sa').textContent='0';
  try{
    const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({difficulty:diff})});
    const d=await r.json();
    if(!r.ok){setErr(d.error);return;}
    minN=loN=d.min; maxN=hiN=d.max; active=true;
    updateRange();
    setFb('',`Guess a number between ${minN} and ${maxN}!`);
    document.getElementById('gi').focus();
  }catch(e){setErr('Server error — make sure Flask is running.');}
}

async function doGuess(){
  if(!active){await newGame();return;}
  const inp=document.getElementById('gi');
  const val=parseInt(inp.value);
  setErr('');
  if(isNaN(val)){setErr('Enter a number.');return;}
  if(val<minN||val>maxN){setErr(`Must be between ${minN} and ${maxN}.`);return;}
  try{
    const r=await fetch('/api/guess',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({guess:val})});
    const d=await r.json();
    if(!r.ok){setErr(d.error);return;}
    document.getElementById('sa').textContent=d.attempts;
    inp.value='';
    if(d.result==='correct'){
      addChip(val,'w');
      setFb('win','Correct! 🎉');
      wins++; if(best===null||d.attempts<best)best=d.attempts;
      document.getElementById('sw').textContent=wins;
      document.getElementById('sb').textContent=best;
      document.getElementById('gb').disabled=true;
      active=false;
      document.getElementById('omsg').textContent=
        `Found in ${d.attempts} attempt${d.attempts===1?'':'s'}!`;
      setTimeout(()=>document.getElementById('overlay').classList.add('show'),400);
    } else {
      addChip(val, d.direction==='higher'?'l':'h');
      const msgs={
        hot:{higher:'🔥 So close! Go higher.',lower:'🔥 So close! Go lower.'},
        warm:{higher:'🌡 Warm! Go higher.',lower:'🌡 Warm! Go lower.'},
        cold:{higher:'❄️ Too low! Go higher.',lower:'❄️ Too high! Go lower.'},
      };
      setFb(d.hint, msgs[d.hint][d.direction]);
      if(d.direction==='higher') loN=Math.max(loN,val+1);
      else hiN=Math.min(hiN,val-1);
      updateRange();
      inp.focus();
    }
  }catch(e){setErr('Server error.');}
}

function closeOverlay(){
  document.getElementById('overlay').classList.remove('show');
  newGame();
}

function setFb(cls,msg){
  const el=document.getElementById('fb');
  el.className='fb'+(cls?' '+cls:'');
  document.getElementById('fbmsg').textContent=msg;
}
function addChip(v,t){
  const c=document.createElement('span');
  c.className='chip c'+t; c.textContent=v;
  document.getElementById('chips').appendChild(c);
}
function updateRange(){
  document.getElementById('rlo').textContent=loN;
  document.getElementById('rhi').textContent=hiN;
  document.getElementById('rmid').textContent=loN+' – '+hiN;
  const pct=Math.round(((hiN-loN)/Math.max(1,maxN-minN))*100);
  document.getElementById('rf').style.width=Math.max(2,pct)+'%';
}
function setErr(m){document.getElementById('err').textContent=m;}

document.getElementById('gi').addEventListener('keydown',e=>{
  if(e.key==='Enter') doGuess();
});

newGame();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

if __name__ == "__main__":
    print("\n  Number Guessing Game")
    print("  ─────────────────────────────")
    print("  Open → http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
