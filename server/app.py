from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import datetime

app = Flask(__name__)
CORS(app)

# ---------- FOLDER ----------
os.makedirs("screenshots", exist_ok=True)

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect("logs.db")
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

# ---------- ADMIN KEY ----------
ADMIN_KEY = "1234"   # change this

# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("index.html")

# -------- LOG --------
@app.route('/log', methods=['POST'])
def log():
    data = request.json

    window = data.get("window", "")
    user = data.get("user", "unknown")
    screenshot = data.get("screenshot", "")

    time_now = str(datetime.datetime.now())

    alert = ""
    blacklist = ["game", "torrent", "hack"]

    if any(word in window.lower() for word in blacklist):
        alert = "⚠ Suspicious Activity"

    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs (window, user, time, alert, screenshot) VALUES (?, ?, ?, ?, ?)",
        (window, user, time_now, alert, screenshot)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


# -------- GET LOGS --------
@app.route('/logs', methods=['GET'])
def get_logs():
    limit = request.args.get("limit", 500)

    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute(f"SELECT window, user, time, alert, screenshot FROM logs ORDER BY id DESC LIMIT {limit}")
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
def stats():
    conn = sqlite3.connect("logs.db")
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


# -------- UPLOAD --------
@app.route('/upload', methods=['POST'])
def upload():
    if not request.files:
        return {"error": "No file"}, 400

    file = list(request.files.values())[0]
    filename = secure_filename(file.filename)
    filepath = os.path.join("screenshots", filename)

    file.save(filepath)

    return {"status": "uploaded", "file": filename}


# -------- SCREENSHOT SERVE --------
@app.route('/screenshots/<filename>')
def get_screenshot(filename):
    return send_from_directory('screenshots', filename)


# -------- CLEAR DATA --------
@app.route("/admin/clear", methods=["POST"])
def clear_data():
    key = request.headers.get("X-Admin-Key")

    if key != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect("logs.db")
    c = conn.cursor()
    c.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

    return jsonify({"status": "cleared"})


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
