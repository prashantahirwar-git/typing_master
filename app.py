from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import random
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'typing.db')

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT    NOT NULL,
                wpm       REAL    NOT NULL,
                accuracy  REAL    NOT NULL,
                duration  INTEGER NOT NULL,
                chars     INTEGER NOT NULL,
                errors    INTEGER NOT NULL
            )
        ''')
        conn.commit()

# ── Sample texts ──────────────────────────────────────────────────────────────

TEXTS = {
    "short": [
        "The quick brown fox jumps over the lazy dog near the river bank.",
        "Typing fast requires practice, patience, and proper finger placement.",
        "A smooth sea never made a skilled sailor, nor did easy paths forge great minds.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "The only way to do great work is to love what you do and keep pushing forward.",
    ],
    "medium": [
        "Programming is the art of telling another human what one wants the computer to do. It is a craft that demands clarity of thought, precision of expression, and an unwavering attention to detail. Every line of code is a decision, a small choice that compounds into something larger.",
        "The most important property of a program is whether it accomplishes the intention of its user. Good code is not just functional; it is readable, maintainable, and elegant. Write code that you would be proud to show to another developer six months from now.",
        "Touch typing is a skill that pays dividends for life. Unlike most computer skills that become obsolete, the ability to type quickly and accurately without looking at the keyboard is universally valuable across every profession and decade of technology.",
        "In the beginning was the command line. Before windows, before mice, before icons, there was a glowing cursor on a dark screen, waiting for your instructions. Those who learned to communicate with that cursor gained a kind of power that persists to this day.",
    ],
    "long": [
        "The history of computing is a history of abstraction. Each generation of technology has hidden the complexity of the previous generation behind a simpler interface. We moved from toggle switches to assembly language, from assembly to high-level languages, from command lines to graphical interfaces, and from desktop apps to the cloud. Each step made computers more accessible but also more opaque. The programmer's art is to understand what lies beneath the abstraction and to know when the abstraction is leaking.",
        "Consistent practice is the foundation of all expertise. Whether you are learning to play a musical instrument, speak a foreign language, or type with speed and precision, the brain learns by repetition. Neural pathways strengthen with each correct repetition and weaken without reinforcement. This is why ten minutes of focused daily practice outperforms two hours of occasional effort. Build the habit, trust the process, and the skill will follow as naturally as breathing.",
    ]
}

LESSONS = [
    {"id": 1, "title": "Home Row Mastery",     "desc": "Master ASDF and JKL keys",         "level": "Beginner",      "icon": "⌨️"},
    {"id": 2, "title": "Top Row Reach",         "desc": "QWERTY and UIOP positions",         "level": "Beginner",      "icon": "🔝"},
    {"id": 3, "title": "Bottom Row Control",    "desc": "ZXCV and NM keys",                  "level": "Intermediate",  "icon": "⬇️"},
    {"id": 4, "title": "Numbers & Symbols",     "desc": "Numeric row and punctuation",        "level": "Intermediate",  "icon": "🔢"},
    {"id": 5, "title": "Speed Drills",          "desc": "Common English words at pace",       "level": "Advanced",      "icon": "⚡"},
    {"id": 6, "title": "Paragraph Flow",        "desc": "Full sentences with punctuation",    "level": "Advanced",      "icon": "📄"},
]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/text')
def get_text():
    length = request.args.get('length', 'medium')
    texts  = TEXTS.get(length, TEXTS['medium'])
    return jsonify({"text": random.choice(texts)})

@app.route('/api/results', methods=['GET'])
def get_results():
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM results ORDER BY date DESC LIMIT 50'
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/results', methods=['POST'])
def save_result():
    data = request.get_json()
    required = ('wpm', 'accuracy', 'duration', 'chars', 'errors')
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    with get_db() as conn:
        cur = conn.execute(
            'INSERT INTO results (date, wpm, accuracy, duration, chars, errors) VALUES (?,?,?,?,?,?)',
            (now, round(data['wpm'], 1), round(data['accuracy'], 1),
             data['duration'], data['chars'], data['errors'])
        )
        conn.commit()
        result_id = cur.lastrowid

    return jsonify({"id": result_id, "message": "Saved"})

@app.route('/api/results/<int:result_id>', methods=['DELETE'])
def delete_result(result_id):
    with get_db() as conn:
        conn.execute('DELETE FROM results WHERE id = ?', (result_id,))
        conn.commit()
    return jsonify({"message": "Deleted"})

@app.route('/api/lessons')
def get_lessons():
    return jsonify(LESSONS)

@app.route('/api/stats')
def get_stats():
    with get_db() as conn:
        rows = conn.execute(
            'SELECT wpm, accuracy, date FROM results ORDER BY date DESC LIMIT 10'
        ).fetchall()
        total = conn.execute('SELECT COUNT(*) as cnt FROM results').fetchone()
        best  = conn.execute('SELECT MAX(wpm) as best FROM results').fetchone()
    data = [dict(r) for r in rows]
    data.reverse()
    return jsonify({
        "history":    data,
        "total_tests": total['cnt'],
        "best_wpm":    best['best'] or 0
    })

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
