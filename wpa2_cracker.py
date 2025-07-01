import tkinter as tk
from tkinter import filedialog, messagebox
import threading, json, os, hashlib, hmac, itertools, time, re
from datetime import datetime
from tkinter import ttk
import winsound

# ================= SESSION STATE =================
SESSION_FILE = "cracking_session.json"
CRACKED_FILE = "cracked_passwords.txt"
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= SIMULATE cap -> hc22000 =================
def simulate_hc22000_from_cap(cap_path):
    fake_hash = "a1b2c3d4e5f60718293a4c5e6f7a8b9c:112233445566:1234567890ab:0987654321ab:1234567890abcdef1234567890abcdef:4d79535749504649"
    new_file = os.path.splitext(cap_path)[0] + ".hc22000"
    with open(new_file, 'w') as f:
        f.write(fake_hash)
    return new_file

# ================= PMKID CRACKING =================
stop_cracking = False
attempt_count = 0
start_time = None


def match_pattern(pwd, pattern):
    if not pattern:
        return True
    return re.match(pattern, pwd)

def crack_pmkid(pmkid_file, wordlist, threads=4):
    global stop_cracking, attempt_count, start_time
    stop_cracking = False
    attempt_count = 0
    start_time = time.time()

    with open(pmkid_file, 'r') as f:
        pmkid_hash = None
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split(":")
            if len(parts) >= 6:
                ssid = bytes.fromhex(parts[5])
                pmkid = parts[4]
                pmkid_hash = pmkid.lower()
                break
    if not pmkid_hash:
        result_label.config(text="Invalid PMKID hash file")
        return

    total = len(wordlist)

    def try_range(pwlist, tid):
        global stop_cracking, attempt_count
        for i, pwd in enumerate(pwlist):
            if stop_cracking:
                result_label.config(text="Cracking stopped by user")
                return
            if not match_pattern(pwd, pattern_filter.get()):
                continue
            pmk = hashlib.pbkdf2_hmac('sha1', pwd.encode(), ssid, 4096, 32)
            pke = b"PMK Name" + ssid
            mic = hmac.new(pmk, pke, hashlib.sha1).hexdigest()[:32]
            attempt_count += 1
            if mic == pmkid_hash:
                elapsed = time.time() - start_time
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                with open(CRACKED_FILE, "a") as log:
                    log.write(f"SSID: {ssid.decode(errors='ignore')}\nPassword: {pwd}\nTime: {elapsed:.2f}s\n{'-'*40}\n")
                messagebox.showinfo("Found", f"Password: {pwd}\nTime: {elapsed:.2f}s")
                result_label.config(text=f"[Thread-{tid}] Found: {pwd}")
                progress_bar.stop()
                return
            if i % 10 == 0:
                percent = ((i + tid * len(pwlist)) / total) * 100
                progress_bar['value'] = percent
                elapsed = time.time() - start_time
                speed = attempt_count / elapsed if elapsed else 0
                time_left = (total - attempt_count) / speed if speed else 0
                time_label.config(text=f"Attempts: {attempt_count} | Speed: {speed:.2f}/s | ETA: {time_left:.1f}s")

    chunk = len(wordlist) // threads
    for t in range(threads):
        part = wordlist[t*chunk:(t+1)*chunk] if t < threads-1 else wordlist[t*chunk:]
        threading.Thread(target=try_range, args=(part, t)).start()

# ================= GUI =================
window = tk.Tk()
window.title("WPA2 Cracker - PMKID Support")
window.geometry("600x600")
window.configure(bg="#1e1e1e")
pattern_filter = tk.StringVar()

style = ttk.Style()
style.theme_use("default")
style.configure("TButton", background="#333", foreground="#fff")
style.configure("TLabel", background="#1e1e1e", foreground="#eee")
style.configure("TProgressbar", troughcolor="#444", background="#00ff00")

pmkid_path = tk.StringVar()
wordlist_path = tk.StringVar()
charset = tk.StringVar(value="abc123")
min_len = tk.StringVar(value="3")
max_len = tk.StringVar(value="4")
use_generated = tk.BooleanVar()
generated_words = []

# Browse functions
def browse_pmkid():
    path = filedialog.askopenfilename(filetypes=[("CAP or PMKID", "*.cap *.hc22000")])
    if path.endswith(".cap"):
        path = simulate_hc22000_from_cap(path)
    pmkid_path.set(path)

def browse_wordlist():
    path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
    wordlist_path.set(path)

# Generate words
def generate_wordlist():
    generated_words.clear()
    try:
        chars = charset.get()
        min_l = int(min_len.get())
        max_l = int(max_len.get())
        for l in range(min_l, max_l+1):
            for combo in itertools.product(chars, repeat=l):
                generated_words.append(''.join(combo))
        result_label.config(text=f"Generated {len(generated_words)} combos")
    except:
        messagebox.showerror("Error", "Invalid charset or length")

# Start cracking
def start():
    if not pmkid_path.get():
        messagebox.showerror("Missing", "Select PMKID hash file")
        return

    if use_generated.get():
        if not generated_words:
            generate_wordlist()
        wordlist = generated_words
    else:
        if not wordlist_path.get():
            messagebox.showerror("Missing", "Select wordlist")
            return
        with open(wordlist_path.get(), 'r', encoding='utf-8', errors='ignore') as f:
            wordlist = [line.strip() for line in f if line.strip()]

    save_session({
        "pmkid_path": pmkid_path.get(),
        "wordlist_path": wordlist_path.get(),
        "use_generated": use_generated.get(),
        "charset": charset.get(),
        "min_len": min_len.get(),
        "max_len": max_len.get(),
        "pattern": pattern_filter.get()
    })

    progress_bar['value'] = 0
    crack_pmkid(pmkid_path.get(), wordlist, threads=4)

# Stop cracking
def stop():
    global stop_cracking
    stop_cracking = True

# Load previous session
session = load_session()
if session:
    pmkid_path.set(session.get("pmkid_path", ""))
    wordlist_path.set(session.get("wordlist_path", ""))
    use_generated.set(session.get("use_generated", False))
    charset.set(session.get("charset", "abc123"))
    min_len.set(session.get("min_len", "3"))
    max_len.set(session.get("max_len", "4"))
    pattern_filter.set(session.get("pattern", ""))

# UI Layout
tk.Label(window, text="PMKID Hash File (.hc22000 or .cap)").pack(pady=4)
tk.Entry(window, textvariable=pmkid_path, width=60).pack()
tk.Button(window, text="Browse PMKID or .cap", command=browse_pmkid).pack()

tk.Checkbutton(window, text="Use Generated Wordlist", variable=use_generated, bg="#1e1e1e", fg="#eee", selectcolor="#1e1e1e").pack(pady=6)

frame = tk.Frame(window, bg="#1e1e1e")
frame.pack()
tk.Label(frame, text="Charset:").grid(row=0, column=0)
tk.Entry(frame, textvariable=charset, width=10).grid(row=0, column=1)
tk.Label(frame, text="Min:").grid(row=0, column=2)
tk.Entry(frame, textvariable=min_len, width=5).grid(row=0, column=3)
tk.Label(frame, text="Max:").grid(row=0, column=4)
tk.Entry(frame, textvariable=max_len, width=5).grid(row=0, column=5)
tk.Button(frame, text="Generate", command=generate_wordlist).grid(row=0, column=6, padx=6)

pattern_frame = tk.Frame(window, bg="#1e1e1e")
pattern_frame.pack(pady=6)
tk.Label(pattern_frame, text="Regex Pattern Filter (e.g. ^pass.*123$):").pack()
tk.Entry(pattern_frame, textvariable=pattern_filter, width=40).pack()

tk.Label(window, text="OR Choose Wordlist File").pack(pady=6)
tk.Entry(window, textvariable=wordlist_path, width=60).pack()
tk.Button(window, text="Browse Wordlist", command=browse_wordlist).pack()

tk.Button(window, text="Start Cracking", command=start, bg="green", fg="white").pack(pady=6)
tk.Button(window, text="Stop Cracking", command=stop, bg="red", fg="white").pack(pady=6)
progress_bar = ttk.Progressbar(window, orient='horizontal', length=500, mode='determinate')
progress_bar.pack(pady=5)
time_label = tk.Label(window, text="", bg="#1e1e1e", fg="#00ff00")
time_label.pack()
result_label = tk.Label(window, text="", bg="#1e1e1e", fg="#ffffff")
result_label.pack()

window.mainloop()
