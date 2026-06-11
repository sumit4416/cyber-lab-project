import requests
import time
import os
import socket
import pygetwindow as gw
import pyautogui
from datetime import datetime, timedelta

# ================= CONFIG =================
SERVER = "https://cyber-lab-project-4.onrender.com"

SERVER_LOG = f"{SERVER}/log"
SERVER_UPLOAD = f"{SERVER}/upload"
SERVER_BLOCK = f"{SERVER}/get_blocked"

SCREENSHOT_FOLDER = "screenshots"
SCREENSHOT_INTERVAL = 30
DELETE_AFTER_DAYS = 7

last_screenshot_time = 0
BLOCKED_SITES = []

# ================= CLIENT ID =================
def get_client_id():
    try:
        with open("id.txt", "r") as f:
            return f.read().strip()
    except:
        return socket.gethostname()

CLIENT_ID = get_client_id()

# ================= SETUP =================
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

# ================= FUNCTIONS =================

def get_active_window():
    try:
        window = gw.getActiveWindow()
        return window.title if window else "No Window"
    except Exception as e:
        print("❌ Window error:", e)
        return "Error"


def take_screenshot():
    global last_screenshot_time

    if time.time() - last_screenshot_time < SCREENSHOT_INTERVAL:
        return None

    filename = f"{CLIENT_ID}_{int(time.time())}.png"
    filepath = os.path.join(SCREENSHOT_FOLDER, filename)

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"📸 Screenshot saved: {filename}")
    except Exception as e:
        print("❌ Screenshot error:", e)
        return None

    # upload
    try:
        with open(filepath, 'rb') as f:
            files = {'file': f}
            res = requests.post(SERVER_UPLOAD, files=files, timeout=10)

            print("📤 Upload:", res.status_code, res.text)

            if res.status_code == 200:
                last_screenshot_time = time.time()
                return filename

    except Exception as e:
        print("❌ Upload error:", e)

    return None


def delete_old_screenshots():
    now = datetime.now()

    for file in os.listdir(SCREENSHOT_FOLDER):
        file_path = os.path.join(SCREENSHOT_FOLDER, file)

        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))

            if now - file_time > timedelta(days=DELETE_AFTER_DAYS):
                os.remove(file_path)
                print(f"🗑 Deleted: {file}")


def send_data(window_title, screenshot_name=None):
    data = {
        "user": CLIENT_ID,
        "window": window_title,
        "time": str(datetime.now()),
        "alert": "",
        "screenshot": screenshot_name or ""
    }

    keywords = ["porn", "game", "pubg", "xxx"]
    if any(k in window_title.lower() for k in keywords):
        data["alert"] = "⚠ Suspicious Activity"

    try:
        r = requests.post(SERVER_LOG, json=data, timeout=10)
        print(f"📡 Log Sent: {r.status_code} | {r.text}")
    except Exception as e:
        print("❌ Log error:", e)


def fetch_blocked_sites():
    global BLOCKED_SITES
    try:
        res = requests.get(SERVER_BLOCK, timeout=10)
        BLOCKED_SITES = res.json()
        print("🚫 Block list:", BLOCKED_SITES)
    except Exception as e:
        print("❌ Block fetch error:", e)


def check_and_block(window_title):
    for site in BLOCKED_SITES:
        if site.lower() in window_title.lower():
            print(f"🚫 Blocking: {site}")

            os.system("taskkill /f /im chrome.exe >nul 2>&1")
            os.system("taskkill /f /im msedge.exe >nul 2>&1")
            os.system("taskkill /f /im firefox.exe >nul 2>&1")


# ================= MAIN LOOP =================

print(f"🚀 Client started: {CLIENT_ID}")

while True:
    try:
        window = get_active_window()

        fetch_blocked_sites()
        check_and_block(window)

        screenshot_name = take_screenshot()
        send_data(window, screenshot_name)

        delete_old_screenshots()

    except Exception as e:
        print("❌ Main loop error:", e)

    time.sleep(5)
