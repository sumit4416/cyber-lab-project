from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)

# ---------- FOLDER SETUP ----------
os.makedirs("screenshots", exist_ok=True)

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            window TEXT,
            user TEXT,
            time TEXT,
            alert TEXT
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
    data = request.json

    window = data.get("window", "")
    user = data.get("user", "unknown")
    time_now = str(datetime.datetime.now())

    alert = ""
    blacklist = ["game", "torrent", "hack"]

    if any(word in window.lower() for word in blacklist):
        alert = "⚠ Suspicious Activity"
        print("⚠ Suspicious activity detected:", window)

    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (window, user, time, alert) VALUES (?, ?, ?, ?)",
        (window, user, time_now, alert)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})

# -------- GET LOGS --------
@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("SELECT window, user, time, alert FROM logs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "window": r[0],
            "user": r[1],
            "time": r[2],
            "alert": r[3]
        })

    return jsonify(logs)

# -------- FILE UPLOAD --------
@app.route('/upload', methods=['POST'])
def upload():
    if not request.files:
        return {"error": "No file"}, 400

    file = list(request.files.values())[0]
    filename = secure_filename(file.filename)
    filepath = os.path.join("screenshots", filename)

    file.save(filepath)

    print("Saved:", filepath)

    return {"status": "uploaded", "file": filename}

# -------- SERVE SCREENSHOT --------
@app.route('/screenshots/<filename>')
def get_screenshot(filename):
    return send_from_directory('screenshots', filename)

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

# ---------- MAIN ----------
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))