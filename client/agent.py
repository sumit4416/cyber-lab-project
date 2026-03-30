import requests
import time
import pygetwindow as gw

SERVER = "http://192.168.1.10:5000/log"

while True:
    try:
        win = gw.getActiveWindow()
        window = win.title if win else "Idle"

        data = {
            "window": window,
            "user": "lab-cp-version"
        }

        res = requests.post(SERVER, json=data, timeout=5)

        print("Sent:", data, "| Status:", res.status_code)

        # normal delay
        time.sleep(5)

    except Exception as e:
        print("⚠ Connection issue, retrying...", e)

        # fast retry if error
        time.sleep(2)