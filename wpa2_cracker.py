import tkinter as tk
from tkinter import filedialog, messagebox
import threading, json, os, hashlib, hmac, itertools
from datetime import datetime

# ================= SESSION STATE =================
SESSION_FILE = "cracking_session.json"
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= PMKID CRACKING =================
def crack_pmkid(pmkid_file, wordlist, threads=4):
    with open(pmkid_file, 'r') as f:
        pmkid_hash = None
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split(":")
            if len(parts) >= 5:
                ssid = bytes.fromhex(parts[5])
                pmkid = parts[4]
                pmkid_hash = pmkid.lower()
                break
    if not pmkid_hash:
        result_label.config(text="Invalid PMKID hash file")
        return

    def try_range(pwlist, tid):
        for i, pwd in enumerate(pwlist):
            pmk = hashlib.pbkdf2_hmac('sha1', pwd.encode(), ssid, 4096, 32)
            pke = b"PMK Name" + ssid
            mic = hmac.new(pmk, pke, hashlib.sha1).hexdigest()[:32]
            if mic == pmkid_hash:
                messagebox.showinfo("Found", f"Password: {pwd}")
                result_label.config(text=f"[Thread-{tid}] Found: {pwd}")
                return
            if i % 50 == 0:
                result_label.config(text=f"[Thread-{tid}] Tried: {i}")

    chunk = len(wordlist) // threads
    for t in range(threads):
        part = wordlist[t*chunk:(t+1)*chunk] if t < threads-1 else wordlist[t*chunk:]
        threading.Thread(target=try_range, args=(part, t)).start()

# ================= GUI =================
window = tk.Tk()
window.title("WPA2 Cracker - PMKID Support")
window.geometry("600x420")

pmkid_path = tk.StringVar()
wordlist_path = tk.StringVar()
charset = tk.StringVar(value="abc123")
min_len = tk.StringVar(value="3")
max_len = tk.StringVar(value="4")
use_generated = tk.BooleanVar()
generated_words = []

# Browse functions
def browse_pmkid():
    path = filedialog.askopenfilename(filetypes=[("PMKID hash", "*.hc22000")])
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
        "max_len": max_len.get()
    })

    crack_pmkid(pmkid_path.get(), wordlist, threads=4)

# Load previous session
session = load_session()
if session:
    pmkid_path.set(session.get("pmkid_path", ""))
    wordlist_path.set(session.get("wordlist_path", ""))
    use_generated.set(session.get("use_generated", False))
    charset.set(session.get("charset", "abc123"))
    min_len.set(session.get("min_len", "3"))
    max_len.set(session.get("max_len", "4"))

# UI Layout
tk.Label(window, text="PMKID Hash File (.hc22000)").pack(pady=4)
tk.Entry(window, textvariable=pmkid_path, width=60).pack()
tk.Button(window, text="Browse PMKID", command=browse_pmkid).pack()

tk.Checkbutton(window, text="Use Generated Wordlist", variable=use_generated).pack(pady=6)

frame = tk.Frame(window)
frame.pack()
tk.Label(frame, text="Charset:").grid(row=0, column=0)
tk.Entry(frame, textvariable=charset, width=10).grid(row=0, column=1)
tk.Label(frame, text="Min:").grid(row=0, column=2)
tk.Entry(frame, textvariable=min_len, width=5).grid(row=0, column=3)
tk.Label(frame, text="Max:").grid(row=0, column=4)
tk.Entry(frame, textvariable=max_len, width=5).grid(row=0, column=5)
tk.Button(frame, text="Generate", command=generate_wordlist).grid(row=0, column=6, padx=6)

tk.Label(window, text="OR Choose Wordlist File").pack(pady=6)
tk.Entry(window, textvariable=wordlist_path, width=60).pack()
tk.Button(window, text="Browse Wordlist", command=browse_wordlist).pack()

tk.Button(window, text="Start Cracking", command=start, bg="green", fg="white").pack(pady=12)
result_label = tk.Label(window, text="")
result_label.pack()

window.mainloop()
# Save session on close