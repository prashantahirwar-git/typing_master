"""
TypeCraft — Single-file Flask typing platform.
No templates/ or static/ folders required.
Run:  python app.py          (local)
      gunicorn app:app        (production / Render)
"""

from flask import Flask, request, jsonify, make_response
import sqlite3, os, random
from datetime import datetime

# ── App & DB ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'typing.db')
app      = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                wpm      REAL    NOT NULL,
                accuracy REAL    NOT NULL,
                duration INTEGER NOT NULL,
                chars    INTEGER NOT NULL,
                errors   INTEGER NOT NULL
            )
        ''')
        conn.commit()

# ── Texts ──────────────────────────────────────────────────────────────────────
TEXTS = {
    "short": [
        "The quick brown fox jumps over the lazy dog near the river bank on a cold winter morning.",
        "Typing fast requires practice, patience, and proper finger placement on the home row keys.",
        "A smooth sea never made a skilled sailor, nor did easy paths forge great minds or strong characters.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts in the end.",
        "The only way to do great work is to love what you do and keep pushing forward every single day.",
        "Every expert was once a beginner. Every professional was once an amateur. Start before you feel ready.",
        "Keyboards are the most intimate interface between human thought and digital action in the modern world.",
        "Speed comes from accuracy, not the other way around. Focus on hitting every key correctly first.",
        "The difference between a slow typist and a fast one is not talent but the number of hours practiced.",
        "Good habits formed at youth make all the difference, and typing is one habit worth forming early on.",
    ],
    "medium": [
        ("Programming is the art of telling another human what one wants the computer to do. It is a craft "
         "that demands clarity of thought, precision of expression, and an unwavering attention to detail. "
         "Every line of code is a decision, a small choice that compounds into something larger over time. "
         "The best programmers are not those who know the most syntax but those who think most clearly "
         "about problems and communicate their solutions in a way that other humans can understand and maintain. "
         "Code is read far more often than it is written, and that fact should inform every decision you make."),
        ("Touch typing is a skill that pays dividends for life. Unlike most computer skills that become "
         "obsolete within a decade, the ability to type quickly and accurately without looking at the "
         "keyboard is universally valuable across every profession and every generation of technology. "
         "Doctors, lawyers, programmers, writers, and executives all benefit from faster typing. "
         "The investment of a few weeks of deliberate practice returns hours saved every single year. "
         "It is one of the few skills where the barrier to entry is low but the compounding reward is enormous."),
        ("The history of the written word spans thousands of years, from cuneiform clay tablets to papyrus "
         "scrolls, from the printing press to the typewriter, and finally to the digital keyboard. "
         "At each stage, the tools changed but the fundamental purpose remained constant: to capture thought "
         "in a form that outlasts the moment of its creation. Today we type faster than scribes could ever "
         "dream of writing, yet the power of a well-chosen word remains unchanged. Speed is a means, "
         "not an end. What matters is the clarity and precision of the ideas you put into the world."),
        ("In the beginning was the command line. Before windows, before mice, before icons, there was a "
         "glowing cursor on a dark screen waiting for your instructions. Those who learned to communicate "
         "with that cursor gained a kind of power that persists to this day. The command line taught "
         "an entire generation that computers were tools to be directed, not oracles to be consulted. "
         "That lesson is still worth learning. Understanding what lies beneath the interface makes you "
         "a more capable, more confident, and ultimately more creative user of every digital tool you touch."),
        ("Muscle memory is a fascinating phenomenon. After enough repetition, complex sequences of physical "
         "actions are offloaded from conscious thought to procedural memory deep in the cerebellum. "
         "A pianist does not think about each finger movement. A driver does not consciously decide when "
         "to brake. A fast typist does not look up each letter. This is the goal of typing practice: "
         "to make the mechanical act of translating thought into keystrokes so effortless that your full "
         "conscious attention can remain on the ideas themselves rather than the physical means of expression."),
    ],
    "long": [
        ("The history of computing is a history of abstraction. Each generation of technology has hidden "
         "the complexity of the previous generation behind a simpler interface. We moved from toggle "
         "switches to assembly language, from assembly to high-level languages, from command lines to "
         "graphical interfaces, and from desktop applications to the cloud. Each step made computers more "
         "accessible but also more opaque. The programmer's art is to understand what lies beneath the "
         "abstraction and to know when the abstraction is leaking. A leaky abstraction is one where the "
         "underlying complexity bleeds through despite the designer's best intentions. Every experienced "
         "developer has encountered this: the database query that ignores the index, the network call "
         "that fails silently, the memory allocation that succeeds until it suddenly does not. "
         "Knowing the layers below your current level of abstraction is not pedantry. It is the difference "
         "between a developer who can only work when things go right and one who can diagnose and fix "
         "problems when they go wrong, which in production is always eventually."),
        ("Consistent practice is the foundation of all expertise. Whether you are learning to play a "
         "musical instrument, speak a foreign language, or type with speed and precision, the brain "
         "learns by repetition. Neural pathways strengthen with each correct repetition and weaken without "
         "reinforcement. This is why ten minutes of focused daily practice outperforms two hours of "
         "occasional effort spread across a month. The brain consolidates skills during sleep, and "
         "returning to practice each day gives it fresh material to work with. Deliberate practice "
         "means practicing at the edge of your current ability, not in the comfortable middle. It means "
         "targeting your weaknesses rather than endlessly repeating your strengths. A typist who always "
         "practices the same easy sentences never improves. Seek out the punctuation, the numbers, the "
         "capital letters, the unusual letter combinations that slow you down. Embrace the discomfort "
         "of making errors in practice so that you make fewer of them when it counts. Build the habit, "
         "trust the process, and the skill will follow as naturally as breathing after enough time."),
        ("Language is the technology that separates human civilization from everything else on this planet. "
         "It allows knowledge to accumulate across generations rather than being rediscovered by each one. "
         "It allows cooperation at scales that no other species can achieve. It allows one mind to model "
         "the internal states of another mind, to predict behavior, to negotiate, to persuade, and to "
         "inspire. Writing is the crystallization of language into a form that persists beyond the moment "
         "of utterance. Typing is the modern means by which we most often produce written language. "
         "The speed and accuracy with which you can translate thought into text is therefore not a trivial "
         "skill but a fundamental bottleneck in how effectively you communicate with the world. "
         "A faster typist is not just more productive in a narrow mechanical sense. They are able to "
         "capture more of their thinking before it evaporates, to correspond more fully, to write more "
         "carefully considered arguments, and to participate more actively in the written conversations "
         "that increasingly define professional and intellectual life in the twenty-first century."),
        ("The relationship between speed and accuracy in typing is often misunderstood. Many beginners "
         "believe they should push for speed first and let accuracy follow. The opposite is true. "
         "Speed is the natural consequence of accuracy practiced enough times that the correct movements "
         "become automatic. When you type incorrectly and then correct yourself, you are not just losing "
         "the time it takes to backspace. You are actively reinforcing a bad habit in your motor memory. "
         "The brain records the error as part of the sequence. Slow down until you can type a passage "
         "with perfect accuracy, then let speed come naturally through repetition. This approach feels "
         "counterintuitive and frustrating at first. Watching your words per minute remain stubbornly low "
         "while others seem to fly ahead is discouraging. But the typist who builds on a foundation of "
         "accuracy will eventually surpass the one who rushed to speed, because they will not carry the "
         "accumulated weight of deeply ingrained error patterns that become harder to unlearn with every "
         "passing month of practice. Patience at the beginning is the fastest path to excellence in the end."),
        ("Every technology that extends human capability also changes the humans who use it. The printing "
         "press did not just make books cheaper. It changed how Europeans thought about knowledge, "
         "authority, and the self. The typewriter did not just speed up writing. It changed prose style, "
         "brought women into the workforce in large numbers, and separated the act of composition from "
         "the physical appearance of the final text for the first time in history. The computer keyboard "
         "is still changing us. It has made writing a more iterative, revisable process. It has blurred "
         "the line between draft and final product. It has made correspondence instantaneous and therefore "
         "both more frequent and less considered. It has created entirely new genres of writing: the "
         "text message, the tweet, the comment thread, the pull request review. Each of these demands "
         "its own register, its own norms, its own rhythm. The typist who moves through all of these "
         "fluently, who can shift from careful technical documentation to warm personal message to "
         "persuasive professional email without friction, has mastered not just a mechanical skill "
         "but a form of communicative intelligence that is increasingly central to modern life."),
    ]
}

LESSONS = [
    {"id": 1, "title": "Home Row Mastery",    "desc": "Master ASDF and JKL keys",        "level": "Beginner",     "icon": "⌨️"},
    {"id": 2, "title": "Top Row Reach",        "desc": "QWERTY and UIOP positions",        "level": "Beginner",     "icon": "🔝"},
    {"id": 3, "title": "Bottom Row Control",   "desc": "ZXCV and NM keys",                 "level": "Intermediate", "icon": "⬇️"},
    {"id": 4, "title": "Numbers & Symbols",    "desc": "Numeric row and punctuation",       "level": "Intermediate", "icon": "🔢"},
    {"id": 5, "title": "Speed Drills",         "desc": "Common English words at pace",      "level": "Advanced",     "icon": "⚡"},
    {"id": 6, "title": "Paragraph Flow",       "desc": "Full sentences with punctuation",   "level": "Advanced",     "icon": "📄"},
]

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    resp = make_response(HTML_PAGE)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route('/api/text')
def get_text():
    length = request.args.get('length', 'medium')
    pool   = TEXTS.get(length, TEXTS['medium'])
    count  = {'short': 4, 'medium': 2, 'long': 3}.get(length, 2)
    chosen = random.sample(pool, min(count, len(pool)))
    return jsonify({'text': '  '.join(chosen)})

@app.route('/api/results', methods=['GET'])
def get_results():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM results ORDER BY date DESC LIMIT 50').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/results', methods=['POST'])
def save_result():
    data = request.get_json()
    if not all(k in data for k in ('wpm','accuracy','duration','chars','errors')):
        return jsonify({"error": "Missing fields"}), 400
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    with get_db() as conn:
        cur = conn.execute(
            'INSERT INTO results (date,wpm,accuracy,duration,chars,errors) VALUES (?,?,?,?,?,?)',
            (now, round(data['wpm'],1), round(data['accuracy'],1),
             data['duration'], data['chars'], data['errors'])
        )
        conn.commit()
    return jsonify({"id": cur.lastrowid, "message": "Saved"})

@app.route('/api/results/<int:rid>', methods=['DELETE'])
def delete_result(rid):
    with get_db() as conn:
        conn.execute('DELETE FROM results WHERE id=?', (rid,))
        conn.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/lessons')
def get_lessons():
    return jsonify(LESSONS)

@app.route('/api/stats')
def get_stats():
    with get_db() as conn:
        rows  = conn.execute('SELECT wpm,accuracy,date FROM results ORDER BY date DESC LIMIT 10').fetchall()
        total = conn.execute('SELECT COUNT(*) as cnt FROM results').fetchone()
        best  = conn.execute('SELECT MAX(wpm) as best FROM results').fetchone()
    data = [dict(r) for r in rows]
    data.reverse()
    return jsonify({"history": data, "total_tests": total['cnt'], "best_wpm": best['best'] or 0})

# ── HTML page (everything inline) ──────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TypeCraft — Professional Typing Platform</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,300&family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;--border:#30363d;
  --amber:#f0a500;--amber-dim:#c47f00;--amber-glow:rgba(240,165,0,.12);
  --green:#39d353;--red:#f85149;
  --text:#e6edf3;--text-muted:#7d8590;--text-dim:#484f58;
  --sidebar-w:260px;--radius:10px;--shadow:0 4px 24px rgba(0,0,0,.4);
  --fh:'Fraunces',serif;--fm:'Space Mono',monospace;--fb:'DM Sans',sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{font-size:16px}
body{font-family:var(--fb);background:var(--bg);color:var(--text);display:flex;min-height:100vh;overflow-x:hidden}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}

/* SIDEBAR */
.sidebar{width:var(--sidebar-w);background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:0;left:0;height:100vh;z-index:100;transition:transform .3s ease}
.sidebar-logo{padding:28px 24px 20px;border-bottom:1px solid var(--border)}
.sidebar-logo h1{font-family:var(--fh);font-weight:700;font-size:1.5rem;color:var(--amber);letter-spacing:-.02em;line-height:1}
.sidebar-logo span{font-family:var(--fm);font-size:.65rem;color:var(--text-muted);letter-spacing:.12em;text-transform:uppercase}
.sidebar-nav{flex:1;padding:16px 12px;overflow-y:auto}
.nav-lbl{font-size:.65rem;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);padding:12px 12px 6px}
.nav-item{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;cursor:pointer;color:var(--text-muted);font-size:.9rem;transition:all .15s;margin-bottom:2px;border:1px solid transparent}
.nav-item:hover{background:var(--bg3);color:var(--text);border-color:var(--border)}
.nav-item.active{background:var(--amber-glow);color:var(--amber);border-color:rgba(240,165,0,.2)}
.nav-icon{width:18px;text-align:center;font-size:1rem;flex-shrink:0}
.sidebar-footer{padding:16px;border-top:1px solid var(--border)}
.sidebar-stats{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.stat-pill{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center}
.stat-pill .val{font-family:var(--fm);font-size:1.1rem;font-weight:700;color:var(--amber);display:block}
.stat-pill .lbl{font-size:.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.08em}

/* MAIN */
.main{margin-left:var(--sidebar-w);flex:1;display:flex;flex-direction:column;min-height:100vh}
.topbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 32px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50}
.topbar-title{font-family:var(--fh);font-size:1.1rem;font-weight:600}
.page-content{padding:32px;flex:1}
.section{display:none}.section.active{display:block}

/* CARDS */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.card-header{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.card-header h2{font-family:var(--fh);font-size:1.15rem;font-weight:600}
.card-body{padding:24px}

/* TEST MODE CARDS */
.test-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px;margin-bottom:28px}
.test-card{background:var(--bg2);border:2px solid var(--border);border-radius:var(--radius);padding:22px;cursor:pointer;transition:all .2s;text-align:center;position:relative;overflow:hidden}
.test-card::before{content:'';position:absolute;inset:0;background:var(--amber-glow);opacity:0;transition:opacity .2s}
.test-card:hover{border-color:var(--amber-dim);transform:translateY(-2px)}
.test-card:hover::before{opacity:1}
.test-card.selected{border-color:var(--amber);box-shadow:0 0 0 4px var(--amber-glow)}
.test-card.selected::before{opacity:1}
.tc-icon{font-size:2rem;margin-bottom:10px}
.tc-title{font-family:var(--fh);font-size:1.05rem;font-weight:600;color:var(--text);margin-bottom:4px}
.tc-sub{font-size:.78rem;color:var(--text-muted)}

/* TYPING ENGINE */
.test-controls{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px;flex-wrap:wrap}
.test-timer{font-family:var(--fm);font-size:2.5rem;font-weight:700;color:var(--amber);letter-spacing:-.02em;min-width:80px}
.test-timer.urgent{color:var(--red);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.live-metrics{display:flex;gap:24px}
.metric-badge{text-align:center}
.m-val{font-family:var(--fm);font-size:1.6rem;font-weight:700;color:var(--text);display:block;line-height:1}
.m-lbl{font-size:.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.1em}
.typing-area-wrapper{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:28px;margin-bottom:20px;position:relative;min-height:140px;cursor:text}
.typing-area-wrapper.focused{border-color:var(--amber-dim)}
.typing-area-wrapper.focused::after{content:'';position:absolute;inset:-1px;border-radius:var(--radius);box-shadow:0 0 0 3px var(--amber-glow);pointer-events:none}
#text-display{font-family:var(--fm);font-size:1.1rem;line-height:1.9;letter-spacing:.03em;word-break:break-word;user-select:none}
.char{position:relative}
.char.correct{color:var(--green)}
.char.incorrect{color:var(--red);background:rgba(248,81,73,.15);border-radius:2px}
.char.current{color:var(--amber);border-bottom:2px solid var(--amber);animation:blink 1s step-end infinite}
@keyframes blink{0%,100%{border-color:var(--amber)}50%{border-color:transparent}}
.char.pending{color:var(--text-dim)}
.typing-hint{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:.85rem;color:var(--text-dim);pointer-events:none;transition:opacity .2s;white-space:nowrap}
#typing-input{position:absolute;opacity:0;pointer-events:none;width:1px;height:1px}
.prog-outer{height:4px;background:var(--bg3);border-radius:2px;margin-bottom:20px;overflow:hidden}
.prog-inner{height:100%;background:linear-gradient(90deg,var(--amber-dim),var(--amber));border-radius:2px;transition:width .1s}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:8px;font-size:.88rem;font-weight:500;font-family:var(--fb);cursor:pointer;border:1px solid transparent;transition:all .15s;white-space:nowrap}
.btn-primary{background:var(--amber);color:#0d1117;border-color:var(--amber)}
.btn-primary:hover{background:#f5b42e}
.btn-secondary{background:transparent;color:var(--text);border-color:var(--border)}
.btn-secondary:hover{background:var(--bg3);border-color:var(--text-muted)}
.btn-ghost{background:transparent;color:var(--text-muted);border-color:transparent}
.btn-ghost:hover{color:var(--text);background:var(--bg3)}
.btn-danger{background:rgba(248,81,73,.1);color:var(--red);border-color:rgba(248,81,73,.3)}
.btn-danger:hover{background:rgba(248,81,73,.2)}
.btn-sm{padding:6px 14px;font-size:.8rem}
kbd{background:var(--bg3);border:1px solid var(--border);padding:1px 6px;border-radius:4px;font-family:var(--fm);font-size:.75rem}

/* MODAL */
.modal-overlay{position:fixed;inset:0;background:rgba(13,17,23,.85);backdrop-filter:blur(6px);z-index:200;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s}
.modal-overlay.open{opacity:1;pointer-events:all}
.result-modal{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:40px;max-width:500px;width:90%;box-shadow:0 24px 64px rgba(0,0,0,.6);transform:translateY(20px) scale(.97);transition:transform .3s;text-align:center}
.modal-overlay.open .result-modal{transform:translateY(0) scale(1)}
.result-modal h2{font-family:var(--fh);font-size:1.8rem;color:var(--amber);margin-bottom:8px}
.result-modal .sub{color:var(--text-muted);font-size:.9rem;margin-bottom:32px}
.rbs{display:flex;justify-content:center;gap:40px;margin-bottom:32px}
.rbs-val{font-family:var(--fm);font-size:3rem;font-weight:700;color:var(--text);line-height:1;display:block}
.rbs-lbl{font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.1em}
.res-sec{display:flex;justify-content:center;gap:24px;margin-bottom:32px;font-size:.85rem;color:var(--text-muted)}

/* HISTORY TABLE */
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
thead th{padding:12px 16px;text-align:left;font-size:.72rem;font-weight:500;text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted);border-bottom:1px solid var(--border)}
tbody td{padding:14px 16px;font-size:.88rem;border-bottom:1px solid var(--border);vertical-align:middle}
tbody tr:hover td{background:var(--bg3)}
tbody tr:last-child td{border-bottom:none}
.wpm-badge{font-family:var(--fm);font-weight:700;font-size:1rem}
.acc-bar-wrap{display:flex;align-items:center;gap:10px}
.acc-outer{flex:1;height:6px;background:var(--bg3);border-radius:3px;overflow:hidden;min-width:80px}
.acc-inner{height:100%;background:linear-gradient(90deg,var(--amber-dim),var(--green));border-radius:3px}
.empty-state{text-align:center;padding:60px 20px;color:var(--text-muted)}
.empty-state .es-icon{font-size:3rem;margin-bottom:12px}

/* CHART */
.chart-container{position:relative;height:280px}

/* LESSONS */
.lessons-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.lesson-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:22px;cursor:pointer;transition:all .2s}
.lesson-card:hover{border-color:var(--amber-dim);transform:translateY(-2px);box-shadow:var(--shadow)}
.lesson-hdr{display:flex;align-items:center;gap:14px;margin-bottom:12px}
.l-icon{font-size:1.8rem}
.l-title{font-family:var(--fh);font-size:1.05rem;font-weight:600}
.l-level{display:inline-block;font-size:.7rem;padding:2px 10px;border-radius:20px;font-weight:500;margin-bottom:8px}
.lv-Beginner{background:rgba(57,211,83,.1);color:var(--green)}
.lv-Intermediate{background:rgba(240,165,0,.1);color:var(--amber)}
.lv-Advanced{background:rgba(248,81,73,.1);color:var(--red)}
.l-desc{font-size:.85rem;color:var(--text-muted)}

/* GAMES */
.games-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.game-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:28px 22px;text-align:center;cursor:pointer;transition:all .2s}
.game-card:hover{border-color:var(--amber-dim);transform:translateY(-2px)}
.gc-icon{font-size:2.4rem;margin-bottom:12px}
.game-card h3{font-family:var(--fh);font-size:1.1rem;margin-bottom:6px}
.game-card p{font-size:.82rem;color:var(--text-muted)}
.coming-soon{font-size:.7rem;background:var(--bg3);color:var(--text-muted);padding:2px 8px;border-radius:4px;margin-top:8px;display:inline-block}
.section-hdr{margin-bottom:24px}
.section-hdr h2{font-family:var(--fh);font-size:1.6rem;margin-bottom:6px}
.section-hdr p{color:var(--text-muted);font-size:.9rem}

/* CERTIFICATE */
@media print{body *{visibility:hidden}#cert-print,#cert-print *{visibility:visible}#cert-print{position:fixed;inset:0;display:flex!important;align-items:center;justify-content:center;background:#fff;z-index:9999}}
#cert-print{display:none}
.certificate{max-width:680px;margin:0 auto;padding:60px;border:8px double #0d1117;font-family:Georgia,serif;text-align:center;background:#fffdf6;color:#1a1a1a}
.certificate h1{font-size:2.5rem;margin-bottom:8px}
.cert-stats{display:flex;justify-content:center;gap:48px;margin:32px 0}
.cs-val{font-size:2.5rem;font-weight:700}
.cs-lbl{font-size:.85rem;text-transform:uppercase;letter-spacing:.1em;color:#555}

/* HAMBURGER */
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:4px}
.hamburger span{display:block;width:22px;height:2px;background:var(--text);border-radius:2px;transition:all .3s}

@media(max-width:900px){
  .sidebar{transform:translateX(-100%)}
  .sidebar.open{transform:translateX(0)}
  .main{margin-left:0}
  .hamburger{display:flex}
  .page-content{padding:20px 16px}
  .topbar{padding:0 16px}
  .rbs{gap:24px}
  .rbs-val{font-size:2.2rem}
}
</style>
</head>
<body>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-logo">
    <h1>TypeCraft</h1>
    <span>Precision Typing Platform</span>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-lbl">Practice</div>
    <div class="nav-item active" data-section="tests"><span class="nav-icon">⌨️</span> Tests</div>
    <div class="nav-item" data-section="lessons"><span class="nav-icon">📖</span> Lessons</div>
    <div class="nav-item" data-section="games"><span class="nav-icon">🎮</span> Games</div>
    <div class="nav-lbl" style="margin-top:8px">Analytics</div>
    <div class="nav-item" data-section="progress"><span class="nav-icon">📈</span> Progress</div>
  </nav>
  <div class="sidebar-footer">
    <div class="sidebar-stats">
      <div class="stat-pill"><span class="val" id="sidebar-tests">—</span><span class="lbl">Tests</span></div>
      <div class="stat-pill"><span class="val" id="sidebar-best">—</span><span class="lbl">Best WPM</span></div>
    </div>
  </div>
</aside>

<div class="main">
  <header class="topbar">
    <div style="display:flex;align-items:center;gap:14px">
      <div class="hamburger" onclick="toggleSidebar()"><span></span><span></span><span></span></div>
      <div class="topbar-title" id="topbar-title">Typing Tests</div>
    </div>
    <button class="btn btn-ghost btn-sm" onclick="loadNewTest()">↻ New Text</button>
  </header>

  <div class="page-content">

    <!-- TESTS -->
    <div id="tests" class="section active">
      <div class="test-grid">
        <div class="test-card selected" data-mode="timed" data-duration="60" onclick="selectMode('timed',60)">
          <div class="tc-icon">⏱️</div><div class="tc-title">1 Minute</div><div class="tc-sub">Quick speed check</div>
        </div>
        <div class="test-card" data-mode="timed" data-duration="180" onclick="selectMode('timed',180)">
          <div class="tc-icon">🕒</div><div class="tc-title">3 Minutes</div><div class="tc-sub">Standard assessment</div>
        </div>
        <div class="test-card" data-mode="timed" data-duration="300" onclick="selectMode('timed',300)">
          <div class="tc-icon">🕔</div><div class="tc-title">5 Minutes</div><div class="tc-sub">Endurance challenge</div>
        </div>
        <div class="test-card" data-mode="page" data-duration="0" onclick="selectMode('page',0)">
          <div class="tc-icon">📄</div><div class="tc-title">Page Test</div><div class="tc-sub">Type full passage</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>Typing Test</h2>
          <span style="font-size:.78rem;color:var(--text-muted)">Press <kbd>Tab</kbd> to restart</span>
        </div>
        <div class="card-body">
          <div class="test-controls">
            <div class="test-timer" id="timer-val">01:00</div>
            <div class="live-metrics">
              <div class="metric-badge"><span class="m-val" id="live-wpm">0</span><span class="m-lbl">WPM</span></div>
              <div class="metric-badge"><span class="m-val" id="live-acc">100</span><span class="m-lbl">Acc %</span></div>
            </div>
          </div>
          <div class="prog-outer"><div class="prog-inner" id="progress-bar" style="width:0%"></div></div>
          <div class="typing-area-wrapper" id="typing-wrapper">
            <div id="text-display"></div>
            <div class="typing-hint" id="test-hint">Click here or start typing…</div>
            <input id="typing-input" type="text" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" tabindex="-1" aria-hidden="true">
          </div>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <button class="btn btn-primary" onclick="focusInput();loadNewTest()">▶ Start / Restart</button>
            <button class="btn btn-secondary" onclick="loadNewTest()">↻ New Text</button>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top:24px">
        <div class="card-header">
          <h2>Recent Results</h2>
          <button class="btn btn-ghost btn-sm" onclick="navigate('progress')">View All →</button>
        </div>
        <div class="card-body" style="padding:0">
          <div class="tbl-wrap">
            <table>
              <thead><tr><th>Date</th><th>WPM</th><th>Accuracy</th><th>Time</th><th>Errors</th><th>Actions</th></tr></thead>
              <tbody id="history-tbody"></tbody>
            </table>
            <div id="history-empty" class="empty-state"><div class="es-icon">⌨️</div><p>No tests yet — complete your first test above!</p></div>
          </div>
        </div>
      </div>
    </div>

    <!-- LESSONS -->
    <div id="lessons" class="section">
      <div class="section-hdr"><h2>Skill-Based Lessons</h2><p>Master your keyboard row by row, key by key.</p></div>
      <div class="lessons-grid" id="lessons-grid"></div>
    </div>

    <!-- GAMES -->
    <div id="games" class="section">
      <div class="section-hdr"><h2>Typing Games</h2><p>Make practice fun with these challenges.</p></div>
      <div class="games-grid">
        <div class="game-card" onclick="navigate('tests')"><div class="gc-icon">⚡</div><h3>Speed Rush</h3><p>Race against the clock. 1-minute all-out sprint.</p></div>
        <div class="game-card"><div class="gc-icon">🎯</div><h3>Accuracy Sniper</h3><p>Zero errors challenge — precision over speed.</p><div class="coming-soon">Coming Soon</div></div>
        <div class="game-card"><div class="gc-icon">🌊</div><h3>Word Flood</h3><p>Words fall from above — type before they hit the bottom.</p><div class="coming-soon">Coming Soon</div></div>
        <div class="game-card"><div class="gc-icon">🔥</div><h3>Streak Master</h3><p>Build consecutive correct keystroke chains.</p><div class="coming-soon">Coming Soon</div></div>
      </div>
    </div>

    <!-- PROGRESS -->
    <div id="progress" class="section">
      <div class="section-hdr"><h2>Your Progress</h2><p>Track your improvement over the last 10 tests.</p></div>
      <div class="card" style="margin-bottom:24px">
        <div class="card-header"><h2>Performance Trend</h2></div>
        <div class="card-body"><div class="chart-container"><canvas id="progress-chart"></canvas></div></div>
      </div>
      <div class="card">
        <div class="card-header"><h2>Full Test History</h2></div>
        <div class="card-body" style="padding:0">
          <div class="tbl-wrap">
            <table>
              <thead><tr><th>Date</th><th>WPM</th><th>Accuracy</th><th>Duration</th><th>Errors</th><th>Actions</th></tr></thead>
              <tbody id="history-tbody-2"></tbody>
            </table>
            <div id="history-empty-2" class="empty-state"><div class="es-icon">📊</div><p>No test history yet.</p></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<!-- RESULT MODAL -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModal()">
  <div class="result-modal" onclick="event.stopPropagation()">
    <h2>Test Complete! 🎉</h2>
    <p class="sub">Here are your results</p>
    <div class="rbs">
      <div><span class="rbs-val" id="res-wpm">—</span><span class="rbs-lbl">WPM</span></div>
      <div><span class="rbs-val" id="res-acc">—</span><span class="rbs-lbl">Accuracy</span></div>
    </div>
    <div class="res-sec">
      <span>⌨️ <strong id="res-chars">—</strong> chars</span>
      <span>❌ <strong id="res-errors">—</strong> errors</span>
      <span>⏱ <strong id="res-time">—</strong></span>
    </div>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <button class="btn btn-primary" onclick="closeModal();loadNewTest();focusInput()">▶ Try Again</button>
      <button class="btn btn-secondary" onclick="closeModal();navigate('progress')">📈 Progress</button>
      <button class="btn btn-ghost" onclick="closeModal()">Close</button>
    </div>
  </div>
</div>

<div id="cert-print"></div>

<script>
'use strict';

const S = {
  section:'tests',
  test:{mode:'timed',duration:60,text:'',chars:[],idx:0,started:false,finished:false,
        startTime:null,timerRef:null,secondsLeft:60,correct:0,keystrokes:0,errors:0},
  history:[],
  chart:null
};

// ── Navigation ──
function navigate(id){
  S.section=id;
  document.querySelectorAll('.section').forEach(s=>s.classList.toggle('active',s.id===id));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.toggle('active',n.dataset.section===id));
  const titles={tests:'Typing Tests',lessons:'Lessons',games:'Games',progress:'Progress'};
  document.getElementById('topbar-title').textContent=titles[id]||'TypeCraft';
  if(id==='progress')renderChart();
  if(id==='progress'||id==='tests')loadHistory();
  if(window.innerWidth<=900)document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open')}

// ── Mode selection ──
function selectMode(mode,dur){
  S.test.mode=mode;S.test.duration=dur;
  document.querySelectorAll('.test-card').forEach(c=>c.classList.remove('selected'));
  document.querySelector(`[data-mode="${mode}"][data-duration="${dur}"]`)?.classList.add('selected');
  loadNewTest();
}

// ── Load test ──
async function loadNewTest(){
  resetTest();
  const len=S.test.duration>=300?'long':S.test.duration>=180?'medium':'short';
  try{
    const r=await fetch(`/api/text?length=${len}`);
    const d=await r.json();
    initText(d.text);
  }catch(e){initText('The quick brown fox jumps over the lazy dog. Practice makes perfect when you type every day.')}
}

function resetTest(){
  const t=S.test;
  clearInterval(t.timerRef);
  Object.assign(t,{started:false,finished:false,startTime:null,timerRef:null,
    idx:0,correct:0,keystrokes:0,errors:0,secondsLeft:t.duration});
  setTimer(t.duration);
  el('live-wpm').textContent='0';el('live-acc').textContent='100';
  el('progress-bar').style.width='0%';
  el('timer-val').classList.remove('urgent');
}

function initText(txt){
  S.test.text=txt;
  S.test.chars=txt.split('').map(c=>({char:c,status:'pending'}));
  renderText();
  showHint(true);
}

function renderText(){
  el('text-display').innerHTML=S.test.chars.map((c,i)=>{
    const cls=i===S.test.idx?'char current':`char ${c.status}`;
    return `<span class="${cls}">${c.char===' '?'&nbsp;':c.char}</span>`;
  }).join('');
}

function el(id){return document.getElementById(id)}

// ── Input ──
function focusInput(){el('typing-input').focus();el('typing-wrapper').classList.add('focused');showHint(false)}
function showHint(v){el('test-hint').style.opacity=v?'1':'0'}

el('typing-wrapper').addEventListener('click',focusInput);
el('typing-input').addEventListener('blur',()=>el('typing-wrapper').classList.remove('focused'));
el('typing-input').addEventListener('keydown',e=>{
  const t=S.test;
  if(t.finished)return;
  if(e.key==='Tab'){e.preventDefault();loadNewTest();return}
  if(e.ctrlKey||e.altKey||e.metaKey)return;
  if(e.key.length!==1&&e.key!=='Backspace')return;
  if(!t.started&&e.key!=='Backspace')startTest();
  if(!t.started)return;
  if(e.key==='Backspace'){
    if(t.idx===0)return;
    t.idx--;t.chars[t.idx].status='pending';
    refreshChar(t.idx,'pending');updateProg();return;
  }
  const ok=e.key===t.chars[t.idx].char;
  t.keystrokes++;
  if(ok){t.correct++;t.chars[t.idx].status='correct';refreshChar(t.idx,'correct')}
  else{t.errors++;t.chars[t.idx].status='incorrect';refreshChar(t.idx,'incorrect')}
  t.idx++;
  updateMetrics();updateProg();
  if(t.mode==='page'&&t.idx>=t.chars.length)finishTest();
});

function refreshChar(idx,status){
  const spans=el('text-display').querySelectorAll('.char');
  if(!spans.length){renderText();return}
  if(spans[idx])spans[idx].className=`char ${status}`;
  spans.forEach(s=>s.classList.remove('current'));
  if(spans[S.test.idx])spans[S.test.idx].classList.add('current');
}

// ── Timer ──
function startTest(){
  S.test.started=true;S.test.startTime=performance.now();
  if(S.test.mode==='timed'){
    S.test.secondsLeft=S.test.duration;
    S.test.timerRef=setInterval(()=>{
      S.test.secondsLeft--;
      setTimer(S.test.secondsLeft);
      if(S.test.secondsLeft<=10)el('timer-val').classList.add('urgent');
      if(S.test.secondsLeft<=0)finishTest();
    },1000);
  }else{
    S.test.timerRef=setInterval(()=>{
      setTimer(Math.floor((performance.now()-S.test.startTime)/1000));
    },1000);
  }
}

function setTimer(v){
  const m=Math.floor(Math.abs(v)/60),s=Math.abs(v)%60;
  el('timer-val').textContent=`${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

// ── Metrics ──
function wpm(){
  if(!S.test.startTime)return 0;
  const mins=(performance.now()-S.test.startTime)/60000;
  return mins<.001?0:Math.round((S.test.correct/5)/mins);
}
function acc(){
  return S.test.keystrokes?Math.round((S.test.correct/S.test.keystrokes)*100):100;
}
function updateMetrics(){el('live-wpm').textContent=wpm();el('live-acc').textContent=acc()}
function updateProg(){el('progress-bar').style.width=Math.round((S.test.idx/S.test.chars.length)*100)+'%'}

// ── Finish ──
async function finishTest(){
  if(S.test.finished)return;
  S.test.finished=true;clearInterval(S.test.timerRef);
  const elapsed=S.test.startTime?Math.round((performance.now()-S.test.startTime)/1000):S.test.duration;
  const w=wpm(),a=acc();
  try{await fetch('/api/results',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({wpm:w,accuracy:a,duration:elapsed,chars:S.test.correct,errors:S.test.errors})})}
  catch(e){}
  showModal(w,a,elapsed);loadSidebarStats();
}

// ── Modal ──
function showModal(w,a,dur){
  el('res-wpm').textContent=w;el('res-acc').textContent=a+'%';
  el('res-chars').textContent=S.test.correct;el('res-errors').textContent=S.test.errors;
  el('res-time').textContent=fmtDur(dur);
  el('modal-overlay').classList.add('open');
}
function closeModal(){el('modal-overlay').classList.remove('open')}
function fmtDur(s){const m=Math.floor(s/60),r=s%60;return m?`${m}m ${r}s`:`${r}s`}

// ── History ──
async function loadHistory(){
  try{const r=await fetch('/api/results');S.history=await r.json();renderHistory()}
  catch(e){}
}
function renderHistory(){
  const rows=S.history.map(r=>`
    <tr>
      <td>${r.date}</td>
      <td class="wpm-badge" style="color:${r.wpm>=80?'var(--amber)':r.wpm>=50?'var(--green)':'var(--text)'}">${r.wpm}</td>
      <td><div class="acc-bar-wrap"><div class="acc-outer"><div class="acc-inner" style="width:${r.accuracy}%"></div></div><span>${r.accuracy}%</span></div></td>
      <td>${fmtDur(r.duration)}</td>
      <td>${r.errors}</td>
      <td style="display:flex;gap:8px">
        <button class="btn btn-secondary btn-sm" onclick="printCert(${r.id})">🏆 Certificate</button>
        <button class="btn btn-danger btn-sm" onclick="deleteResult(${r.id})">✕</button>
      </td>
    </tr>`).join('');

  ['history-tbody','history-tbody-2'].forEach(id=>{
    const tb=el(id);if(tb)tb.innerHTML=rows;
  });
  ['history-empty','history-empty-2'].forEach(id=>{
    const e=el(id);if(e)e.style.display=S.history.length?'none':'block';
  });
}

async function deleteResult(id){
  if(!confirm('Delete this result?'))return;
  try{await fetch(`/api/results/${id}`,{method:'DELETE'});
    S.history=S.history.filter(r=>r.id!==id);renderHistory();renderChart()}catch(e){}
}

function printCert(id){
  const r=S.history.find(h=>h.id===id);if(!r)return;
  el('cert-print').innerHTML=`<div class="certificate">
    <h1>🏆 Certificate of Achievement</h1>
    <p style="font-size:1.2rem;margin-top:16px">This certifies successful completion of a typing assessment</p>
    <div class="cert-stats">
      <div><div class="cs-val">${r.wpm}</div><div class="cs-lbl">WPM</div></div>
      <div><div class="cs-val">${r.accuracy}%</div><div class="cs-lbl">Accuracy</div></div>
    </div>
    <p>Completed on ${r.date}</p>
    <p style="margin-top:24px;font-size:.8rem;color:#888">TypeCraft Typing Platform</p>
  </div>`;
  el('cert-print').style.display='flex';window.print();el('cert-print').style.display='none';
}

// ── Chart ──
async function renderChart(){
  try{const r=await fetch('/api/stats');const d=await r.json();buildChart(d.history);updateSidebarStats(d)}catch(e){}
}
function buildChart(history){
  const canvas=el('progress-chart');if(!canvas)return;
  if(S.chart){S.chart.destroy();S.chart=null}
  if(!history.length){
    canvas.parentElement.innerHTML='<div class="empty-state"><div class="es-icon">📊</div><p>Complete some tests to see your chart.</p></div>';return;
  }
  S.chart=new Chart(canvas,{
    type:'line',
    data:{
      labels:history.map((_,i)=>`Test ${i+1}`),
      datasets:[
        {label:'WPM',data:history.map(r=>r.wpm),borderColor:'#f0a500',backgroundColor:'rgba(240,165,0,.08)',
         borderWidth:2.5,pointBackgroundColor:'#f0a500',pointRadius:5,tension:.4,fill:true,yAxisID:'y'},
        {label:'Accuracy %',data:history.map(r=>r.accuracy),borderColor:'#39d353',backgroundColor:'rgba(57,211,83,.06)',
         borderWidth:2,pointBackgroundColor:'#39d353',pointRadius:4,tension:.4,fill:true,yAxisID:'y1'}
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{labels:{color:'#7d8590',font:{family:"'DM Sans'",size:12},boxWidth:14}},
        tooltip:{backgroundColor:'#1c2128',borderColor:'#30363d',borderWidth:1,
          titleColor:'#e6edf3',bodyColor:'#7d8590',
          titleFont:{family:"'Space Mono'",size:11},bodyFont:{family:"'DM Sans'",size:12}}
      },
      scales:{
        x:{grid:{color:'rgba(48,54,61,.8)'},ticks:{color:'#7d8590',font:{size:11}}},
        y:{position:'left',grid:{color:'rgba(48,54,61,.8)'},ticks:{color:'#f0a500',font:{size:11},callback:v=>v+' wpm'},
           title:{display:true,text:'WPM',color:'#f0a500',font:{size:11}}},
        y1:{position:'right',grid:{drawOnChartArea:false},ticks:{color:'#39d353',font:{size:11},callback:v=>v+'%'},
            title:{display:true,text:'Accuracy',color:'#39d353',font:{size:11}},min:0,max:100}
      }
    }
  });
}

async function loadSidebarStats(){
  try{const r=await fetch('/api/stats');const d=await r.json();updateSidebarStats(d)}catch(e){}
}
function updateSidebarStats(d){
  el('sidebar-tests').textContent=d.total_tests;
  el('sidebar-best').textContent=d.best_wpm?Math.round(d.best_wpm):'—';
}

// ── Lessons ──
async function loadLessons(){
  try{
    const r=await fetch('/api/lessons');const lessons=await r.json();
    el('lessons-grid').innerHTML=lessons.map(l=>`
      <div class="lesson-card" onclick="navigate('tests')">
        <div class="lesson-hdr"><span class="l-icon">${l.icon}</span>
          <div><div class="l-title">${l.title}</div>
          <span class="l-level lv-${l.level}">${l.level}</span></div>
        </div>
        <p class="l-desc">${l.desc}</p>
        <div style="margin-top:14px"><button class="btn btn-secondary btn-sm">Start Lesson →</button></div>
      </div>`).join('');
  }catch(e){}
}

// ── Init ──
document.querySelectorAll('.nav-item').forEach(n=>n.addEventListener('click',()=>navigate(n.dataset.section)));
loadNewTest();loadSidebarStats();loadHistory();loadLessons();
</script>
</body>
</html>"""

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
