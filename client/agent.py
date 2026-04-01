import requests
import time
import pygetwindow as gw
import socket

SERVER = "http://192.168.1.10:5000/log"

# ✅ UNIQUE ID
def get_client_id():
    try:
        with open("id.txt", "r") as f:
            return f.read().strip()
    except:
        return socket.gethostname()

CLIENT_ID = get_client_id()

while True:
    try:
        win = gw.getActiveWindow()
        window = win.title if win else "Idle"

        data = {
            "window": window,
            "user": CLIENT_ID   # 🔥 FIX
        }

        res = requests.post(SERVER, json=data, timeout=5)

        print("Sent:", data, "| Status:", res.status_code)

        time.sleep(5)

    except Exception as e:
        print("⚠ Connection issue, retrying...", e)
        time.sleep(2)
