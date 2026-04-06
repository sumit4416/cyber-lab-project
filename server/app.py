from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)

# ---------- FOLDER SETUP ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs.db")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            window TEXT,
            user TEXT,
            time TEXT,
            alert TEXT,
            screenshot TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- BLOCK STORAGE ----------
blocked_sites = []

# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("index.html")


# -------- LOG API --------
@app.route('/log', methods=['POST'])
def log():
    try:
        data = request.json

        window = data.get("window", "")
        user = data.get("user", "unknown")
        time_now = str(datetime.datetime.now())

        alert = ""
        blacklist = ["game", "torrent", "hack", "porn"]

        if any(word in window.lower() for word in blacklist):
            alert = "⚠ Suspicious Activity"

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs (window, user, time, alert, screenshot) VALUES (?, ?, ?, ?, ?)",
            (window, user, time_now, alert, "")
        )
        conn.commit()
        conn.close()

        return jsonify({"status": "saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------- GET LOGS --------
@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT window, user, time, alert, screenshot FROM logs ORDER BY id DESC LIMIT 500")
    rows = c.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "window": r[0],
            "user": r[1],
            "time": r[2],
            "alert": r[3],
            "screenshot": r[4]
        })

    return jsonify(logs)


# -------- STATS --------
@app.route('/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM logs")
    total_logs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs WHERE alert != ''")
    total_alerts = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT user) FROM logs")
    active_users = c.fetchone()[0]

    conn.close()

    return jsonify({
        "total_logs": total_logs,
        "total_alerts": total_alerts,
        "active_users": active_users
    })


# -------- UPLOAD SCREENSHOT --------
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'screenshot' not in request.files:
            return jsonify({"error": "No file"}), 400

        file = request.files['screenshot']
        filename = secure_filename(file.filename)
        filepath = os.path.join(SCREENSHOTS_DIR, filename)

        file.save(filepath)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE logs SET screenshot=? WHERE id=(SELECT MAX(id) FROM logs)", (filename,))
        conn.commit()
        conn.close()

        return jsonify({"status": "uploaded", "file": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------- SERVE SCREENSHOT --------
@app.route('/screenshots/<filename>')
def get_screenshot(filename):
    return send_from_directory(SCREENSHOTS_DIR, filename)


# -------- BLOCK WEBSITE --------
@app.route("/block", methods=["POST"])
def block_site():
    data = request.json
    site = data.get("site")

    if site and site not in blocked_sites:
        blocked_sites.append(site)

    return jsonify({"status": "blocked", "site": site})


# -------- GET BLOCKED --------
@app.route("/get_blocked", methods=["GET"])
def get_blocked():
    return jsonify(blocked_sites)


# -------- CLEAR DATA (ADMIN) --------
@app.route("/admin/clear", methods=["POST"])
def clear_data():
    key = request.headers.get("X-Admin-Key")

    if key != "admin123":
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

    return jsonify({"status": "cleared"})


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
